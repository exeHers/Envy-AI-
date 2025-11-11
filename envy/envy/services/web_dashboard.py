from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.templating import Jinja2Templates

LOGGER = logging.getLogger(__name__)


@dataclass
class DashboardEvent:
    timestamp: float
    level: str
    message: str


@dataclass
class DashboardState:
    last_transcript: str = ""
    last_response: str = ""
    pending_confirmation: Optional[str] = None
    voice_confirmed: bool = False
    dashboard_confirmed: bool = False
    events: List[DashboardEvent] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "last_transcript": self.last_transcript,
            "last_response": self.last_response,
            "pending_confirmation": self.pending_confirmation,
            "voice_confirmed": self.voice_confirmed,
            "dashboard_confirmed": self.dashboard_confirmed,
            "events": [
                {"timestamp": ev.timestamp, "level": ev.level, "message": ev.message}
                for ev in self.events[-200:]
            ],
        }

    def add_event(self, level: str, message: str, timestamp: float) -> None:
        self.events.append(DashboardEvent(timestamp=timestamp, level=level, message=message))

    def request_confirmation(self, message: str) -> None:
        self.pending_confirmation = message
        self.dashboard_confirmed = False
        self.voice_confirmed = False

    def confirm(self) -> None:
        self.dashboard_confirmed = True

    def reset_confirmation(self) -> None:
        self.pending_confirmation = None
        self.dashboard_confirmed = False
        self.voice_confirmed = False


class ConfirmPayload(BaseModel):
    approve: bool


class DashboardService:
    def __init__(
        self,
        templates_dir: Path,
        static_dir: Path,
        host: str = "0.0.0.0",
        port: int = 8765,
    ) -> None:
        self.state = DashboardState()
        self.host = host
        self.port = port
        self.app = FastAPI(title="Envy Dashboard")
        self._lock = asyncio.Lock()
        self.templates = Jinja2Templates(directory=str(templates_dir))
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        self._register_routes()

    def _register_routes(self) -> None:
        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request) -> HTMLResponse:
            async with self._lock:
                context = {"request": request, "state": self.state.to_dict()}
            return self.templates.TemplateResponse("index.html", context)

        @self.app.get("/api/status")
        async def api_status() -> JSONResponse:
            async with self._lock:
                payload = self.state.to_dict()
            return JSONResponse(payload)

        @self.app.post("/api/confirm")
        async def api_confirm(payload: ConfirmPayload) -> JSONResponse:
            async with self._lock:
                if self.state.pending_confirmation is None:
                    raise HTTPException(status_code=400, detail="No action awaiting confirmation.")
                if payload.approve:
                    self.state.confirm()
                    LOGGER.info("Dashboard confirmation granted.")
                else:
                    self.state.reset_confirmation()
                    LOGGER.info("Dashboard confirmation rejected.")
            return JSONResponse({"status": "ok", "approved": payload.approve})

    async def log_event(self, level: str, message: str) -> None:
        async with self._lock:
            self.state.add_event(level=level, message=message, timestamp=asyncio.get_event_loop().time())

    async def set_transcript(self, transcript: str) -> None:
        async with self._lock:
            self.state.last_transcript = transcript

    async def set_response(self, response: str) -> None:
        async with self._lock:
            self.state.last_response = response

    async def request_confirmation(self, message: str) -> None:
        async with self._lock:
            self.state.request_confirmation(message)

    async def mark_voice_confirmed(self) -> None:
        async with self._lock:
            self.state.voice_confirmed = True

    async def reset_confirmation(self) -> None:
        async with self._lock:
            self.state.reset_confirmation()

    def get_app(self) -> FastAPI:
        return self.app
