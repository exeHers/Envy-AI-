#!/usr/bin/env python3
"""
Web Dashboard
FastAPI-based web interface for Envy.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    print("ERROR: Missing dependencies. Run: pip install fastapi uvicorn websockets")
    import sys
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebDashboard:
    """Web dashboard for Envy."""
    
    def __init__(self, config: dict, services: Dict[str, Any]):
        self.config = config
        self.services = services
        self.host = config.get('host', '0.0.0.0')
        self.port = config.get('port', 8080)
        self.debug = config.get('debug', False)
        
        self.app = FastAPI(title="Envy Dashboard")
        
        # CORS
        if config.get('enable_cors', True):
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            return self._get_dashboard_html()
        
        @self.app.get("/api/status")
        async def status():
            return {
                'status': 'running',
                'services': {
                    'wake': 'active' if 'wake' in self.services else 'inactive',
                    'stt': 'active' if 'stt' in self.services else 'inactive',
                    'tts': 'active' if 'tts' in self.services else 'inactive',
                    'llm': 'active' if 'llm' in self.services else 'inactive',
                }
            }
        
        @self.app.post("/api/command")
        async def command(data: dict):
            """Execute a command via web interface."""
            text = data.get('text', '')
            if not text:
                return {'success': False, 'error': 'No text provided'}
            
            try:
                # Route and execute
                skill_name, params = self.services['router'].route(text)
                result = self.services['skills'].execute(skill_name, params, require_confirmation=False)
                
                return result
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                return {'success': False, 'error': str(e)}
        
        @self.app.get("/api/logs")
        async def logs():
            """Get recent logs."""
            log_file = Path('artifacts/envy.log')
            if log_file.exists():
                lines = log_file.read_text().split('\n')[-100:]
                return {'logs': lines}
            return {'logs': []}
        
        @self.app.get("/api/skills")
        async def skills():
            """List available skills."""
            if 'skills' in self.services:
                return {'skills': self.services['skills'].list_skills()}
            return {'skills': []}
    
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
        .status { background: #2a2a2a; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .status-item { margin: 10px 0; }
        .status-active { color: #4CAF50; }
        .status-inactive { color: #f44336; }
        .command-box {
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
            margin-top: 10px;
            padding: 12px 24px;
            background: #4CAF50;
            border: none;
            border-radius: 4px;
            color: white;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background: #45a049; }
        .logs {
            background: #1a1a1a;
            padding: 15px;
            border-radius: 8px;
            max-height: 400px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
        .log-entry { margin: 5px 0; color: #888; }
        .result {
            margin-top: 15px;
            padding: 15px;
            background: #2a2a2a;
            border-radius: 4px;
            border-left: 4px solid #4CAF50;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Envy Personal Assistant</h1>
        
        <div class="status" id="status">
            <h2>Status</h2>
            <div id="status-content">Loading...</div>
        </div>
        
        <div class="command-box">
            <h2>Command</h2>
            <input type="text" id="command-input" placeholder="Type a command or speak to Envy..." />
            <button onclick="sendCommand()">Send</button>
            <div id="result"></div>
        </div>
        
        <div class="logs">
            <h2>Logs</h2>
            <div id="logs-content"></div>
        </div>
    </div>
    
    <script>
        async function updateStatus() {
            const res = await fetch('/api/status');
            const data = await res.json();
            const statusDiv = document.getElementById('status-content');
            statusDiv.innerHTML = Object.entries(data.services).map(([name, status]) => 
                `<div class="status-item">
                    ${name}: <span class="status-${status}">${status}</span>
                </div>`
            ).join('');
        }
        
        async function updateLogs() {
            const res = await fetch('/api/logs');
            const data = await res.json();
            const logsDiv = document.getElementById('logs-content');
            logsDiv.innerHTML = data.logs.slice(-20).map(log => 
                `<div class="log-entry">${log}</div>`
            ).join('');
        }
        
        async function sendCommand() {
            const input = document.getElementById('command-input');
            const text = input.value.trim();
            if (!text) return;
            
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '<div class="result">Processing...</div>';
            
            const res = await fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text})
            });
            
            const data = await res.json();
            resultDiv.innerHTML = `<div class="result">
                <strong>Result:</strong><br/>
                ${JSON.stringify(data, null, 2)}
            </div>`;
            
            input.value = '';
            updateLogs();
        }
        
        document.getElementById('command-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendCommand();
        });
        
        setInterval(updateStatus, 2000);
        setInterval(updateLogs, 3000);
        updateStatus();
        updateLogs();
    </script>
</body>
</html>"""
    
    def run(self):
        """Run the web server."""
        import uvicorn
        
        logger.info(f"Starting web dashboard on {self.host}:{self.port}")
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level='info' if self.debug else 'warning'
        )


def main():
    """Main entry point."""
    import yaml
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent.parent / 'config' / 'envy.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    web_config = config.get('web', {})
    dashboard = WebDashboard(web_config, {})
    dashboard.run()


if __name__ == '__main__':
    main()
