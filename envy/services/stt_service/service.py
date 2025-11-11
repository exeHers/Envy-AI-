from __future__ import annotations

import json
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generator, Iterable, Optional

import vosk

from ..config import load_config, resolve_profile
from ..logger import get_logger


logger = get_logger("stt_service")


@dataclass
class TranscriptChunk:
    text: str
    confidence: float
    final: bool


class SttService:
    def __init__(self, config_path: Optional[Path] = None, profile: Optional[str] = None):
        self.config = load_config(config_path)
        self.profile = resolve_profile(self.config, profile)
        self.model_path = self.profile["stt"]["model"]
        self._recognizer = None
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            model_path = Path(self.model_path)
            if not model_path.exists():
                raise FileNotFoundError(
                    f"Vosk model not found at {model_path}. Run scripts/download_models.sh first."
                )
            logger.info("Loading STT model from %s", model_path)
            self._model = vosk.Model(str(model_path))
            self._recognizer = vosk.KaldiRecognizer(self._model, 16000)

    def transcribe_stream(self, stream: Iterable[bytes]) -> Generator[TranscriptChunk, None, Dict]:
        self._ensure_model()
        transcript = []
        confidence_scores = []
        for chunk in stream:
            if self._recognizer.AcceptWaveform(chunk):
                result = json.loads(self._recognizer.Result())
                text = result.get("text", "")
                if text:
                    chunk_conf = result.get("confidence", 0.0)
                    transcript.append(text)
                    confidence_scores.append(chunk_conf)
                    logger.info("STT final chunk: %s (%.2f)", text, chunk_conf)
                    yield TranscriptChunk(text=text, confidence=chunk_conf, final=True)
            else:
                partial = json.loads(self._recognizer.PartialResult())
                text = partial.get("partial", "")
                if text:
                    logger.debug("STT partial chunk: %s", text)
                    yield TranscriptChunk(text=text, confidence=0.0, final=False)
        final = json.loads(self._recognizer.FinalResult())
        text = final.get("text", "")
        if text:
            chunk_conf = final.get("confidence", 0.0)
            transcript.append(text)
            confidence_scores.append(chunk_conf)
            yield TranscriptChunk(text=text, confidence=chunk_conf, final=True)
        joined = " ".join(transcript).strip()
        mean_conf = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        logger.info("STT final transcript: %s (%.2f)", joined, mean_conf)
        return {"text": joined, "confidence": mean_conf}

    def transcribe_wav(self, wav_path: str | Path) -> Dict:
        wav_path = Path(wav_path)
        if not wav_path.exists():
            raise FileNotFoundError(wav_path)
        with wave.open(str(wav_path), "rb") as wf:
            if wf.getframerate() != 16000 or wf.getnchannels() != 1:
                raise ValueError("STT audio must be mono 16kHz.")
            stream = iter(lambda: wf.readframes(4000), b"")
            final_data = None
            for chunk in self.transcribe_stream(stream):
                final_data = chunk
            final_dict = {
                "text": final_data.text if final_data else "",
                "confidence": final_data.confidence if final_data else 0.0,
            }
            return final_dict
