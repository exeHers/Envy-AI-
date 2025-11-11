"""Central router coordinating Envy services."""

from __future__ import annotations

import argparse
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from ..config import EnvyConfig, load_config
from ..logging_config import configure_logging
from ..core.intent_classifier import IntentClassifier
from ..core.llm_adapter import LLMAdapter

LOGGER = logging.getLogger("envy.router")


class AudioCommandRequest(BaseModel):
    audio_path: str
    session_id: Optional[str] = None
    stream: bool = True


class TextCommandRequest(BaseModel):
    text: str
    session_id: Optional[str] = None


class WakeNotification(BaseModel):
    session_id: Optional[str] = None
    transcript: str
    confidence: float


class RouterService:
    def __init__(self, config: EnvyConfig, client: Optional[httpx.AsyncClient] = None):
        self.config = config
        self.classifier = IntentClassifier()
        self.llm = LLMAdapter(config)
        self.session_states: Dict[str, Dict[str, Any]] = {}
        self._client = client or httpx.AsyncClient(timeout=30)
        services = config.services
        self.stt_url = services["stt"].url() + "/stt/transcribe"
        self.skill_url = services["skill_manager"].url() + "/skills/execute"
        self.tts_url = services["tts"].url() + "/tts/speak"

    async def ensure_session(self, session_id: Optional[str]) -> str:
        if session_id and session_id in self.session_states:
            return session_id
        new_session = session_id or str(uuid.uuid4())
        self.session_states.setdefault(new_session, {"history": []})
        return new_session

    async def process_audio(self, payload: AudioCommandRequest) -> Dict[str, Any]:
        session_id = await self.ensure_session(payload.session_id)
        LOGGER.info("Processing audio for session %s", session_id)
        audio_path = Path(payload.audio_path)
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail=f"Audio path not found: {audio_path}")

        stt_response = await self._client.post(
            self.stt_url, json={"audio_path": str(audio_path), "session_id": session_id, "stream": payload.stream}
        )
        stt_response.raise_for_status()
        stt_data = stt_response.json()
        transcript = stt_data.get("text", "")
        if not transcript:
            transcript = " "
        text_result = await self.process_text(TextCommandRequest(text=transcript, session_id=session_id))
        text_result["stt_source"] = stt_data.get("source")
        text_result["stt_partials"] = stt_data.get("partials", [])
        text_result["session_id"] = session_id
        return text_result

    async def process_text(self, payload: TextCommandRequest) -> Dict[str, Any]:
        session_id = await self.ensure_session(payload.session_id)
        text = payload.text.strip()
        if text.lower().startswith("envy"):
            text = text[4:].strip(",. ")
        intent = self.classifier.classify(text)
        if not intent:
            intent = self.classifier.classify("fallback")
        LOGGER.info("Session %s intent %s (%.2f)", session_id, intent.name, intent.confidence)

        skill_result: Optional[Dict[str, Any]] = None
        if intent.name.endswith("Skill"):
            skill_result = await self.invoke_skill(intent.name, text, session_id)
            if skill_result and skill_result.get("requires_confirmation"):
                pending = {
                    "confirmation_id": skill_result.get("confirmation_id"),
                    "skill": intent.name,
                    "text": text,
                    "status": "pending",
                }
                self.session_states[session_id].setdefault("pending_confirmations", []).append(pending)

        llm_prompt = self._build_prompt(intent.name, text, skill_result)
        llm_reply = self.llm.generate(llm_prompt)

        tts_payload = {"text": llm_reply, "session_id": session_id}
        try:
            tts_response = await self._client.post(self.tts_url, json=tts_payload)
            tts_response.raise_for_status()
            tts_data = tts_response.json()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("TTS service error: %s", exc)
            tts_data = {"status": "error", "detail": str(exc)}

        result = {
            "session_id": session_id,
            "intent": intent.name,
            "intent_confidence": intent.confidence,
            "command_text": text,
            "skill_result": skill_result,
            "llm_reply": llm_reply,
            "tts": tts_data,
        }
        self.session_states[session_id]["history"].append(result)
        return result

    async def invoke_skill(self, skill_name: str, text: str, session_id: str) -> Dict[str, Any]:
        payload = {"skill": skill_name, "text": text, "session_id": session_id}
        response = await self._client.post(self.skill_url, json=payload)
        response.raise_for_status()
        data = response.json()
        LOGGER.info("Skill %s executed with status %s", skill_name, data.get("status"))
        return data

    def _build_prompt(self, intent_name: str, text: str, skill_result: Optional[Dict[str, Any]]) -> str:
        base = (
            "You are Envy, a concise, slightly sardonic personal assistant. Respond briefly but helpfully.\n"
            f"User request intent: {intent_name}\n"
            f"Raw command text: {text}\n"
        )
        if skill_result:
            base += f"Skill output: {skill_result.get('message', '')}\n"
        else:
            base += "Skill output: none\n"
        base += "Compose the spoken response."
        return base

    async def handle_wake(self, payload: WakeNotification) -> Dict[str, Any]:
        session_id = await self.ensure_session(payload.session_id)
        self.session_states[session_id]["wake_detected"] = payload.confidence
        self.session_states[session_id]["wake_transcript"] = payload.transcript
        LOGGER.info("Wake event logged for session %s (confidence %.2f)", session_id, payload.confidence)
        return {"session_id": session_id, "status": "wake_logged"}

    async def confirm_action(self, confirmation_id: str, approved: bool, approver: str) -> Dict[str, Any]:
        for session_id, session in self.session_states.items():
            pending_list = session.get("pending_confirmations", [])
            for entry in pending_list:
                if entry.get("confirmation_id") == confirmation_id:
                    entry["status"] = "approved" if approved else "rejected"
                    entry["approver"] = approver
                    message = "Action approved" if approved else "Action rejected"
                    LOGGER.info("Confirmation %s %s by %s", confirmation_id, message, approver)
                    return {"session_id": session_id, "confirmation_id": confirmation_id, "status": entry["status"]}
        raise HTTPException(status_code=404, detail="Confirmation ID not found")


