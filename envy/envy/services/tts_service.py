"""Text-to-speech microservice."""

from __future__ import annotations

import argparse
import datetime as dt
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from ..config import EnvyConfig, load_config
from ..logging_config import configure_logging
from ..utils.audio_utils import save_wave

LOGGER = logging.getLogger("envy.tts")


class SpeakRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    voice: Optional[str] = None


class SpeakResponse(BaseModel):
    status: str
    audio_path: Optional[str] = None
    engine: str


class TTSRenderer:
    def __init__(self, config: EnvyConfig):
        self.config = config
        self.engine = self._init_engine()

    def _init_engine(self):
        try:
            import pyttsx3  # type: ignore

            engine = pyttsx3.init()
            profile_voice = self.config.profile().tts_voice
            if profile_voice and profile_voice != "default":
                for voice in engine.getProperty("voices"):
                    if profile_voice.lower() in voice.name.lower():
                        engine.setProperty("voice", voice.id)
                        break
            engine.setProperty("rate", 180)
            LOGGER.info("Initialized pyttsx3 engine.")
            return engine
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Failed to initialize pyttsx3: %s", exc)
            return None

    def synthesize(self, text: str, session_id: Optional[str]) -> SpeakResponse:
        timestamp = dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        safe_session = session_id or "session"
        audio_dir = self.config.artifacts_path / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = audio_dir / f"{safe_session}-{timestamp}.wav"

        if not text:
            return SpeakResponse(status="empty_text", engine="none")

        if self.engine:
            self.engine.save_to_file(text, str(audio_path))
            self.engine.runAndWait()
            LOGGER.info("Generated TTS audio at %s", audio_path)
            return SpeakResponse(status="ok", audio_path=str(audio_path), engine="pyttsx3")

        # Fallback: write silence but log text
        silence = b"\x00\x00" * 16000
        save_wave(audio_path, silence)
        LOGGER.warning("Using silent fallback TTS output at %s", audio_path)
        return SpeakResponse(status="fallback", audio_path=str(audio_path), engine="silent")


def create_app(config: EnvyConfig) -> FastAPI:
    renderer = TTSRenderer(config)
    app = FastAPI(title="Envy TTS Service", version="0.1.0")

    @app.post("/tts/speak", response_model=SpeakResponse)
    async def speak(request: SpeakRequest):
        if not request.text:
            raise HTTPException(status_code=400, detail="Text must not be empty.")
        response = renderer.synthesize(request.text, request.session_id)
        return response

    @app.get("/health")
    async def health():
        return {"status": "ok", "engine": "pyttsx3" if renderer.engine else "fallback"}

    return app


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Envy TTS service.")
    parser.add_argument("--config", type=str, default=str(CONFIG_PATH := Path(__file__).resolve().parents[2] / "config" / "envy.yaml"))
    parser.add_argument("--host", type=str, help="Override host binding")
    parser.add_argument("--port", type=int, help="Override port binding")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    service_conf = config.services["tts"]
    host = args.host or service_conf.host
    port = args.port or service_conf.port

    configure_logging(config, "tts_service")
    app = create_app(config)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    main()

