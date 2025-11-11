#!/usr/bin/env python3
"""
Envy Web Dashboard - FastAPI-based web interface
Provides logs, config management, command input, and confirmation UI
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Envy AI Assistant Dashboard", version="1.0.0")

# Global assistant instance (set by main)
assistant_instance = None


# Request models
class CommandRequest(BaseModel):
    command: str


class ConfirmationRequest(BaseModel):
    confirmation_id: str
    action: str  # 'confirm' or 'cancel'


# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard_home():
    """Serve main dashboard page"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Envy AI Assistant</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 10px;
        }
        
        .command-input {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        input[type="text"] {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            padding: 15px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #5568d3;
        }
        
        button:active {
            transform: scale(0.98);
        }
        
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .status.active {
            background: #4caf50;
            color: white;
        }
        
        .status.inactive {
            background: #f44336;
            color: white;
        }
        
        .log-container {
            background: #f5f5f5;
            border-radius: 8px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .log-entry {
            padding: 5px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .log-entry:last-child {
            border-bottom: none;
        }
        
        .response-box {
            background: #f0f7ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-top: 15px;
            border-radius: 5px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-box h3 {
            font-size: 2em;
            margin-bottom: 5px;
        }
        
        .stat-box p {
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎤 Envy</h1>
            <p>Your Personal AI Assistant</p>
        </div>
        
        <div class="card">
            <h2>Status</h2>
            <p>System Status: <span class="status active" id="status">Active</span></p>
            <div class="grid">
                <div class="stat-box">
                    <h3 id="commands-count">0</h3>
                    <p>Commands Processed</p>
                </div>
                <div class="stat-box">
                    <h3 id="skills-count">4</h3>
                    <p>Skills Loaded</p>
                </div>
                <div class="stat-box">
                    <h3 id="uptime">0m</h3>
                    <p>Uptime</p>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Command Input</h2>
            <div class="command-input">
                <input type="text" id="commandInput" placeholder="Enter a command or ask Envy something..." />
                <button onclick="sendCommand()">Send</button>
            </div>
            <div id="response" class="response-box" style="display:none;">
                <strong>Response:</strong>
                <p id="responseText"></p>
            </div>
        </div>
        
        <div class="card">
            <h2>Recent Activity</h2>
            <div class="log-container" id="logContainer">
                <div class="log-entry">System initialized</div>
                <div class="log-entry">Wake listener started</div>
                <div class="log-entry">All services ready</div>
            </div>
        </div>
    </div>
    
    <script>
        let commandCount = 0;
        const startTime = Date.now();
        
        // Update uptime
        setInterval(() => {
            const minutes = Math.floor((Date.now() - startTime) / 60000);
            document.getElementById('uptime').textContent = minutes + 'm';
        }, 60000);
        
        // Send command function
        async function sendCommand() {
            const input = document.getElementById('commandInput');
            const command = input.value.trim();
            
            if (!command) return;
            
            // Add to log
            addLog('User: ' + command);
            
            // Clear input
            input.value = '';
            
            try {
                const response = await fetch('/api/command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ command: command })
                });
                
                const result = await response.json();
                
                // Show response
                document.getElementById('responseText').textContent = result.response || 'Command processed';
                document.getElementById('response').style.display = 'block';
                
                // Add to log
                addLog('Envy: ' + (result.response || 'Done'));
                
                // Update command count
                commandCount++;
                document.getElementById('commands-count').textContent = commandCount;
            } catch (error) {
                console.error('Error:', error);
                addLog('Error: Failed to process command');
            }
        }
        
        // Add log entry
        function addLog(text) {
            const container = document.getElementById('logContainer');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.textContent = new Date().toLocaleTimeString() + ' - ' + text;
            container.appendChild(entry);
            container.scrollTop = container.scrollHeight;
        }
        
        // Allow Enter key to send command
        document.getElementById('commandInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendCommand();
            }
        });
        
        // Load initial stats
        fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                if (data.skills_count) {
                    document.getElementById('skills-count').textContent = data.skills_count;
                }
            })
            .catch(console.error);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/command")
async def process_command(request: CommandRequest):
    """Process a text command"""
    if not assistant_instance:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    try:
        result = assistant_instance.process_text_command(request.command)
        return result
    except Exception as e:
        logger.error(f"Error processing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    if not assistant_instance:
        return {"status": "not_initialized"}
    
    skills_count = len(assistant_instance.skill_manager.list_skills()) if assistant_instance.skill_manager else 0
    
    return {
        "status": "active" if assistant_instance.running else "inactive",
        "skills_count": skills_count,
        "version": "1.0.0"
    }


@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    if not assistant_instance:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    return assistant_instance.config


@app.post("/api/confirmation")
async def handle_confirmation(request: ConfirmationRequest):
    """Handle action confirmation"""
    if not assistant_instance or not assistant_instance.skill_manager:
        raise HTTPException(status_code=503, detail="Assistant not initialized")
    
    try:
        if request.action == 'confirm':
            result = assistant_instance.skill_manager.confirm_action(request.confirmation_id)
        else:
            result = assistant_instance.skill_manager.cancel_action(request.confirmation_id)
        
        return result
    except Exception as e:
        logger.error(f"Error handling confirmation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def set_assistant_instance(instance):
    """Set the global assistant instance"""
    global assistant_instance
    assistant_instance = instance


def run_dashboard(assistant, host="127.0.0.1", port=8080):
    """Run the dashboard server"""
    import uvicorn
    
    set_assistant_instance(assistant)
    
    logger.info(f"Starting web dashboard on http://{host}:{port}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    # Standalone mode for testing
    logging.basicConfig(level=logging.INFO)
    
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
