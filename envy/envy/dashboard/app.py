from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import httpx
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger("envy.dashboard")


@dataclass
class DashboardConfig:
    router_url: str = "http://127.0.0.1:7000"
    artifacts_dir: Path = Path("/workspace/envy/artifacts")
    logs_dir: Path = Path("/workspace/envy/logs")


def create_app(config: DashboardConfig) -> FastAPI:
    templates_path = Path(__file__).resolve().parent / "templates"
    static_path = Path(__file__).resolve().parent / "static"
    templates = Environment(loader=FileSystemLoader(str(templates_path)), autoescape=select_autoescape())

    app = FastAPI(title="Envy Dashboard")
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request):
        context = await _gather_context(config)
        template = templates.get_template("index.html")
        html = template.render(**context)
        return HTMLResponse(html)

    @app.post("/confirm/{action_id}")
    async def confirm_action(action_id: str):
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(f"{config.router_url}/confirm/dashboard", json={"action_id": action_id})
        return RedirectResponse("/", status_code=303)

    @app.get("/api/pending")
    async def api_pending():
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{config.router_url}/pending-actions")
            resp.raise_for_status()
            return JSONResponse(resp.json())

    return app


async def _gather_context(config: DashboardConfig) -> Dict[str, Any]:
    pending = []
    router_health = {}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            pending_resp = await client.get(f"{config.router_url}/pending-actions")
            pending_resp.raise_for_status()
            pending = pending_resp.json()
            health_resp = await client.get(f"{config.router_url}/health")
            health_resp.raise_for_status()
            router_health = health_resp.json()
    except Exception as exc:
        logger.warning("Failed to query router: %s", exc)

    logs = _tail_logs(config.logs_dir / "envy.log", 50)
    return {
        "pending_actions": pending,
        "router_health": router_health,
        "logs": logs,
    }


def _tail_logs(log_path: Path, lines: int) -> list[str]:
    if not log_path.exists():
        return []
    content = log_path.read_text(encoding="utf-8").splitlines()
    return content[-lines:]
