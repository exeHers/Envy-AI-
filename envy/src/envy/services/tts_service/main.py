from __future__ import annotations

from typing import Optional

import typer
import uvicorn
from fastapi import Depends, FastAPI
from pydantic import BaseModel

from ..common.deps import get_config, verify_secret
from ..common.logging import get_logger
from .tts_engine import TTSEngine


class SynthesizeRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    play: bool = False


class SynthesizeResponse(BaseModel):
    path: str
    engine: str


def create_app() -> FastAPI:
    config = get_config()
    logger = get_logger("TTSService", config=config)
    engine = TTSEngine(config)

    app = FastAPI(title="Envy TTS Service", version="0.1.0")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "engine": engine.engine_name}

    @app.post("/synthesize", response_model=SynthesizeResponse, dependencies=[Depends(verify_secret)])
    async def synthesize(request: SynthesizeRequest) -> SynthesizeResponse:
        result = engine.synthesize(request.text, request.session_id, play=request.play)
        logger.info(f"Synthesised TTS for session {request.session_id}: {result}")
        return SynthesizeResponse(path=result["path"], engine=result["engine"])

    return app


app = create_app()


def main(
    host: str = typer.Option("0.0.0.0", help="Host for the TTS service."),
    port: int = typer.Option(8205, help="Port for the TTS service."),
    reload: bool = typer.Option(False, help="Enable autoreload (development only)."),
) -> None:
    uvicorn.run("envy.services.tts_service.main:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    typer.run(main)
