from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from envy.bus import Event, EventBus
from envy.config import Config
from envy.services.base import ServiceBase

LOGGER = logging.getLogger("dashboard_service")


DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Envy Dashboard</title>
    <style>
      body { font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; }
      header { padding: 1rem 2rem; background: #111c33; display: flex; justify-content: space-between; align-items: center; }
      main { padding: 1.5rem 2rem; display: grid; gap: 1.5rem; grid-template-columns: 2fr 1fr; }
      section { background: rgba(15, 23, 42, 0.8); padding: 1rem; border-radius: 0.75rem; border: 1px solid rgba(148, 163, 184, 0.2); }
      h1, h2 { margin: 0 0 0.75rem 0; }
      .event-list { max-height: 300px; overflow-y: auto; font-size: 0.9rem; }
      .event-item { margin-bottom: 0.5rem; border-bottom: 1px solid rgba(148, 163, 184, 0.1); padding-bottom: 0.5rem; }
      .pending { background: rgba(234, 179, 8, 0.12); padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 1rem; }
      button { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border-radius: 999px; border: none; cursor: pointer; font-weight: 600; }
      .approve { background: #22c55e; color: #022c22; }
      .reject { background: #ef4444; color: #2b0b0b; margin-left: 0.5rem; }
      .badge { font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 999px; background: rgba(125, 211, 252, 0.25); color: #38bdf8; }
      small { color: #94a3b8; }
    </style>
  </head>
  <body>
    <header>
      <h1>Envy Control Deck</h1>
      <div>
        <span id="profile-badge" class="badge">Profile: balanced</span>
      </div>
    </header>
    <main>
      <section>
        <h2>Event Stream</h2>
        <div id="events" class="event-list"></div>
      </section>
      <section>
        <h2>Pending Confirmations</h2>
        <div id="confirmations"></div>
      </section>
    </main>
    <script>
      async function refreshStatus() {
        const response = await fetch('/api/status');
        const data = await response.json();
        document.getElementById('profile-badge').textContent = 'Profile: ' + data.profile;
        renderConfirmations(data.pending_confirmations);
      }

      function renderConfirmations(confirmations) {
        const container = document.getElementById('confirmations');
        container.innerHTML = '';
        confirmations.forEach(item => {
          const element = document.createElement('div');
          element.className = 'pending';
          element.innerHTML = `
            <div><strong>${item.skill}</strong></div>
            <div>${item.message}</div>
            <div><small>Voice confirmed: ${item.voice_confirmed ? 'yes' : 'awaiting'}</small></div>
            <div style="margin-top:0.5rem;">
              <button class="approve" onclick="approve('${item.confirmation_id}')">Approve</button>
              <button class="reject" onclick="reject('${item.confirmation_id}')">Reject</button>
            </div>
          `;
          container.appendChild(element);
        });
        if (!confirmations.length) {
          container.innerHTML = '<small>No pending actions.</small>';
        }
      }

      async function approve(id) {
        await fetch('/api/confirmations/' + id + '/approve', {method: 'POST'});
        refreshStatus();
      }
      async function reject(id) {
        await fetch('/api/confirmations/' + id + '/reject', {method: 'POST'});
        refreshStatus();
      }

      const eventsContainer = document.getElementById('events');
      const eventSource = new EventSource('/api/events/stream');
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const div = document.createElement('div');
        div.className = 'event-item';
        div.innerHTML = `<div><strong>${data.type}</strong> — ${data.message}</div><small>${data.timestamp}</small>`;
        eventsContainer.prepend(div);
        const items = eventsContainer.querySelectorAll('.event-item');
        if (items.length > 50) {
          items[items.length - 1].remove();
        }
      };

      refreshStatus();
      setInterval(refreshStatus, 5000);
    </script>
  </body>
</html>
"""


class DashboardService(ServiceBase):
    name = "dashboard_service"

    def __init__(self, config: Config, bus: EventBus):
        super().__init__(config, bus)
        self.app = FastAPI(title="Envy Dashboard")
        self._events: List[Dict[str, Any]] = []
        self._listeners: List[asyncio.Queue[Dict[str, Any]]] = []
        self._pending_confirmations: Dict[str, Dict[str, Any]] = {}
        self._voice_confirmed: Dict[str, bool] = {}
        self._setup_routes()

    async def run(self) -> None:
        host = self.config.get("web.host", "0.0.0.0")
        port = int(self.config.get("web.port", 8080))
        server = uvicorn.Server(uvicorn.Config(self.app, host=host, port=port, log_level="info", loop="asyncio"))
        listener_task = asyncio.create_task(self._consume_events())
        await server.serve()
        await listener_task

    async def _consume_events(self) -> None:
        while True:
            event = await self.bus.next_event()
            self._record_event(event)

    def _record_event(self, event: Event) -> None:
        message = event.payload.get("message") or json.dumps(event.payload)[:200]
        record = {
            "type": event.type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self._events.insert(0, record)
        self._events = self._events[:200]
        for listener in list(self._listeners):
            listener.put_nowait(record)

        if event.type == "security.confirmation_required":
            confirmation_id = event.payload["confirmation_id"]
            self._pending_confirmations[confirmation_id] = {
                "confirmation_id": confirmation_id,
                "skill": event.payload.get("skill"),
                "message": event.payload.get("message"),
                "voice_confirmed": False,
            }
        elif event.type == "security.voice_confirmed":
            confirmation_id = event.payload.get("confirmation_id")
            if confirmation_id and confirmation_id in self._pending_confirmations:
                self._pending_confirmations[confirmation_id]["voice_confirmed"] = True

        elif event.type == "skill.result":
            confirmation_id = event.payload.get("confirmation_id")
            if confirmation_id and confirmation_id in self._pending_confirmations:
                if event.payload.get("status") != "pending_confirmation":
                    self._pending_confirmations.pop(confirmation_id, None)

    def _setup_routes(self) -> None:
        @self.app.get("/", response_class=HTMLResponse)
        async def index() -> str:
            return DASHBOARD_TEMPLATE

        @self.app.get("/api/status")
        async def status() -> Dict[str, Any]:
            return {
                "profile": self.config.profile,
                "pending_confirmations": list(self._pending_confirmations.values()),
                "events": self._events[:20],
            }

        @self.app.get("/api/events/stream")
        async def events_stream() -> EventSourceResponse:
            queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
            self._listeners.append(queue)

            async def event_generator():
                try:
                    while True:
                        event = await queue.get()
                        yield {"data": json.dumps(event)}
                finally:
                    self._listeners.remove(queue)

            return EventSourceResponse(event_generator())

        @self.app.post("/api/confirmations/{confirmation_id}/approve")
        async def approve_confirmation(confirmation_id: str):
            entry = self._pending_confirmations.get(confirmation_id)
            if not entry:
                raise HTTPException(status_code=404, detail="Confirmation not found")
            if not entry.get("voice_confirmed"):
                raise HTTPException(status_code=400, detail="Voice confirmation required before approval.")
            await self.bus.publish(
                "security.confirmed",
                {"confirmation_id": confirmation_id, "source": "dashboard"},
            )
            self._pending_confirmations.pop(confirmation_id, None)
            return JSONResponse({"status": "approved"})

        @self.app.post("/api/confirmations/{confirmation_id}/reject")
        async def reject_confirmation(confirmation_id: str):
            if confirmation_id in self._pending_confirmations:
                self._pending_confirmations.pop(confirmation_id, None)
            await self.bus.publish(
                "skill.result",
                {
                    "skill": "unknown",
                    "status": "denied",
                    "message": "Action rejected from dashboard.",
                    "confirmation_id": confirmation_id,
                },
            )
            return JSONResponse({"status": "rejected"})
