from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from ..config import load_config
from ..logger import get_logger


logger = get_logger("web_dashboard")


def _read_state_file(path: Path) -> Dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Dashboard state file corrupt, resetting.")
    return {"pending_actions": []}


def create_app(config_path: Optional[Path] = None) -> FastAPI:
    config = load_config(config_path)
    runtime = config.get("runtime", {})
    artifacts_dir = Path(runtime.get("artifacts_dir", "artifacts"))
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    dashboard_state = artifacts_dir / "dashboard_state.json"

    app = FastAPI(title="Envy Dashboard", version="0.1.0")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return """
        <html>
          <head>
            <title>Envy Dashboard</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 2rem; background: #0b0e11; color: #fafafa; }
              h1 { color: #8be9fd; }
              button { padding: 0.8rem 1.6rem; margin-right: 1rem; background: #50fa7b; border: none; cursor: pointer; }
              pre { background: #1d232b; padding: 1rem; border-radius: 0.5rem; }
            </style>
          </head>
          <body>
            <h1>Envy Control Panel</h1>
            <p>Monitor, confirm, or cancel pending actions.</p>
            <div id="actions"></div>
            <script>
              async function loadActions() {
                const resp = await fetch('/api/pending');
                const data = await resp.json();
                const container = document.getElementById('actions');
                container.innerHTML = '';
                if (!data.pending || data.pending.length === 0) {
                  container.innerHTML = '<p>No pending confirmations.</p>';
                  return;
                }
                data.pending.forEach(item => {
                  const div = document.createElement('div');
                  div.innerHTML = `
                    <pre>${JSON.stringify(item, null, 2)}</pre>
                    <button onclick="confirmAction('${item.id}', true)">Confirm</button>
                    <button onclick="confirmAction('${item.id}', false)">Reject</button>
                  `;
                  container.appendChild(div);
                });
              }
              async function confirmAction(id, approve) {
                await fetch('/api/confirm', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/json'},
                  body: JSON.stringify({id, approve})
                });
                loadActions();
              }
              loadActions();
              setInterval(loadActions, 5000);
            </script>
          </body>
        </html>
        """

    @app.get("/api/pending")
    async def pending():
        state = _read_state_file(dashboard_state)
        return {"pending": state.get("pending_actions", [])}

    @app.post("/api/confirm")
    async def confirm(payload: Dict[str, bool]):
        action_id = payload.get("id")
        approve = payload.get("approve", False)
        if not action_id:
            raise HTTPException(400, "Missing id.")
        state = _read_state_file(dashboard_state)
        new_actions = []
        matched = False
        for item in state.get("pending_actions", []):
            if item["id"] == action_id:
                matched = True
                item["dashboard_confirmed"] = approve
                item["status"] = "approved" if approve else "rejected"
                logger.info("Dashboard %s action %s", "approved" if approve else "rejected", action_id)
            else:
                new_actions.append(item)
        if not matched:
            raise HTTPException(404, "Action not found.")
        state["pending_actions"] = new_actions
        dashboard_state.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return {"status": "ok", "approved": approve}

    return app
