"""Web dashboard for Envy."""
import asyncio
from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.config_loader import get_config
from services.logger import setup_logger


app = FastAPI(title="Envy Dashboard")
config = get_config()
logger = setup_logger("Dashboard", config.get("logging.file"))

# Templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Store active connections
active_connections = []

# Store logs
recent_logs = []
max_logs = 100


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/status")
async def get_status():
    """Get system status."""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "profile": config.get("profile"),
            "wake_word": config.get("wake_word.keyword"),
            "stt_engine": config.get("stt.engine"),
            "tts_engine": config.get("tts.engine"),
            "llm_local": config.get("llm.local.enabled"),
            "llm_remote": config.get("llm.remote.enabled")
        }
    }


@app.get("/api/logs")
async def get_logs():
    """Get recent logs."""
    return {"logs": recent_logs}


@app.post("/api/command")
async def execute_command(request: Request):
    """Execute a manual command."""
    data = await request.json()
    command = data.get("command", "")
    
    logger.info(f"Manual command: {command}")
    
    # This would integrate with the router
    # For now, just echo back
    return {
        "success": True,
        "command": command,
        "response": f"Command received: {command}"
    }


@app.post("/api/confirm")
async def confirm_action(request: Request):
    """Confirm a pending action."""
    data = await request.json()
    action_id = data.get("action_id")
    confirmed = data.get("confirmed", False)
    
    logger.info(f"Action {action_id} confirmed: {confirmed}")
    
    return {
        "success": True,
        "action_id": action_id,
        "confirmed": confirmed
    }


@app.get("/api/config")
async def get_config_api():
    """Get current configuration."""
    return {"config": config.config}


@app.post("/api/config")
async def update_config(request: Request):
    """Update configuration."""
    data = await request.json()
    
    # Update config (simplified)
    for key, value in data.items():
        parts = key.split('.')
        current = config.config
        for part in parts[:-1]:
            current = current.get(part, {})
        if isinstance(current, dict):
            current[parts[-1]] = value
            
    config.save()
    
    return {"success": True, "message": "Configuration updated"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            logger.debug(f"WebSocket received: {data}")
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)


async def broadcast_log(message: str):
    """Broadcast log message to all connected clients."""
    recent_logs.append({
        "timestamp": datetime.now().isoformat(),
        "message": message
    })
    
    # Keep only recent logs
    if len(recent_logs) > max_logs:
        recent_logs.pop(0)
        
    # Broadcast to websockets
    for connection in active_connections:
        try:
            await connection.send_json({
                "type": "log",
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass


def start_dashboard(host: str = None, port: int = None):
    """Start the dashboard server."""
    import uvicorn
    
    host = host or config.get("web.host", "127.0.0.1")
    port = port or config.get("web.port", 8080)
    
    logger.info(f"Starting dashboard on {host}:{port}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_dashboard()
