"""
Web dashboard for Envy assistant using FastAPI.
"""
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WebDashboard:
    """Web dashboard for Envy assistant."""
    
    def __init__(self, config: dict, router, tts_service, skill_manager):
        self.config = config
        self.router = router
        self.tts_service = tts_service
        self.skill_manager = skill_manager
        self.app = FastAPI(title="Envy Dashboard")
        self.pending_confirmations: Dict[str, Dict[str, Any]] = {}
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            """Main dashboard page."""
            return """
<!DOCTYPE html>
<html>
<head>
    <title>Envy Personal Assistant</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        .subtitle { opacity: 0.9; }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .section h2 {
            margin-bottom: 15px;
            color: #667eea;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        button {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover { background: #5568d3; }
        button.danger { background: #e74c3c; }
        button.danger:hover { background: #c0392b; }
        .log {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            max-height: 400px;
            overflow-y: auto;
            margin-top: 10px;
        }
        .log-entry {
            margin-bottom: 5px;
            padding: 5px;
        }
        .log-entry.info { color: #4ec9b0; }
        .log-entry.warning { color: #dcdcaa; }
        .log-entry.error { color: #f48771; }
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .status.active { background: #2ecc71; color: white; }
        .status.inactive { background: #95a5a6; color: white; }
        .confirmation-box {
            background: #fff3cd;
            border: 2px solid #ffc107;
            padding: 15px;
            border-radius: 6px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 Envy</h1>
            <p class="subtitle">Personal Assistant Dashboard</p>
        </header>
        <div class="content">
            <div class="section">
                <h2>Status</h2>
                <p>Status: <span class="status active" id="status">Active</span></p>
            </div>
            
            <div class="section">
                <h2>Manual Command</h2>
                <input type="text" id="commandInput" placeholder="Type a command (e.g., 'create test.py that prints hello')">
                <button onclick="sendCommand()">Send</button>
            </div>
            
            <div class="section">
                <h2>Activity Log</h2>
                <div class="log" id="log"></div>
            </div>
            
            <div class="section" id="confirmations" style="display: none;">
                <h2>Pending Confirmations</h2>
                <div id="confirmationList"></div>
            </div>
        </div>
    </div>
    
    <script>
        const log = document.getElementById('log');
        const commandInput = document.getElementById('commandInput');
        
        function addLog(message, type = 'info') {
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;
        }
        
        async function sendCommand() {
            const command = commandInput.value.trim();
            if (!command) return;
            
            addLog(`Sending: ${command}`, 'info');
            commandInput.value = '';
            
            try {
                const response = await fetch('/api/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: command})
                });
                
                const data = await response.json();
                
                if (data.requires_confirmation) {
                    addLog(`Confirmation required: ${data.response}`, 'warning');
                    showConfirmation(data);
                } else {
                    addLog(`Response: ${data.response}`, 'info');
                    if (data.outputs && data.outputs.length > 0) {
                        data.outputs.forEach(output => {
                            if (output.type === 'file') {
                                addLog(`Created file: ${output.path}`, 'info');
                            }
                        });
                    }
                }
            } catch (error) {
                addLog(`Error: ${error.message}`, 'error');
            }
        }
        
        function showConfirmation(data) {
            const confirmSection = document.getElementById('confirmations');
            const confirmList = document.getElementById('confirmationList');
            confirmSection.style.display = 'block';
            
            const box = document.createElement('div');
            box.className = 'confirmation-box';
            box.innerHTML = `
                <p><strong>Action:</strong> ${data.user_text}</p>
                <button onclick="confirmAction('${data.id}')">Confirm</button>
                <button class="danger" onclick="cancelAction('${data.id}')">Cancel</button>
            `;
            confirmList.appendChild(box);
        }
        
        commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendCommand();
        });
        
        // Load initial log
        addLog('Envy dashboard ready', 'info');
    </script>
</body>
</html>
            """
        
        @self.app.post("/api/command")
        async def handle_command(request: Request):
            """Handle manual command from dashboard."""
            data = await request.json()
            command = data.get('command', '')
            
            if not command:
                raise HTTPException(status_code=400, detail="Command required")
            
            # Route command
            result = await self.router.route(command)
            
            if result.get('requires_confirmation'):
                # Store confirmation request
                import uuid
                confirmation_id = str(uuid.uuid4())
                self.pending_confirmations[confirmation_id] = {
                    'id': confirmation_id,
                    'user_text': result.get('user_text', command),
                    'skill': result.get('skill'),
                    'result': result
                }
                result['id'] = confirmation_id
            
            return JSONResponse(result)
        
        @self.app.post("/api/confirm/{confirmation_id}")
        async def confirm_action(confirmation_id: str):
            """Confirm a pending action."""
            if confirmation_id not in self.pending_confirmations:
                raise HTTPException(status_code=404, detail="Confirmation not found")
            
            confirmation = self.pending_confirmations.pop(confirmation_id)
            user_text = confirmation['user_text']
            skill_name = confirmation['skill']
            
            # Execute the action
            skill = self.skill_manager.get_skill(skill_name)
            if skill:
                result = await skill.execute(user_text, {})
                return JSONResponse(result)
            
            return JSONResponse({'success': False, 'response': 'Skill not found'})
        
        @self.app.get("/api/status")
        async def get_status():
            """Get assistant status."""
            return JSONResponse({
                'status': 'active',
                'skills': self.skill_manager.list_skills(),
                'pending_confirmations': len(self.pending_confirmations)
            })
    
    def get_app(self):
        """Get FastAPI app instance."""
        return self.app
