from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .audio_utils import read_wav_mono

LOGGER = logging.getLogger(__name__)

try:
    from vosk import KaldiRecognizer, Model  # type: ignore
except Exception:  # pragma: no cover
    KaldiRecognizer = None  # type: ignore
    Model = None  # type: ignore
    LOGGER.warning("VOSK not available. STT will emit placeholder transcripts.")


@dataclass
class TranscriptWord:
    word: str
    start: float
    end: float
    confidence: float


@dataclass
class TranscriptResult:
    text: str
    words: List[TranscriptWord]

    def command_after(self, wake_word: str) -> str:
        if wake_word.lower() not in self.text.lower():
            return self.text.strip()
        parts = self.text.lower().split(wake_word.lower(), 1)
        command = parts[1] if len(parts) > 1 else ""
        return command.strip(" ,")


class SpeechToTextService:
    def __init__(self, model_path: Path, sample_rate: int = 16000) -> None:
        self.model_path = model_path
        self.sample_rate = sample_rate
        self._model = self._load_model(model_path)

    @staticmethod
    def _load_model(model_path: Path):
        if Model is None:
            return None
        if not model_path.exists():
            raise FileNotFoundError(
                f"STT model path {model_path} not found. Run download_models.sh first."
            )
        LOGGER.debug("Loading Vosk STT model from %s", model_path)
        return Model(str(model_path))

    def transcribe_file(self, audio_path: Path) -> TranscriptResult:
        LOGGER.info("Transcribing audio %s", audio_path)

        if self._model is None:
            LOGGER.warning("Using fallback transcript for %s (no STT model).", audio_path)
            text = audio_path.stem.replace("_", " ")
            return TranscriptResult(text=text, words=[])

        recognizer = KaldiRecognizer(self._model, self.sample_rate)
        recognizer.SetWords(True)

        _, frames = read_wav_mono(audio_path, self.sample_rate)
        for chunk in frames:
            recognizer.AcceptWaveform(chunk)

        result = json.loads(recognizer.FinalResult())
        text = result.get("text", "").strip()
        words = [
            TranscriptWord(
                word=word_info.get("word", ""),
                start=float(word_info.get("start", 0.0)),
                end=float(word_info.get("end", 0.0)),
                confidence=float(word_info.get("conf", 0.0)),
            )
            for word_info in result.get("result", [])
        ]
        LOGGER.info("Transcription complete: '%s'", text)
        return TranscriptResult(text=text, words=words)
