"""Speech-to-text microservice."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from ..config import EnvyConfig, load_config
from ..logging_config import configure_logging

LOGGER = logging.getLogger("envy.stt")


class TranscriptionRequest(BaseModel):
    audio_path: str
    session_id: Optional[str] = None
    stream: bool = False


class TranscriptionResponse(BaseModel):
    text: str
    partials: List[str]
    source: str


class STTEngine:
    def __init__(self, config: EnvyConfig):
        self.config = config
        self.model = self._load_vosk_model()
        self.transcript_cache = self._load_transcripts()
        self.sample_rate = config.wake.sample_rate

    def _load_vosk_model(self):
        try:
            from vosk import Model  # type: ignore

            profile = self.config.profile()
            model_key = profile.stt_model
            model_map = {
                "vosk-small": self.config.wake.model_path,
                "vosk-large": "artifacts/models/vosk-model-en-us-0.22",
            }
            model_path = Path(model_map.get(model_key, self.config.wake.model_path))
            if model_path.exists():
                LOGGER.info("Loading STT model from %s", model_path)
                return Model(str(model_path))
            LOGGER.warning("STT model path does not exist: %s", model_path)
        except ImportError:
            LOGGER.warning("vosk package not installed; STT will use transcript fallback.")
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Failed to load STT model: %s", exc)
        return None

    def _load_transcripts(self) -> Dict[str, Dict[str, str]]:
        transcript_file = self.config.audio_demo_path / "transcripts.json"
        if transcript_file.exists():
            with transcript_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def transcribe_file(self, path: Path, stream: bool = False) -> TranscriptionResponse:
        if not path.exists():
            raise FileNotFoundError(path)

        if self.model:
            text, partials = self._transcribe_with_vosk(path, stream=stream)
            return TranscriptionResponse(text=text, partials=partials, source="vosk")

        key = path.name
        transcript = self.transcript_cache.get(key)
        if transcript:
            LOGGER.debug("Transcript fallback for %s", key)
            return TranscriptionResponse(
                text=transcript.get("text", ""),
                partials=[transcript.get("text", "")],
                source="transcript-cache",
            )
        return TranscriptionResponse(text="", partials=[], source="unknown")

    def _transcribe_with_vosk(self, path: Path, stream: bool = False):
        from vosk import KaldiRecognizer  # type: ignore
        import wave

        recognizer = KaldiRecognizer(self.model, self.sample_rate)
        recognizer.SetWords(True)

        partials: List[str] = []
        with wave.open(str(path), "rb") as wf:
            while True:
                data = wf.readframes(self.config.wake.chunk_size)
                if not data:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    partials.append(result.get("text", ""))
                elif stream:
                    partial = json.loads(recognizer.PartialResult())
                    if partial.get("partial"):
                        partials.append(partial["partial"])

        final = json.loads(recognizer.FinalResult())
        text = final.get("text", "")
        if text and (not partials or partials[-1] != text):
            partials.append(text)
        return text, partials


def create_app(config: EnvyConfig) -> FastAPI:
    engine = STTEngine(config)
    app = FastAPI(title="Envy STT Service", version="0.1.0")

    @app.post("/stt/transcribe", response_model=TranscriptionResponse)
    async def transcribe(request: TranscriptionRequest):
        audio_path = Path(request.audio_path)
        try:
            response = engine.transcribe_file(audio_path, stream=request.stream)
            LOGGER.info("Transcription complete for %s via %s", audio_path, response.source)
            return response
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/health")
    async def health():
        return {"status": "ok", "stt_model_loaded": bool(engine.model)}

    return app


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Envy STT service.")
    parser.add_argument("--config", type=str, default=str(CONFIG_PATH := Path(__file__).resolve().parents[2] / "config" / "envy.yaml"))
    parser.add_argument("--host", type=str, help="Override host binding")
    parser.add_argument("--port", type=int, help="Override port binding")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    service_conf = config.services["stt"]

    host = args.host or service_conf.host
    port = args.port or service_conf.port

    configure_logging(config, "stt_service")
    app = create_app(config)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    main()

