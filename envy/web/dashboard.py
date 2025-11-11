"""Web dashboard for Envy using FastAPI."""
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from typing import Dict, List, Optional
import json
from pathlib import Path
import asyncio
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class CommandRequest(BaseModel):
    text: str


class EnvyWebDashboard:
    """Web dashboard for Envy."""
    
    def __init__(self, config, orchestrator):
        self.config = config
        self.orchestrator = orchestrator
        self.app = FastAPI(title="Envy Dashboard")
        self.connected_clients: List[WebSocket] = []
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            return self._get_dashboard_html()
        
        @self.app.get("/api/status")
        async def status():
            return {
                "status": "running" if self.orchestrator.running else "stopped",
                "profile": self.config.get("profile", "balanced"),
                "skills": self.config.get("skills.enabled", [])
            }
        
        @self.app.post("/api/command")
        async def command(cmd: CommandRequest):
            """Process text command."""
            try:
                result = self.orchestrator.router.route(cmd.text)
                
                # If requires confirmation, store it
                if result.get("requires_confirmation"):
                    self.orchestrator.pending_confirmation = result
                    return {
                        "success": False,
                        "requires_confirmation": True,
                        "message": result.get("response", "Confirmation required"),
                        "data": result.get("data", {})
                    }
                
                return result
            except Exception as e:
                logger.error(f"Command processing failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/confirm")
        async def confirm():
            """Confirm pending action."""
            if not self.orchestrator.pending_confirmation:
                return {"success": False, "message": "No pending confirmation"}
            
            # Execute confirmed action
            result = self.orchestrator.pending_confirmation
            self.orchestrator.pending_confirmation = None
            
            # Speak confirmation
            self.orchestrator.tts_service.speak("Confirmed. Executing.")
            
            return {"success": True, "result": result}
        
        @self.app.get("/api/logs")
        async def logs():
            """Get recent logs."""
            log_file = Path(self.config.get("logging.file", "artifacts/envy.log"))
            if log_file.exists():
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    return {"logs": lines[-100:]}  # Last 100 lines
            return {"logs": []}
        
        @self.app.get("/api/files")
        async def files():
            """List workspace files."""
            workspace_path = Path(self.config.get("skills.sandbox.allowed_paths", ["workspace"])[0])
            files = []
            if workspace_path.exists():
                for f in workspace_path.rglob("*"):
                    if f.is_file():
                        files.append({
                            "name": f.name,
                            "path": str(f.relative_to(workspace_path)),
                            "size": f.stat().st_size
                        })
            return {"files": files}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.connected_clients.append(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    # Echo back or process
                    await websocket.send_json({"message": f"Received: {data}"})
            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)
    
    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML."""
        return """<!DOCTYPE html>
<html>
<head>
    <title>Envy Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #4CAF50; margin-bottom: 20px; }
        .status { 
            background: #2a2a2a; 
            padding: 15px; 
            border-radius: 8px; 
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
            display: inline-block;
            margin-right: 8px;
        }
        .command-input {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            background: #1a1a1a;
            border: 1px solid #444;
            border-radius: 4px;
            color: #e0e0e0;
            font-size: 16px;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }
        button:hover { background: #45a049; }
        .logs {
            background: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        .log-entry {
            margin-bottom: 5px;
            padding: 5px;
            border-left: 3px solid #444;
            padding-left: 10px;
        }
        .files {
            background: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .file-item {
            padding: 8px;
            border-bottom: 1px solid #444;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Envy Personal Assistant</h1>
        
        <div class="status">
            <div>
                <span class="status-indicator"></span>
                <span id="status-text">Running</span>
            </div>
            <div id="profile">Profile: Balanced</div>
        </div>
        
        <div class="command-input">
            <h2>Command</h2>
            <input type="text" id="command-input" placeholder="Type a command or speak 'Envy' followed by your command">
            <button onclick="sendCommand()">Send</button>
        </div>
        
        <div class="logs">
            <h3>Logs</h3>
            <div id="logs-container"></div>
        </div>
        
        <div class="files">
            <h3>Workspace Files</h3>
            <div id="files-container"></div>
        </div>
    </div>
    
    <script>
        async function sendCommand() {
            const input = document.getElementById('command-input');
            const text = input.value.trim();
            if (!text) return;
            
            try {
                const response = await fetch('/api/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text})
                });
                const result = await response.json();
                
                addLog(`Command: ${text}`);
                addLog(`Response: ${result.response || result.message || 'Done'}`);
                
                if (result.requires_confirmation) {
                    if (confirm(result.message || 'Confirm this action?')) {
                        await fetch('/api/confirm', {method: 'POST'});
                        addLog('Action confirmed');
                    }
                }
                
                input.value = '';
                loadFiles();
            } catch (error) {
                addLog(`Error: ${error.message}`);
            }
        }
        
        function addLog(message) {
            const container = document.getElementById('logs-container');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.textContent = new Date().toLocaleTimeString() + ' - ' + message;
            container.appendChild(entry);
            container.scrollTop = container.scrollHeight;
        }
        
        async function loadFiles() {
            try {
                const response = await fetch('/api/files');
                const data = await response.json();
                const container = document.getElementById('files-container');
                container.innerHTML = '';
                data.files.forEach(file => {
                    const div = document.createElement('div');
                    div.className = 'file-item';
                    div.textContent = file.path + ' (' + formatSize(file.size) + ')';
                    container.appendChild(div);
                });
            } catch (error) {
                console.error('Failed to load files:', error);
            }
        }
        
        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB';
            return (bytes/(1024*1024)).toFixed(1) + ' MB';
        }
        
        async function loadStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                document.getElementById('status-text').textContent = 
                    data.status.charAt(0).toUpperCase() + data.status.slice(1);
                document.getElementById('profile').textContent = 
                    'Profile: ' + (data.profile || 'balanced').charAt(0).toUpperCase() + 
                    (data.profile || 'balanced').slice(1);
            } catch (error) {
                console.error('Failed to load status:', error);
            }
        }
        
        // Load initial data
        loadStatus();
        loadFiles();
        setInterval(loadFiles, 5000);
        
        // Enter key to send command
        document.getElementById('command-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendCommand();
            }
        });
    </script>
</body>
</html>"""


def create_app(config, orchestrator):
    """Create FastAPI app instance."""
    dashboard = EnvyWebDashboard(config, orchestrator)
    return dashboard.app
