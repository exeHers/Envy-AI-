from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import json
import uuid

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ...core.events import EventBus

logger = logging.getLogger("envy.router")


@dataclass
class RouterConfig:
    persona: str = "neutral-sardonic"
    stt_url: str = "http://127.0.0.1:7002"
    skill_url: str = "http://127.0.0.1:7004"
    tts_url: str = "http://127.0.0.1:7003"
    llm_url: str = "http://127.0.0.1:7005"
    artifacts_dir: Path = Path("/workspace/envy/artifacts")
    command_whitelist: tuple[str, ...] = ("ls", "pwd", "cat")


class RouterService:
    def __init__(self, config: RouterConfig, event_bus: Optional[EventBus] = None):
        self.config = config
        self.event_bus = event_bus or EventBus()
        self.config.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._pending_path = self.config.artifacts_dir / "pending_actions.json"
        self._pending_path.parent.mkdir(parents=True, exist_ok=True)
        self.pending_actions: Dict[str, Dict[str, object]] = self._load_pending()

    async def handle_wake_audio(self, audio_path: str) -> Dict[str, object]:
        logger.info("Handling wake audio from %s", audio_path)
        transcript = await self._transcribe(audio_path)
        intent = self._infer_intent(transcript)
        await self.event_bus.publish("transcript", {"text": transcript, "intent": intent})
        skill_result = await self._execute_skill(intent, transcript, confirmed=False)
        speech = skill_result.get("speech", "Task completed.")
        tts_file = await self._speak(speech)
        response = {
            "transcript": transcript,
            "intent": intent,
            "skill_result": skill_result,
            "tts_file": tts_file,
        }
        if skill_result.get("requires_confirmation"):
            action_id = self._store_pending_action(intent, transcript, skill_result)
            response["pending_action_id"] = action_id
        await self.event_bus.publish("response", response)
        return response

    async def _transcribe(self, audio_path: str) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(audio_path, "rb") as f:
                files = {"file": ("audio.wav", f, "audio/wav")}
                resp = await client.post(f"{self.config.stt_url}/transcribe", files=files)
                resp.raise_for_status()
                data = resp.json()
                transcript = data.get("text", "")
                if not transcript:
                    raise RuntimeError("Transcript empty")
                logger.info("Transcript: %s", transcript)
                return transcript

    def _infer_intent(self, transcript: str) -> str:
        lower = transcript.lower()
        if "create" in lower and ".py" in lower:
            return "code"
        if "research" in lower or "look into" in lower:
            return "research"
        if "remind me" in lower:
            return "reminder"
        if any(word in lower for word in ["run", "execute"]):
            return "syscontrol"
        return "llm"

    async def _execute_skill(self, intent: str, transcript: str, confirmed: bool) -> Dict[str, object]:
        if intent == "llm":
            completion = await self._ask_llm(transcript)
            return {"success": True, "speech": completion, "data": {"provider": "llm"}}

        payload = {
            "skill_name": intent,
            "transcript": transcript,
            "context": {
                "artifacts_dir": str(self.config.artifacts_dir),
                "command_whitelist": list(self.config.command_whitelist),
                "confirmed": confirmed,
            },
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.config.skill_url}/execute", json=payload)
            if resp.status_code == 404:
                logger.warning("Skill %s not found; falling back to LLM.", intent)
                return await self._execute_skill("llm", transcript, confirmed)
            resp.raise_for_status()
            data = resp.json()
            if data.get("requires_confirmation"):
                logger.info("Skill %s requires confirmation, deferring execution.", intent)
            return data

    async def _ask_llm(self, transcript: str) -> str:
        payload = {"prompt": transcript, "persona": self.config.persona}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.config.llm_url}/complete", json=payload)
            resp.raise_for_status()
            data = resp.json()
            logger.info("LLM provider %s responded.", data.get("provider"))
            return data.get("text", "I processed your request.")

    async def _speak(self, text: str) -> str:
        payload = {"text": text}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self.config.tts_url}/synthesize", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("file_path", "")

    def _store_pending_action(self, intent: str, transcript: str, skill_result: Dict[str, object]) -> str:
        action_id = uuid.uuid4().hex
        pending = {
            "id": action_id,
            "intent": intent,
            "transcript": transcript,
            "skill_result": skill_result,
            "voice_confirmed": False,
            "dashboard_confirmed": False,
            "status": "awaiting_voice",
        }
        self.pending_actions[action_id] = pending
        self._save_pending()
        logger.info("Pending action %s created for intent %s", action_id, intent)
        return action_id

    def _load_pending(self) -> Dict[str, Dict[str, object]]:
        if not self._pending_path.exists():
            return {}
        try:
            data = json.loads(self._pending_path.read_text(encoding="utf-8"))
            return {item["id"]: item for item in data}
        except Exception as exc:  # pragma: no cover - guard
            logger.error("Failed to load pending actions: %s", exc)
            return {}

    def _save_pending(self) -> None:
        data = list(self.pending_actions.values())
        self._pending_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    async def voice_confirm(self, action_id: str) -> Dict[str, object]:
        action = self.pending_actions.get(action_id)
        if not action:
            raise KeyError("Action not found")
        action["voice_confirmed"] = True
        action["status"] = "awaiting_dashboard"
        self._save_pending()
        logger.info("Action %s voice-confirmed", action_id)
        return action

    async def dashboard_confirm(self, action_id: str) -> Dict[str, object]:
        action = self.pending_actions.get(action_id)
        if not action:
            raise KeyError("Action not found")
        if not action.get("voice_confirmed"):
            raise PermissionError("Voice confirmation required first")
        if action.get("dashboard_confirmed"):
            return action
        result = await self._execute_skill(action["intent"], action["transcript"], confirmed=True)
        action["dashboard_confirmed"] = True
        action["status"] = "completed"
        action["final_result"] = result
        self._save_pending()
        logger.info("Action %s executed after dashboard confirmation", action_id)
        return action


class WakeRequest(BaseModel):
    audio_path: str


class RouterResponse(BaseModel):
    transcript: str
    intent: str
    skill_result: Dict[str, object]
    tts_file: str
    pending_action_id: Optional[str] = None


class ConfirmRequest(BaseModel):
    action_id: str


def create_app(router_service: RouterService) -> FastAPI:
    app = FastAPI(title="Envy Router")

    @app.post("/process", response_model=RouterResponse)
    async def process(request: WakeRequest):
        path = Path(request.audio_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found.")
        result = await router_service.handle_wake_audio(str(path))
        return RouterResponse(**result)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/pending-actions")
    async def pending_actions():
        return list(router_service.pending_actions.values())

    @app.post("/confirm/voice")
    async def confirm_voice(request: ConfirmRequest):
        try:
            action = await router_service.voice_confirm(request.action_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return action

    @app.post("/confirm/dashboard")
    async def confirm_dashboard(request: ConfirmRequest):
        try:
            action = await router_service.dashboard_confirm(request.action_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return action

    return app
