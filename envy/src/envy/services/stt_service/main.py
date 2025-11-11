from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Optional

import typer
import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from ..common.deps import get_config, verify_secret
from ..common.logging import get_logger
from .stt_engine import STTEngine


class TranscribeRequest(BaseModel):
    path: str
    session_id: Optional[str] = None


class TranscribeResponse(BaseModel):
    session_id: Optional[str]
    text: str
    partials: list[str]
    engine: str


def create_app() -> FastAPI:
    config = get_config()
    logger = get_logger("STTService", config=config)
    engine = STTEngine(config)

    app = FastAPI(title="Envy STT Service", version="0.1.0")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "engine": "vosk" if engine.model else "fallback"}

    @app.post("/transcribe-file", response_model=TranscribeResponse, dependencies=[Depends(verify_secret)])
    async def transcribe_file(request: TranscribeRequest) -> TranscribeResponse:
        audio_path = Path(request.path)
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail=f"Audio file not found: {audio_path}")
        result = engine.transcribe_file(audio_path)
        logger.info(f"Transcription for {audio_path}: {result.text}")
        return TranscribeResponse(
            session_id=request.session_id,
            text=result.text,
            partials=result.partials,
            engine=result.engine,
        )

    @app.post("/transcribe-upload", response_model=TranscribeResponse, dependencies=[Depends(verify_secret)])
    async def transcribe_upload(
        file: UploadFile = File(...),
        session_id: Optional[str] = None,
    ) -> TranscribeResponse:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            tmp.write(await file.read())
            tmp.flush()
            temp_path = Path(tmp.name)
        try:
            result = engine.transcribe_file(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)
        logger.info(f"Transcription for uploaded file: {result.text}")
        return TranscribeResponse(session_id=session_id, text=result.text, partials=result.partials, engine=result.engine)

    @app.post("/transcribe-stream", dependencies=[Depends(verify_secret)])
    async def transcribe_stream(request: TranscribeRequest):
        audio_path = Path(request.path)
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail=f"Audio file not found: {audio_path}")

        queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def emit_partial(text: str) -> None:
            queue.put_nowait(("partial", text))

        def run_transcription() -> None:
            result = engine.transcribe_file(audio_path, emit_partial=emit_partial)
            queue.put_nowait(("complete", json.dumps({
                "session_id": request.session_id,
                "text": result.text,
                "engine": result.engine,
            })))

        loop.run_in_executor(None, run_transcription)

        async def event_generator():
            while True:
                event, payload = await queue.get()
                if event == "partial":
                    yield {"event": "partial", "data": payload}
                elif event == "complete":
                    yield {"event": "complete", "data": payload}
                    break

        return EventSourceResponse(event_generator())

    return app


app = create_app()


def main(
    host: str = typer.Option("0.0.0.0", help="Host for the STT service."),
    port: int = typer.Option(8202, help="Port for the STT service."),
    reload: bool = typer.Option(False, help="Enable autoreload (development only)."),
) -> None:
    uvicorn.run("envy.services.stt_service.main:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    typer.run(main)
