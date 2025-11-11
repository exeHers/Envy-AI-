from __future__ import annotations

from typing import Dict

import typer
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..common.config import PROJECT_ROOT
from ..common.deps import get_config, verify_secret
from ..common.logging import get_logger
from ..common.messaging import ServiceClient


def create_app() -> FastAPI:
    config = get_config()
    logger = get_logger("WebDashboard", config=config)
    templates_dir = PROJECT_ROOT / "src" / "envy" / "services" / "web_dashboard" / "templates"
    static_dir = PROJECT_ROOT / "src" / "envy" / "services" / "web_dashboard" / "static"
    templates = Jinja2Templates(directory=str(templates_dir))

    router_client = ServiceClient(config.get("messaging.router_url"), config)

    service_map: Dict[str, str] = {
        "wake_listener": config.get("messaging.wake_url", "http://127.0.0.1:8201"),
        "stt_service": config.get("messaging.stt_url"),
        "tts_service": config.get("messaging.tts_url"),
        "skill_manager": config.get("messaging.skill_manager_url"),
        "router": config.get("messaging.router_url"),
    }

    app = FastAPI(title="Envy Dashboard", version="0.1.0")
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "profile": config.profile,
                "config": config,
            },
        )

    @app.get("/api/status", dependencies=[Depends(verify_secret)])
    async def api_status() -> Dict[str, Dict]:
        status = {}
        for name, url in service_map.items():
            client = ServiceClient(url, config)
            try:
                health = client.get_json("/health")
                status[name] = {"status": "up", "details": health}
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Healthcheck failed for {name}: {exc}")
                status[name] = {"status": "down", "details": {"error": str(exc)}}
        return status

    @app.get("/api/sessions", dependencies=[Depends(verify_secret)])
    async def api_sessions() -> Dict[str, list]:
        sessions = router_client.get_json("/sessions")
        return sessions

    @app.post("/api/confirm", dependencies=[Depends(verify_secret)])
    async def api_confirm(request: Request) -> Dict[str, object]:
        payload = await request.json()
        if "action_id" not in payload or "channel" not in payload:
            raise HTTPException(status_code=400, detail="action_id and channel required")
        response = router_client.post_json("/confirm", payload)
        return response

    @app.get("/api/logs", dependencies=[Depends(verify_secret)])
    async def api_logs(limit: int = 200) -> JSONResponse:
        logs_dir = config.get("runtime.logs_dir", "artifacts/logs")
        log_path = (PROJECT_ROOT / logs_dir).resolve() / "envy.log"
        if not log_path.exists():
            return JSONResponse({"entries": []})
        lines = log_path.read_text(encoding="utf-8").splitlines()[-limit:]
        return JSONResponse({"entries": lines})

    return app


app = create_app()


def main(
    host: str = typer.Option("0.0.0.0", help="Host for the dashboard service."),
    port: int = typer.Option(8300, help="Port for the dashboard service."),
    reload: bool = typer.Option(False, help="Enable autoreload (development only)."),
) -> None:
    uvicorn.run("envy.services.web_dashboard.main:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    typer.run(main)
