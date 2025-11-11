from __future__ import annotations

import uuid
from typing import Optional

import typer
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from ..common.deps import get_config, verify_secret
from ..common.logging import get_logger
from ..common.messaging import ServiceClient
from ..common.security import SecurityManager
from .intent_classifier import IntentClassifier
from .llm_adapter import LLMAdapter
from .session_manager import SessionManager


class SessionStartRequest(BaseModel):
    audio_path: str
    session_id: Optional[str] = None
    source: str = "wake_listener"


class SessionResponse(BaseModel):
    session_id: str
    transcript: str
    partials: list[str]
    intent: str
    skill: Optional[str]
    response_text: str
    tts_path: Optional[str]
    llm_engine: str
    skill_result: dict
    requires_confirmation: bool = False
    confirmation_id: Optional[str] = None


class ConfirmationRequest(BaseModel):
    action_id: str
    channel: str


def create_app() -> FastAPI:
    config = get_config()
    logger = get_logger("RouterService", config=config)
    session_manager = SessionManager(config)
    classifier = IntentClassifier(config)
    llm = LLMAdapter(config)
    security = SecurityManager(config)
    stt_client = ServiceClient(config.get("messaging.stt_url"), config)
    tts_client = ServiceClient(config.get("messaging.tts_url"), config)
    skill_client = ServiceClient(config.get("messaging.skill_manager_url"), config)

    app = FastAPI(title="Envy Router Service", version="0.1.0")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "profile": config.profile}

    @app.post("/session/start", response_model=SessionResponse, dependencies=[Depends(verify_secret)])
    async def session_start(request: SessionStartRequest) -> SessionResponse:
        session_id = request.session_id or uuid.uuid4().hex
        session_manager.create(session_id, request.audio_path)
        logger.info(f"Session {session_id} started with audio {request.audio_path}")

        stt_result = stt_client.post_json(
            "/transcribe-file",
            {"path": request.audio_path, "session_id": session_id},
        )
        transcript = stt_result.get("text", "")
        partials = stt_result.get("partials", [])
        session_manager.update_transcript(session_id, transcript, partials)
        logger.info(f"Session {session_id} transcript: {transcript}")

        intent_result = classifier.classify(transcript)
        session_manager.set_intent(
            session_id,
            intent=intent_result.intent,
            skill=intent_result.skill,
            confidence=intent_result.confidence,
            parameters=intent_result.parameters,
        )

        skill_result = {}
        requires_confirmation = False
        confirmation_id: Optional[str] = None

        if intent_result.skill:
            skill_payload = {
                "session_id": session_id,
                "intent": intent_result.intent,
                "skill": intent_result.skill,
                "transcript": transcript,
                "parameters": intent_result.parameters,
            }
            skill_result = skill_client.post_json("/execute", skill_payload)
            session_manager.set_skill_result(session_id, skill_result)
            requires_confirmation = skill_result.get("requires_confirmation", False)
            logger.info(f"Skill {intent_result.skill} executed for session {session_id}: {skill_result}")

        if security.requires_confirmation(intent_result.intent, transcript):
            requires_confirmation = True

        response_text = ""
        if skill_result.get("success"):
            response_text = skill_result.get("message", "")
        else:
            llm_response = llm.respond(transcript, {"intent": intent_result.intent, "skill": intent_result.skill or ""})
            response_text = llm_response["text"]

        llm_engine = "rule-based"
        if not skill_result.get("success"):
            llm_data = llm.respond(transcript, {"intent": intent_result.intent})
            response_text = llm_data["text"]
            llm_engine = llm_data["engine"]
        else:
            llm_engine = "skill"

        if requires_confirmation:
            pending = security.create_pending(intent_result.intent, response_text)
            confirmation_id = pending.action_id
            response_text = (
                f"{response_text} I need confirmation before proceeding. "
                f"Please confirm with action id {pending.action_id}."
            )

        tts_result = tts_client.post_json(
            "/synthesize",
            {"text": response_text, "session_id": session_id},
        )
        tts_path = tts_result.get("path")
        session_manager.set_response(session_id, response_text, tts_path)

        return SessionResponse(
            session_id=session_id,
            transcript=transcript,
            partials=partials,
            intent=intent_result.intent,
            skill=intent_result.skill,
            response_text=response_text,
            tts_path=tts_path,
            llm_engine=llm_engine,
            skill_result=skill_result,
            requires_confirmation=requires_confirmation,
            confirmation_id=confirmation_id,
        )

    @app.post("/confirm", dependencies=[Depends(verify_secret)])
    async def confirm_action(request: ConfirmationRequest) -> dict:
        try:
            confirmed = security.confirm(request.action_id, request.channel)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except TimeoutError as exc:
            raise HTTPException(status_code=410, detail=str(exc))
        return {"action_id": request.action_id, "confirmed": confirmed}

    @app.get("/sessions/{session_id}", dependencies=[Depends(verify_secret)])
    async def get_session(session_id: str) -> dict:
        try:
            session = session_manager.sessions[session_id]
        except KeyError:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"session": session.__dict__}

    @app.get("/sessions", dependencies=[Depends(verify_secret)])
    async def list_sessions() -> dict:
        return {"sessions": [session.__dict__ for session in session_manager.sessions.values()]}

    return app


app = create_app()


def main(
    host: str = typer.Option("0.0.0.0", help="Host for the router service."),
    port: int = typer.Option(8203, help="Port for the router service."),
    reload: bool = typer.Option(False, help="Enable autoreload (development only)."),
) -> None:
    uvicorn.run("envy.services.router.main:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    typer.run(main)
