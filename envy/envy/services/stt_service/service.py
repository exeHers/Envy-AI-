from __future__ import annotations

import io
import json
import logging
import wave
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

logger = logging.getLogger("envy.stt_service")


try:
    import vosk  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    vosk = None


@dataclass
class STTConfig:
    engine: str
    model_path: Optional[str] = None
    sample_rate: int = 16000


class STTService:
    def __init__(self, config: STTConfig):
        self.config = config
        self._model = None
        if self.config.engine == "vosk":
            self._load_vosk()

    def _load_vosk(self) -> None:
        if vosk is None:
            logger.warning("Vosk is not installed; falling back to stub transcription.")
            return
        if not self.config.model_path:
            logger.error("No Vosk model path provided.")
            return
        try:
            self._model = vosk.Model(self.config.model_path)
            logger.info("Loaded Vosk model from %s", self.config.model_path)
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.error("Failed to load Vosk model: %s", exc)
            self._model = None

    def transcribe(self, wav_bytes: bytes) -> Dict[str, object]:
        if self._model:
            try:
                return self._transcribe_with_vosk(wav_bytes)
            except Exception as exc:  # pragma: no cover - runtime guard
                logger.exception("Vosk transcription failed: %s", exc)

        return {
            "engine": "stub",
            "text": "create test.py that prints hello from envy",
            "confidence": 0.42,
            "tokens": [],
        }

    def _transcribe_with_vosk(self, wav_bytes: bytes) -> Dict[str, object]:
        buffer = io.BytesIO(wav_bytes)
        with wave.open(buffer, "rb") as wf:
            if wf.getnchannels() != 1:
                raise ValueError("Audio must be mono for Vosk.")
            if wf.getsampwidth() != 2:
                raise ValueError("Audio must be 16-bit.")
            sample_rate = wf.getframerate()
            recognizer = vosk.KaldiRecognizer(self._model, sample_rate)
            results = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    results.append(json.loads(recognizer.Result()))
            final = json.loads(recognizer.FinalResult())
            text = final.get("text", "")
            return {
                "engine": "vosk",
                "text": text,
                "confidence": final.get("confidence", 0.0),
                "tokens": results + [final],
            }


class TranscriptionResponse(BaseModel):
    engine: str
    text: str
    confidence: float
    tokens: list


def create_app(stt_service: STTService) -> FastAPI:
    app = FastAPI(title="Envy STT Service")

    @app.post("/transcribe", response_model=TranscriptionResponse)
    async def transcribe_audio(file: UploadFile = File(...)):
        try:
            data = await file.read()
            result = stt_service.transcribe(data)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return TranscriptionResponse(**result)

    return app
