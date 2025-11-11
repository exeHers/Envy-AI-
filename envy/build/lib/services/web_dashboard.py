"""Web dashboard service for Envy."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

from ..config import EnvyConfig, load_config
from ..logging_config import configure_logging

LOGGER = logging.getLogger("envy.dashboard")


class CommandRequest(BaseModel):
    text: str


class DashboardConfirmRequest(BaseModel):
    confirmation_id: str
    approved: bool = True


class WebDashboard:
    def __init__(self, config: EnvyConfig):
        self.config = config
        self.router_url = config.services["router"].url()
        self.client = httpx.AsyncClient(timeout=30)

    async def get_sessions(self):
        response = await self.client.get(f"{self.router_url}/sessions")
        response.raise_for_status()
        return response.json()

    async def get_confirmations(self):
        response = await self.client.get(f"{self.router_url}/pending-confirmations")
        response.raise_for_status()
        return response.json()

    async def send_command(self, text: str):
        payload = {"text": text}
        response = await self.client.post(f"{self.router_url}/session/from-text", json=payload)
        response.raise_for_status()
        return response.json()

    async def confirm(self, confirmation_id: str, approved: bool):
        payload = {"confirmation_id": confirmation_id, "approved": approved, "approver": "dashboard"}
        response = await self.client.post(f"{self.router_url}/confirm", json=payload)
        response.raise_for_status()
        return response.json()

    async def shutdown(self):
        await self.client.aclose()


def create_app(config: EnvyConfig) -> FastAPI:
    dashboard = WebDashboard(config)
    app = FastAPI(title="Envy Dashboard", version="0.1.0")
    base_dir = Path(__file__).resolve().parents[2]
    static_dir = base_dir / "web" / "static"
    template_dir = base_dir / "web" / "templates"
    templates = Jinja2Templates(directory=str(template_dir))

    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.on_event("shutdown")
    async def shutdown_event():
        await dashboard.shutdown()

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/api/sessions")
    async def api_sessions():
        return await dashboard.get_sessions()

    @app.get("/api/pending-confirmations")
    async def api_confirmations():
        return await dashboard.get_confirmations()

    @app.post("/api/command")
    async def api_command(request: CommandRequest):
        return await dashboard.send_command(request.text)

    @app.post("/api/confirm")
    async def api_confirm(request: DashboardConfirmRequest):
        return await dashboard.confirm(request.confirmation_id, request.approved)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Envy web dashboard service.")
    parser.add_argument("--config", type=str, default=str(CONFIG_PATH := Path(__file__).resolve().parents[2] / "config" / "envy.yaml"))
    parser.add_argument("--host", type=str, help="Override host binding")
    parser.add_argument("--port", type=int, help="Override port binding")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    service_conf = config.services["dashboard"]
    host = args.host or service_conf.host
    port = args.port or service_conf.port

    configure_logging(config, "web_dashboard")
    app = create_app(config)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    main()

