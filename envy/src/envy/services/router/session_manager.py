from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from ..common.config import EnvyConfig, PROJECT_ROOT
from ..common.logging import get_logger


@dataclass
class Session:
    session_id: str
    audio_path: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "created"
    transcript: str = ""
    partials: list[str] = field(default_factory=list)
    intent: Optional[str] = None
    skill: Optional[str] = None
    skill_result: Dict = field(default_factory=dict)
    response_text: str = ""
    tts_path: Optional[str] = None
    events: list[Dict] = field(default_factory=list)


class SessionManager:
    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self.logger = get_logger("SessionManager", config=config)
        self.sessions: Dict[str, Session] = {}
        sessions_dir = Path(config.get("runtime.sessions_dir", "artifacts/sessions"))
        self.sessions_dir = (PROJECT_ROOT / sessions_dir).resolve()
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create(self, session_id: str, audio_path: str) -> Session:
        session = Session(session_id=session_id, audio_path=audio_path)
        self.sessions[session_id] = session
        self.logger.info(f"Session {session_id} created for {audio_path}")
        self._write_session_file(session)
        return session

    def update_transcript(self, session_id: str, transcript: str, partials: list[str]) -> None:
        session = self._get(session_id)
        session.transcript = transcript
        session.partials = partials
        session.status = "transcribed"
        session.events.append({"type": "stt", "transcript": transcript, "partials": partials})
        self._write_session_file(session)

    def set_intent(self, session_id: str, intent: str, skill: Optional[str], confidence: float, parameters: Dict) -> None:
        session = self._get(session_id)
        session.intent = intent
        session.skill = skill
        session.events.append(
            {"type": "intent", "intent": intent, "skill": skill, "confidence": confidence, "parameters": parameters}
        )
        self._write_session_file(session)

    def set_skill_result(self, session_id: str, result: Dict) -> None:
        session = self._get(session_id)
        session.skill_result = result
        session.events.append({"type": "skill_result", "result": result})
        self._write_session_file(session)

    def set_response(self, session_id: str, text: str, tts_path: Optional[str]) -> None:
        session = self._get(session_id)
        session.response_text = text
        session.tts_path = tts_path
        session.status = "completed"
        session.events.append({"type": "response", "text": text, "tts_path": tts_path})
        self._write_session_file(session)

    def _get(self, session_id: str) -> Session:
        if session_id not in self.sessions:
            raise KeyError(f"Unknown session {session_id}")
        return self.sessions[session_id]

    def _write_session_file(self, session: Session) -> None:
        session_dir = self.sessions_dir / session.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        path = session_dir / "session.json"
        path.write_text(json.dumps(asdict(session), indent=2), encoding="utf-8")


__all__ = ["SessionManager", "Session"]
