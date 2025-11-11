from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generator, Optional

from .audio_utils import read_wav_mono

LOGGER = logging.getLogger(__name__)

try:
    from vosk import KaldiRecognizer, Model  # type: ignore
except Exception:  # pragma: no cover - optional dependency during tests
    KaldiRecognizer = None  # type: ignore
    Model = None  # type: ignore
    LOGGER.warning("VOSK is not available. Wake word detection will use fallback logic.")


WakeCallback = Callable[[], None]


@dataclass
class WakeDetectionResult:
    detected: bool
    confidence: float
    transcript: str


class WakeWordListener:
    """Continuously listens for the configured wake word."""

    def __init__(
        self,
        model_path: Path,
        wake_word: str = "envy",
        sample_rate: int = 16000,
        sensitivity: float = 0.45,
    ) -> None:
        self.model_path = model_path
        self.wake_word = wake_word.lower()
        self.sample_rate = sample_rate
        self.sensitivity = sensitivity
        self._model = self._load_model(model_path)
        self._stop_event = threading.Event()

    @staticmethod
    def _load_model(model_path: Path):
        if Model is None:
            return None
        if not model_path.exists():
            raise FileNotFoundError(
                f"Wake model path {model_path} not found. Run download_models.sh first."
            )
        LOGGER.debug("Loading Vosk model from %s", model_path)
        return Model(str(model_path))

    def stop(self) -> None:
        self._stop_event.set()

    def reset(self) -> None:
        self._stop_event.clear()

    def listen_stream(
        self,
        frames: Generator[bytes, None, None],
        on_detected: WakeCallback,
    ) -> WakeDetectionResult:
        """Listen to an incoming PCM16 stream."""

        if self._model is None:
            LOGGER.info("Using fallback wake detection (no Vosk).")
            try:
                first_chunk = next(frames)
                detected = self.wake_word.encode("utf-8") in first_chunk.lower()
            except StopIteration:
                detected = False
            if detected:
                on_detected()
            return WakeDetectionResult(detected=detected, confidence=1.0, transcript=self.wake_word)

        grammar = json.dumps([self.wake_word])
        recognizer = KaldiRecognizer(self._model, self.sample_rate, grammar)
        confidence = 0.0
        transcript = ""

        for chunk in frames:
            if self._stop_event.is_set():
                break
            if recognizer.AcceptWaveform(chunk):
                result = json.loads(recognizer.Result())
                transcript = result.get("text", "")
                confidence = self._extract_confidence(result)
                if self._contains_wake(transcript):
                    LOGGER.info("Wake word detected with confidence %.2f", confidence)
                    on_detected()
                    return WakeDetectionResult(True, confidence, transcript)
            else:
                partial = json.loads(recognizer.PartialResult())
                transcript = partial.get("partial", "") or transcript
                if self._contains_wake(transcript):
                    confidence = max(confidence, self.sensitivity)
                    LOGGER.info("Wake word detected (partial) at confidence %.2f", confidence)
                    on_detected()
                    return WakeDetectionResult(True, confidence, transcript)

        final = json.loads(recognizer.FinalResult())
        transcript = final.get("text", transcript)
        confidence = max(confidence, self._extract_confidence(final))
        detected = self._contains_wake(transcript)
        if detected:
            LOGGER.info("Wake word detected in final result (confidence %.2f)", confidence)
            on_detected()
        return WakeDetectionResult(detected, confidence, transcript)

    def detect_in_file(self, audio_path: Path) -> WakeDetectionResult:
        """Convenience helper for tests and scripted runs."""

        _, frames = read_wav_mono(audio_path, self.sample_rate)
        detection = self.listen_stream(frames, on_detected=lambda: None)
        if detection.detected:
            LOGGER.info("Wake word detected in %s", audio_path)
        else:
            LOGGER.warning("Wake word not detected in %s", audio_path)
        return detection

    def _contains_wake(self, transcript: str) -> bool:
        tokens = transcript.lower().replace(",", " ").split()
        return self.wake_word in tokens

    @staticmethod
    def _extract_confidence(result: dict) -> float:
        words = result.get("result", [])
        if not words:
            return 0.0
        return float(words[-1].get("conf", 0.0))
