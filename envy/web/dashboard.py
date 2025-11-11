#!/usr/bin/env python3
"""
Envy Web Dashboard
FastAPI backend for web interface
"""
from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging
import uvicorn
from pathlib import Path
from typing import List
import json

from services.config_loader import get_config
from services.router import Router


app = FastAPI(title="Envy Dashboard")

# Setup
config = get_config()
logger = logging.getLogger("Dashboard")

# Templates directory
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Global router instance (will be initialized when server starts)
router = None


@app.on_event("startup")
async def startup():
    """Initialize services on startup"""
    global router
    logger.info("Initializing dashboard services...")
    try:
        router = Router()
        logger.info("Dashboard services initialized")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Envy Dashboard"
    })


@app.get("/api/status")
async def get_status():
    """Get system status"""
    profile = config.get_profile()
    resources = config.get_resource_limits()
    
    return JSONResponse({
        "status": "online",
        "profile": profile,
        "resources": resources,
        "services": {
            "wake_listener": "active",
            "stt": "ready",
            "tts": "ready",
            "llm": "ready"
        }
    })


@app.get("/api/config")
async def get_config_api():
    """Get current configuration"""
    return JSONResponse(config.config)


@app.post("/api/config")
async def update_config(data: dict):
    """Update configuration"""
    try:
        for key, value in data.items():
            config.set(key, value)
        config.save()
        return JSONResponse({"success": True, "message": "Configuration updated"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@app.post("/api/command")
async def execute_command(data: dict):
    """Execute voice command via API"""
    command = data.get('command', '')
    
    if not command:
        return JSONResponse({"success": False, "error": "No command provided"}, status_code=400)
    
    if not router:
        return JSONResponse({"success": False, "error": "Router not initialized"}, status_code=500)
    
    try:
        response = router.process_command(command)
        return JSONResponse({
            "success": True,
            "response": response
        })
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries"""
    log_file = Path(__file__).parent.parent / "logs" / "envy.log"
    
    if not log_file.exists():
        return JSONResponse({"logs": []})
    
    try:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
        
        return JSONResponse({"logs": recent_lines})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/files")
async def list_files(path: str = "workspace"):
    """List files in workspace"""
    base_dir = Path(__file__).parent.parent
    target_dir = base_dir / path
    
    if not target_dir.exists():
        return JSONResponse({"files": []})
    
    try:
        files = []
        for item in target_dir.iterdir():
            files.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0
            })
        
        return JSONResponse({"files": files})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def run_dashboard(host: str = None, port: int = None):
    """Run dashboard server"""
    if host is None:
        host = config.get('web.host', '127.0.0.1')
    if port is None:
        port = config.get('web.port', 8080)
    
    logger.info(f"Starting dashboard on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_dashboard()
