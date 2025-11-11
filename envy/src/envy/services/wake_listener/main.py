from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

import typer
import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from ..common.deps import get_config, verify_secret
from ..common.logging import get_logger
from .wake_detector import WakeDetector


class DetectRequest(BaseModel):
    path: str
    session_id: Optional[str] = None


class DetectResponse(BaseModel):
    session_id: Optional[str]
    keyword: str
    detected: bool


def create_app() -> FastAPI:
    config = get_config()
    logger = get_logger("WakeListenerService", config=config)
    detector = WakeDetector(config)

    app = FastAPI(title="Envy Wake Listener", version="0.1.0")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "profile": config.profile}

    @app.post("/detect-file", response_model=DetectResponse, dependencies=[Depends(verify_secret)])
    async def detect_file(request: DetectRequest) -> DetectResponse:
        audio_path = Path(request.path)
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail=f"Audio file not found: {audio_path}")
        detected = detector.detect_from_file(audio_path)
        logger.info(f"Wake detection for {audio_path}: {detected}")
        return DetectResponse(session_id=request.session_id, keyword=detector.keyword, detected=detected)

    @app.post("/detect-upload", response_model=DetectResponse, dependencies=[Depends(verify_secret)])
    async def detect_upload(file: UploadFile = File(...), session_id: Optional[str] = None) -> DetectResponse:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            tmp.write(await file.read())
            tmp.flush()
            temp_path = Path(tmp.name)
        try:
            detected = detector.detect_from_file(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)
        logger.info(f"Wake detection on uploaded file: {detected}")
        return DetectResponse(session_id=session_id, keyword=detector.keyword, detected=detected)

    return app


app = create_app()


def main(
    host: str = typer.Option("0.0.0.0", help="Host for the wake listener service."),
    port: int = typer.Option(8201, help="Port for the wake listener service."),
    reload: bool = typer.Option(False, help="Enable autoreload (development only)."),
) -> None:
    uvicorn.run("envy.services.wake_listener.main:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    typer.run(main)
