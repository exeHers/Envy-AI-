"""Web dashboard for Envy."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.config_loader import EnvyConfig
from services.utils import check_resources


class WebDashboard:
    """Web dashboard for Envy."""
    
    def __init__(self, config, orchestrator, logger: Optional[logging.Logger] = None):
        self.config = config
        self.orchestrator = orchestrator
        self.logger = logger or logging.getLogger("envy.web")
        self.app = FastAPI(title="Envy Dashboard")
        
        # CORS
        if config.web.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        # WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            return self._get_dashboard_html()
        
        @self.app.get("/api/status")
        async def get_status():
            resources = check_resources(self.config)
            return {
                "status": "running" if self.orchestrator.is_running else "stopped",
                "resources": resources
            }
        
        @self.app.get("/api/logs")
        async def get_logs():
            log_file = Path(self.config.logging.file)
            if log_file.exists():
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    return {"logs": lines[-100:]}  # Last 100 lines
            return {"logs": []}
        
        @self.app.post("/api/command")
        async def send_command(command: dict):
            text = command.get('text', '')
            if not text:
                raise HTTPException(status_code=400, detail="No command text provided")
            
            self.orchestrator.process_command(text)
            return {"success": True, "message": "Command processed"}
        
        @self.app.post("/api/confirm")
        async def confirm_action(confirmation: dict):
            skill_name = confirmation.get('skill_name')
            intent_data = confirmation.get('intent_data', {})
            
            if not skill_name:
                raise HTTPException(status_code=400, detail="No skill name provided")
            
            result = self.orchestrator.skill_manager.confirm_and_execute(skill_name, intent_data)
            return result
        
        @self.app.get("/api/files")
        async def list_files():
            # List files in workspace
            workspace = Path(".")
            files = []
            for file_path in workspace.rglob("*"):
                if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
                    files.append({
                        "path": str(file_path),
                        "size": file_path.stat().st_size
                    })
            return {"files": files[:100]}  # Limit to 100 files
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    # Echo back or process
                    await websocket.send_text(f"Echo: {data}")
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
    
    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML."""
        return """
<!DOCTYPE html>
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
            color: #e0e0e0;
            border-radius: 4px;
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
            margin: 5px 0;
            padding: 5px;
            border-left: 3px solid #4CAF50;
            padding-left: 10px;
        }
        .resources {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .resource-card {
            background: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
        }
        .resource-label { color: #888; font-size: 12px; }
        .resource-value { color: #4CAF50; font-size: 24px; font-weight: bold; }
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
            <div id="resources" class="resources"></div>
        </div>
        
        <div class="command-input">
            <h2>Send Command</h2>
            <input type="text" id="command-input" placeholder="Type a command or speak 'Envy' to activate voice...">
            <button onclick="sendCommand()">Send</button>
        </div>
        
        <div class="logs">
            <h2>Logs</h2>
            <div id="log-container"></div>
        </div>
    </div>
    
    <script>
        const commandInput = document.getElementById('command-input');
        const logContainer = document.getElementById('log-container');
        const statusText = document.getElementById('status-text');
        const resourcesDiv = document.getElementById('resources');
        
        commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendCommand();
            }
        });
        
        async function sendCommand() {
            const text = commandInput.value.trim();
            if (!text) return;
            
            addLog('User: ' + text);
            commandInput.value = '';
            
            try {
                const response = await fetch('/api/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text})
                });
                const data = await response.json();
                addLog('Envy: ' + (data.message || 'Command processed'));
            } catch (error) {
                addLog('Error: ' + error.message);
            }
        }
        
        function addLog(message) {
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.textContent = new Date().toLocaleTimeString() + ' - ' + message;
            logContainer.appendChild(entry);
            logContainer.scrollTop = logContainer.scrollHeight;
        }
        
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                statusText.textContent = data.status === 'running' ? 'Running' : 'Stopped';
                
                // Update resources
                if (data.resources) {
                    resourcesDiv.innerHTML = `
                        <div class="resource-card">
                            <div class="resource-label">CPU</div>
                            <div class="resource-value">${data.resources.cpu_percent.toFixed(1)}%</div>
                        </div>
                        <div class="resource-card">
                            <div class="resource-label">Memory</div>
                            <div class="resource-value">${(data.resources.memory_mb / 1024).toFixed(1)}GB</div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Status update error:', error);
            }
        }
        
        async function loadLogs() {
            try {
                const response = await fetch('/api/logs');
                const data = await response.json();
                logContainer.innerHTML = '';
                data.logs.forEach(line => {
                    addLog(line.trim());
                });
            } catch (error) {
                console.error('Log load error:', error);
            }
        }
        
        // Update status every 5 seconds
        setInterval(updateStatus, 5000);
        updateStatus();
        
        // Load logs on start
        loadLogs();
        setInterval(loadLogs, 10000);
    </script>
</body>
</html>
        """
    
    def run(self):
        """Run the web dashboard."""
        import uvicorn
        uvicorn.run(
            self.app,
            host=self.config.web.host,
            port=self.config.web.port,
            log_level=self.config.web.log_level
        )
