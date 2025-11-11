from __future__ import annotations

import asyncio
import logging
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
import math

logger = logging.getLogger("envy.tts_service")


try:
    import pyttsx3  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    pyttsx3 = None


@dataclass
class TTSConfig:
    engine: str = "pyttsx3"
    voice: str = "default"
    rate: int = 185
    artifacts_dir: Path = Path("/workspace/envy/artifacts")


class TTSService:
    def __init__(self, config: TTSConfig):
        self.config = config
        self.config.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._engine = None
        if self.config.engine == "pyttsx3" and pyttsx3:
            try:
                self._engine = pyttsx3.init()
                self._engine.setProperty("rate", self.config.rate)
                logger.info("pyttsx3 initialized for TTS output.")
            except Exception as exc:  # pragma: no cover - runtime guard
                logger.warning("pyttsx3 initialization failed (%s); falling back to stub audio.", exc)
                self._engine = None
        if self._engine is None:
            logger.warning("pyttsx3 unavailable; using synthetic sine-wave fallback.")

    async def synthesize(self, text: str, file_path: Optional[Path] = None) -> Path:
        dest = file_path or self.config.artifacts_dir / "tts-output.wav"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if self._engine:
            await asyncio.to_thread(self._save_with_pyttsx3, text, dest)
        else:
            await asyncio.to_thread(self._generate_stub_wav, text, dest)
        return dest

    def _save_with_pyttsx3(self, text: str, dest: Path) -> None:
        self._engine.save_to_file(text, str(dest))
        self._engine.runAndWait()
        logger.info("Synthesized speech saved to %s", dest)

    def _generate_stub_wav(self, text: str, dest: Path) -> None:
        duration_sec = max(1.0, min(3.0, len(text) / 50.0))
        sample_rate = 16000
        total_frames = int(duration_sec * sample_rate)
        amplitude = 1000
        frequency = 440
        with wave.open(str(dest), "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for i in range(total_frames):
                value = int(amplitude * math.sin(2 * math.pi * frequency * (i / sample_rate)))
                wav_file.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))
            wav_file.writeframes(b"")
        logger.info("Generated stub WAV at %s", dest)


class TTSRequest(BaseModel):
    text: str
    file_hint: Optional[str] = None


class TTSResponse(BaseModel):
    file_path: str


def create_app(service: TTSService) -> FastAPI:
    app = FastAPI(title="Envy TTS Service")

    @app.post("/synthesize", response_model=TTSResponse)
    async def synthesize(request: TTSRequest):
        target = Path(request.file_hint) if request.file_hint else None
        result = await service.synthesize(request.text, target)
        return TTSResponse(file_path=str(result))

    return app
