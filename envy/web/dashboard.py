"""
Web Dashboard for Envy
FastAPI-based web interface for monitoring and control
MIT License
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.config_manager import get_config

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Envy Dashboard", version="1.0.0")

# Global state
envy_state = {
    'status': 'stopped',
    'router': None,
    'logs': [],
    'max_logs': 100
}

# WebSocket connections
active_connections: List[WebSocket] = []


# Templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Envy Dashboard"
    })


@app.get("/api/status")
async def get_status():
    """Get current system status"""
    config = get_config()
    
    return {
        'status': envy_state['status'],
        'version': config.get('system.version', '1.0.0'),
        'profile': config.get_profile(),
        'gpu_enabled': config.is_gpu_enabled(),
        'skills_count': len(config.get('skills.enabled', [])),
        'uptime': 0  # TODO: track actual uptime
    }


@app.get("/api/config")
async def get_config_api():
    """Get current configuration"""
    config = get_config()
    return {
        'profile': config.get_profile(),
        'wake_keyword': config.get('wake.keyword'),
        'stt_engine': config.get('stt.engine'),
        'tts_engine': config.get('tts.engine'),
        'llm_primary': config.get('llm.primary'),
        'enabled_skills': config.get('skills.enabled', [])
    }


@app.post("/api/command")
async def execute_command(data: Dict[str, Any]):
    """Execute manual command"""
    try:
        command = data.get('command', '')
        
        if not command:
            return {'success': False, 'error': 'No command provided'}
        
        logger.info(f"Manual command: {command}")
        
        # Execute command via router if available
        if envy_state.get('router'):
            result = envy_state['router'].handle_manual_command(command)
            
            # Broadcast to websockets
            await broadcast_log({
                'type': 'command',
                'command': command,
                'response': result.get('response', ''),
                'timestamp': result.get('timestamp')
            })
            
            return result
        else:
            return {
                'success': False,
                'error': 'Envy is not running'
            }
            
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@app.get("/api/logs")
async def get_logs():
    """Get recent logs"""
    return {
        'logs': envy_state['logs'][-50:]  # Last 50 logs
    }


@app.post("/api/control/{action}")
async def control_action(action: str):
    """Control Envy (start/stop/restart)"""
    try:
        if action == 'start':
            # TODO: Start Envy services
            envy_state['status'] = 'running'
            await broadcast_log({'type': 'system', 'message': 'Envy started'})
            return {'success': True, 'status': 'running'}
        
        elif action == 'stop':
            # TODO: Stop Envy services
            envy_state['status'] = 'stopped'
            await broadcast_log({'type': 'system', 'message': 'Envy stopped'})
            return {'success': True, 'status': 'stopped'}
        
        elif action == 'restart':
            # TODO: Restart Envy services
            envy_state['status'] = 'running'
            await broadcast_log({'type': 'system', 'message': 'Envy restarted'})
            return {'success': True, 'status': 'running'}
        
        else:
            return {'success': False, 'error': f'Unknown action: {action}'}
            
    except Exception as e:
        logger.error(f"Control action failed: {e}")
        return {'success': False, 'error': str(e)}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial status
        await websocket.send_json({
            'type': 'status',
            'data': await get_status()
        })
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Echo back for now
            await websocket.send_json({
                'type': 'echo',
                'data': data
            })
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("WebSocket disconnected")


async def broadcast_log(log_entry: Dict[str, Any]):
    """Broadcast log entry to all connected websockets"""
    envy_state['logs'].append(log_entry)
    
    # Trim logs
    if len(envy_state['logs']) > envy_state['max_logs']:
        envy_state['logs'] = envy_state['logs'][-envy_state['max_logs']:]
    
    # Broadcast to all connections
    for connection in active_connections:
        try:
            await connection.send_json({
                'type': 'log',
                'data': log_entry
            })
        except:
            pass


def set_router(router):
    """Set router instance for command execution"""
    envy_state['router'] = router
    logger.info("Router registered with dashboard")


def start_dashboard(host: str = "127.0.0.1", port: int = 8080):
    """Start dashboard server"""
    logger.info(f"Starting dashboard on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    # Get config
    config = get_config()
    host = config.get('web.host', '127.0.0.1')
    port = config.get('web.port', 8080)
    
    start_dashboard(host, port)
