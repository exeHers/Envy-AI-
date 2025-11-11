"""Wake listener microservice."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from ..config import EnvyConfig, load_config
from ..logging_config import configure_logging

LOGGER = logging.getLogger("envy.wake")


class WakeRequest(BaseModel):
    audio_path: str
    session_id: Optional[str] = None


class WakeDetector:
    """Wraps Vosk keyword spotting with a transcript fallback."""

    def __init__(self, config: EnvyConfig):
        self.config = config
        self.model = self._load_vosk_model()
        self.transcript_cache = self._load_transcripts()
        self.sample_rate = config.wake.sample_rate

    def _load_vosk_model(self):
        try:
            from vosk import Model  # type: ignore

            model_path = Path(self.config.wake.model_path)
            if model_path.exists():
                LOGGER.info("Loading Vosk model from %s", model_path)
                return Model(str(model_path))
            LOGGER.warning("Vosk model path does not exist: %s", model_path)
        except ImportError:
            LOGGER.warning("vosk package not installed, using transcript fallback.")
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Failed to load Vosk model: %s", exc)
        return None

    def _load_transcripts(self) -> Dict[str, Dict[str, str]]:
        transcript_file = self.config.audio_demo_path / "transcripts.json"
        if transcript_file.exists():
            with transcript_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def detect_from_file(self, path: Path) -> Tuple[bool, float, str]:
        if not path.exists():
            raise FileNotFoundError(path)

        if self.model:
            return self._detect_with_vosk(path)

        # Transcript fallback
        key = path.name
        transcript = self.transcript_cache.get(key)
        if transcript and transcript.get("wake_word"):
            LOGGER.debug("Transcript fallback triggered for %s", key)
            return True, 0.6, transcript.get("text", "envy")
        return False, 0.0, ""

    def _detect_with_vosk(self, path: Path) -> Tuple[bool, float, str]:
        from vosk import KaldiRecognizer  # type: ignore
        import wave

        recognizer = KaldiRecognizer(self.model, self.sample_rate)
        recognizer.SetWords(True)
        recognizer.SetGrammar('["envy"]')

        with wave.open(str(path), "rb") as wf:
            while True:
                data = wf.readframes(self.config.wake.chunk_size)
                if not data:
                    break
                recognizer.AcceptWaveform(data)

        final = json.loads(recognizer.Result())
        text = final.get("text", "")
        if "envy" in text.lower():
            confidence = max((w.get("conf", 0.0) for w in final.get("result", [])), default=0.5)
            return True, confidence, text
        return False, 0.0, text


class WakeService:
    def __init__(self, config: EnvyConfig):
        self.config = config
        self.detector = WakeDetector(config)
        self.router_url = config.services["router"].url() + "/wake"

    def notify_router(self, session_id: Optional[str], transcript: str, confidence: float) -> None:
        payload = {
            "session_id": session_id,
            "transcript": transcript,
            "confidence": confidence,
        }
        try:
            response = httpx.post(self.router_url, json=payload, timeout=5)
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Failed to notify router: %s", exc)


def create_app(config: EnvyConfig) -> FastAPI:
    service = WakeService(config)
    app = FastAPI(title="Envy Wake Listener", version="0.1.0")

    @app.on_event("startup")
    async def _startup():
        LOGGER.info("Wake listener service starting with profile '%s'", config.active_profile)

    @app.post("/wake/detect")
    async def detect(request: WakeRequest):
        audio_path = Path(request.audio_path)
        try:
            triggered, confidence, transcript = service.detector.detect_from_file(audio_path)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if triggered:
            LOGGER.info("Wake word detected (confidence %.2f) for %s", confidence, audio_path)
            service.notify_router(request.session_id, transcript, confidence)
        else:
            LOGGER.info("Wake word not detected for %s", audio_path)
        return {
            "wake_detected": triggered,
            "confidence": confidence,
            "transcript": transcript,
        }

    @app.get("/health")
    async def health():
        return {"status": "ok", "wake_model_loaded": bool(service.detector.model)}

    return app


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Envy wake listener service.")
    parser.add_argument("--config", type=str, default=str(CONFIG_PATH := Path(__file__).resolve().parents[2] / "config" / "envy.yaml"))
    parser.add_argument("--host", type=str, help="Override host binding")
    parser.add_argument("--port", type=int, help="Override port binding")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    service_conf = config.services["wake_listener"]

    host = args.host or service_conf.host
    port = args.port or service_conf.port

    configure_logging(config, "wake_listener")
    app = create_app(config)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    main()

