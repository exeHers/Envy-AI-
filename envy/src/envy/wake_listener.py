"""
Wake word detection service using VOSK with a simulation fallback.
"""

from __future__ import annotations

import asyncio
import json
import logging
import queue
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable, Optional

try:
    from vosk import KaldiRecognizer, Model  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    KaldiRecognizer = None  # type: ignore
    Model = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import sounddevice as sd
except (ImportError, OSError):  # pragma: no cover - optional dependency
    sd = None  # type: ignore

from .config import EnvyConfig

_LOGGER = logging.getLogger(__name__)


class WakeDetectionError(RuntimeError):
    """Raised when the wake listener cannot be initialised."""


@dataclass
class WakeEvent:
    transcript: str
    confidence: float
    source: str


class SimpleWakeWordEngine:
    """
    Lightweight fallback detector used for automated tests and environments
    where VOSK is unavailable.
    """

    def __init__(self, wake_word: str):
        self.wake_word = wake_word.lower()

    def detect_in_text(self, text: str) -> Optional[WakeEvent]:
        if self.wake_word in text.lower():
            return WakeEvent(
                transcript=text,
                confidence=0.9,
                source="simple-text",
            )
        return None

    def detect_in_bytes(self, payload: bytes, source: str) -> Optional[WakeEvent]:
        try:
            decoded = payload.decode("utf-8", errors="ignore").lower()
        except Exception:  # pragma: no cover - defensive
            decoded = ""
        if self.wake_word in decoded:
            return WakeEvent(
                transcript=self.wake_word,
                confidence=0.5,
                source=source,
            )
        return None


class WakeListener:
    """
    Streaming wake word listener. Emits events through an async callback
    whenever the keyword is recognised.
    """

    def __init__(
        self,
        config: EnvyConfig,
        on_detect: Callable[[WakeEvent], Awaitable[None]],
        queue_size: int = 8,
    ) -> None:
        self.config = config
        self.on_detect = on_detect
        self._audio_queue: "queue.Queue[bytes]" = queue.Queue(maxsize=queue_size)
        self._running = False
        self._vosk_model: Optional[Model] = None
        self._recognizer: Optional[KaldiRecognizer] = None
        self._fallback = SimpleWakeWordEngine(config.wake_word)

        if Model is not None:
            model_path = Path(config.audio.wake_model_path)
            if model_path.exists():
                try:
                    self._vosk_model = Model(str(model_path))
                    self._recognizer = KaldiRecognizer(self._vosk_model, config.audio.sample_rate)
                    _LOGGER.info("Loaded VOSK wake model from %s", model_path)
                except Exception as exc:  # pragma: no cover - defensive
                    _LOGGER.warning("Failed to load VOSK wake model: %s", exc)
            else:
                _LOGGER.warning(
                    "VOSK model path %s does not exist. Falling back to simple detection.", model_path
                )
        else:
            _LOGGER.warning("VOSK not installed. Wake detection will run in simulation mode.")

    async def run(self) -> None:
        if sd is None or self._recognizer is None:
            _LOGGER.info("Wake listener running in simulation mode (no audio input).")
            return

        if self._running:
            raise WakeDetectionError("WakeListener already running")

        loop = asyncio.get_running_loop()
        self._running = True

        def audio_callback(indata, frames, time, status):  # pragma: no cover - relies on sounddevice
            if status:
                _LOGGER.debug("Audio status: %s", status)
            try:
                self._audio_queue.put_nowait(bytes(indata))
            except queue.Full:
                _LOGGER.warning("Wake audio queue full; dropping frame.")

        with sd.RawInputStream(
            samplerate=self.config.audio.sample_rate,
            blocksize=self.config.audio.chunk_size,
            dtype="int16",
            channels=1,
            callback=audio_callback,
            device=self.config.audio.device,
        ):
            _LOGGER.info("Wake listener started using device %s", self.config.audio.device or "default")
            while self._running:
                data = await loop.run_in_executor(None, self._audio_queue.get)
                await self._process_frame(data)

    async def stop(self) -> None:
        self._running = False

    async def _process_frame(self, frame: bytes) -> None:
        if self._recognizer is None:
            fallback_event = self._fallback.detect_in_bytes(frame, "simulated-audio-frame")
            if fallback_event:
                _LOGGER.info("Wake word detected via fallback.")
                await self.on_detect(fallback_event)
            return

        if self._recognizer.AcceptWaveform(frame):  # pragma: no cover - requires vosk
            result = json.loads(self._recognizer.Result())
            word = result.get("text", "").strip().lower()
            if self.config.wake_word in word:
                event = WakeEvent(
                    transcript=result.get("text", ""),
                    confidence=float(result.get("confidence", 0.7)),
                    source="vosk-stream",
                )
                _LOGGER.info("Wake word detected (vosk stream).")
                await self.on_detect(event)

    async def simulate_from_text(self, utterance: str) -> Optional[WakeEvent]:
        event = self._fallback.detect_in_text(utterance)
        if event:
            _LOGGER.info("Wake word detected via simulation from text.")
            await self.on_detect(event)
        return event

    async def detect_from_audio_file(self, path: Path) -> Optional[WakeEvent]:
        """
        Evaluate a file for the wake word. Used by automated tests.
        """
        if not path.exists():
            raise FileNotFoundError(path)

        if self._recognizer is None:
            payload = path.read_bytes()
            event = self._fallback.detect_in_bytes(payload, source=str(path))
            if event:
                _LOGGER.info("Wake word detected via fallback file detection for %s", path.name)
                await self.on_detect(event)
            return event

        import wave  # pragma: no cover - executed in tests

        try:
            with wave.open(str(path), "rb") as wf:
                if wf.getframerate() != self.config.audio.sample_rate or wf.getnchannels() != 1:
                    _LOGGER.warning(
                        "Unexpected audio format for %s: %s Hz, %s channels",
                        path,
                        wf.getframerate(),
                        wf.getnchannels(),
                    )
                data = wf.readframes(self.config.audio.chunk_size)
                while data:
                    if self._recognizer.AcceptWaveform(data):
                        result = json.loads(self._recognizer.Result())
                        if self.config.wake_word in result.get("text", "").lower():
                            event = WakeEvent(
                                transcript=result.get("text", ""),
                                confidence=float(result.get("confidence", 0.6)),
                                source=str(path),
                            )
                            _LOGGER.info("Wake word detected in file %s", path.name)
                            await self.on_detect(event)
                            return event
                    data = wf.readframes(self.config.audio.chunk_size)
        except wave.Error:
            payload = path.read_bytes()
            event = self._fallback.detect_in_bytes(payload, source=str(path))
            if event:
                _LOGGER.info("Wake word detected via fallback text payload for %s", path.name)
                await self.on_detect(event)
            return event
        return None
