"""
FastAPI dashboard exposing controls and status for Envy.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from ..config import EnvyConfig

_LOGGER = logging.getLogger(__name__)


@dataclass
class DashboardState:
    config: EnvyConfig
    pending_confirmations: Dict[str, Dict[str, Any]] = field(default_factory=dict)


def create_app(state: DashboardState, on_confirm: Optional[Callable[[str], None]] = None) -> FastAPI:
    app = FastAPI(title="Envy Dashboard")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return _INDEX_HTML

    @app.get("/api/status")
    async def status() -> Dict[str, Any]:
        return {
            "profile": state.config.profile.name,
            "wake_model": state.config.audio.wake_model_path,
            "stt_model": state.config.audio.stt_model_path,
            "llm_backend": state.config.llm.default_backend,
            "pending_confirmations": list(state.pending_confirmations.keys()),
        }

    @app.get("/api/config")
    async def get_config() -> Dict[str, Any]:
        return {
            "profile": state.config.profile.name,
            "skills": state.config.skills.whitelist,
            "persona": state.config.llm.persona,
        }

    @app.post("/api/confirm")
    async def confirm_action(payload: Dict[str, Any]) -> Dict[str, Any]:
        skill = payload.get("skill")
        if not skill:
            raise HTTPException(status_code=400, detail="Missing skill.")
        state.pending_confirmations[skill] = {"confirmed": True}
        if on_confirm:
            on_confirm(skill)
        return {"status": "confirmed", "skill": skill}

    @app.get("/api/logs")
    async def logs(limit: int = 200) -> Dict[str, Any]:
        log_file = state.config.artifacts_dir / "logs" / "envy.log"
        if not log_file.exists():
            return {"lines": []}
        lines = log_file.read_text(encoding="utf-8").splitlines()[-limit:]
        return {"lines": lines}

    return app


_INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Envy Dashboard</title>
    <style>
      body { font-family: sans-serif; background: #0b0d10; color: #e4e7eb; margin: 0; padding: 0; }
      header { background: #151a1f; padding: 1.5rem; }
      h1 { margin: 0; font-size: 1.6rem; }
      main { padding: 1.5rem; }
      section { margin-bottom: 1.5rem; }
      button { background: #2f80ed; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 6px; cursor: pointer; }
      .card { background: #151a1f; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
      pre { background: rgba(255, 255, 255, 0.05); padding: 1rem; border-radius: 6px; overflow-x: auto; }
    </style>
  </head>
  <body>
    <header>
      <h1>Envy Control Room</h1>
    </header>
    <main>
      <section class="card">
        <h2>Status</h2>
        <pre id="status">Loading...</pre>
        <button onclick="refreshStatus()">Refresh</button>
      </section>
      <section class="card">
        <h2>Pending Confirmations</h2>
        <pre id="confirmations">Loading...</pre>
        <input id="confirm-skill" placeholder="Skill name" />
        <button onclick="confirmSkill()">Confirm</button>
      </section>
      <section class="card">
        <h2>Logs</h2>
        <pre id="logs">Loading...</pre>
        <button onclick="loadLogs()">Reload Logs</button>
      </section>
    </main>
    <script>
      async function refreshStatus() {
        const res = await fetch('/api/status');
        const data = await res.json();
        document.getElementById('status').innerText = JSON.stringify(data, null, 2);
        document.getElementById('confirmations').innerText = JSON.stringify(data.pending_confirmations || [], null, 2);
      }

      async function loadLogs() {
        const res = await fetch('/api/logs?limit=200');
        const data = await res.json();
        document.getElementById('logs').innerText = (data.lines || []).join('\\n');
      }

      async function confirmSkill() {
        const skill = document.getElementById('confirm-skill').value;
        if (!skill) return;
        await fetch('/api/confirm', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ skill })
        });
        refreshStatus();
      }

      refreshStatus();
      loadLogs();
      setInterval(() => { refreshStatus(); }, 5000);
    </script>
  </body>
</html>
"""