def create_app(config: EnvyConfig) -> FastAPI:
    router_service = RouterService(config)
    app = FastAPI(title="Envy Router Service", version="0.1.0")

    @app.post("/session/from-audio")
    async def session_from_audio(request: AudioCommandRequest):
        try:
            return await router_service.process_audio(request)
        except HTTPException:
            raise
        except httpx.HTTPError as exc:
            LOGGER.error("HTTP error while processing audio: %s", exc)
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post("/session/from-text")
    async def session_from_text(request: TextCommandRequest):
        try:
            return await router_service.process_text(request)
        except httpx.HTTPError as exc:
            LOGGER.error("HTTP error while processing text: %s", exc)
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.post("/wake")
    async def wake_event(notification: WakeNotification):
        return await router_service.handle_wake(notification)

    @app.get("/sessions/{session_id}")
    async def get_session(session_id: str):
        if session_id not in router_service.session_states:
            raise HTTPException(status_code=404, detail="Session not found")
        return router_service.session_states[session_id]

    @app.get("/sessions")
    async def list_sessions():
        sessions = []
        for session_id, state in router_service.session_states.items():
            history = state.get("history", [])
            sessions.append(
                {
                    "session_id": session_id,
                    "history": history,
                    "wake_confidence": state.get("wake_detected"),
                    "last_intent": history[-1]["intent"] if history else None,
                    "pending_confirmations": state.get("pending_confirmations", []),
                }
            )
        return sessions

    class ConfirmRequest(BaseModel):
        confirmation_id: str
        approved: bool = True
        approver: str = "dashboard"

    @app.post("/confirm")
    async def confirm(request: ConfirmRequest):
        return await router_service.confirm_action(request.confirmation_id, request.approved, request.approver)

    @app.get("/pending-confirmations")
    async def pending_confirmations():
        items = []
        for session_id, state in router_service.session_states.items():
            for entry in state.get("pending_confirmations", []):
                item = dict(entry)
                item["session_id"] = session_id
                items.append(item)
        return items

    @app.get("/health")
    async def health():
        return {"status": "ok", "sessions": len(router_service.session_states)}

    return app


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Envy router service.")
    parser.add_argument("--config", type=str, default=str(CONFIG_PATH := Path(__file__).resolve().parents[2] / "config" / "envy.yaml"))
    parser.add_argument("--host", type=str, help="Override host binding")
    parser.add_argument("--port", type=int, help="Override port binding")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    service_conf = config.services["router"]
    host = args.host or service_conf.host
    port = args.port or service_conf.port

    configure_logging(config, "router_service")
    app = create_app(config)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    main()

