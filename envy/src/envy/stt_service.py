"""
Speech-to-text service built around VOSK with simulation fallback.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import AsyncIterator, Iterable, List, Optional

try:
    from vosk import KaldiRecognizer, Model  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    KaldiRecognizer = None  # type: ignore
    Model = None  # type: ignore

from .config import EnvyConfig

_LOGGER = logging.getLogger(__name__)


class STTService:
    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self._model: Optional[Model] = None
        self._recognizer: Optional[KaldiRecognizer] = None
        self._load_model()

    def _load_model(self) -> None:
        if Model is None:  # pragma: no cover - optional dependency
            _LOGGER.warning("VOSK not available; STT will run in simulation mode.")
            return
        model_path = Path(self.config.audio.stt_model_path)
        if not model_path.exists():
            _LOGGER.warning("STT model path %s does not exist; using simulation mode.", model_path)
            return
        try:
            self._model = Model(str(model_path))
            self._recognizer = KaldiRecognizer(self._model, self.config.audio.sample_rate)
            _LOGGER.info("Loaded STT model from %s", model_path)
        except Exception as exc:  # pragma: no cover - defensive
            _LOGGER.error("Failed to initialise STT model: %s", exc)
            self._model = None
            self._recognizer = None

    async def transcribe_frames(self, frames: AsyncIterator[bytes]) -> str:
        """Stream transcription from async iterator of audio frames."""
        if self._recognizer is None:
            _LOGGER.info("STT simulation: returning placeholder transcription.")
            return "envy placeholder transcription"

        text_fragments: List[str] = []
        async for frame in frames:
            if self._recognizer.AcceptWaveform(frame):  # pragma: no cover - relies on vosk
                result = json.loads(self._recognizer.Result())
                if "text" in result:
                    text_fragments.append(result["text"])
        final_res = json.loads(self._recognizer.FinalResult())
        if "text" in final_res:
            text_fragments.append(final_res["text"])
        transcript = " ".join(fragment for fragment in text_fragments if fragment)
        _LOGGER.debug("STT produced transcript: %s", transcript)
        return transcript.strip()

    async def transcribe_file(self, path: Path) -> str:
        """
        Convenience helper for automated tests: transcribe the entire audio file.
        """
        if self._recognizer is None:
            payload = path.read_text(encoding="utf-8", errors="ignore")
            _LOGGER.info("STT simulation reading text payload from %s", path)
            return payload.strip()

        import wave  # pragma: no cover - depends on actual audio

        with wave.open(str(path), "rb") as wf:
            if wf.getframerate() != self.config.audio.sample_rate or wf.getnchannels() != 1:
                _LOGGER.warning(
                    "Unexpected audio format for %s: %s Hz, %s channels",
                    path,
                    wf.getframerate(),
                    wf.getnchannels(),
                )

            def frame_iter() -> Iterable[bytes]:
                chunk = wf.readframes(self.config.audio.chunk_size)
                while chunk:
                    yield chunk
                    chunk = wf.readframes(self.config.audio.chunk_size)

            return await self.transcribe_frames(_async_from_iterable(frame_iter()))

    async def transcribe_text(self, text: str) -> str:
        """Simulation helper used in tests."""
        _LOGGER.debug("STT simulation using direct text input.")
        await asyncio.sleep(0.01)
        return text


async def _async_from_iterable(iterable: Iterable[bytes]) -> AsyncIterator[bytes]:
    for item in iterable:
        yield item
        await asyncio.sleep(0)  # yield control for cooperative scheduling
