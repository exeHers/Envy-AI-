from __future__ import annotations

import json
import uuid
from datetime import datetime

from .base import BaseSkill, SkillRequest, SkillResponse
from ..services.common.config import EnvyConfig, PROJECT_ROOT
from ..services.common.logging import get_logger


class ReminderSkill(BaseSkill):
    name = "reminder_skill"
    intents = ("reminder.add", "reminder.list", "reminder.clear")

    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self.logger = get_logger("ReminderSkill", config=config)
        self.storage = (PROJECT_ROOT / "artifacts" / "reminders.json").resolve()
        self.storage.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage.exists():
            self.storage.write_text("[]", encoding="utf-8")

    def handle(self, request: SkillRequest) -> SkillResponse:
        if request.intent == "reminder.add":
            return self._add_reminder(request)
        if request.intent == "reminder.list":
            return self._list_reminders()
        if request.intent == "reminder.clear":
            return self._clear_reminders()
        return SkillResponse(success=False, message=f"Unsupported intent {request.intent}")

    def _add_reminder(self, request: SkillRequest) -> SkillResponse:
        reminder_text = request.parameters.get("text") or request.transcript
        reminder = {
            "id": str(uuid.uuid4()),
            "text": reminder_text,
            "created_at": datetime.utcnow().isoformat(),
        }
        reminders = self._read_reminders()
        reminders.append(reminder)
        self._write_reminders(reminders)
        self.logger.info(f"Added reminder: {reminder_text}")
        return SkillResponse(success=True, message="Reminder saved.", data=reminder)

    def _list_reminders(self) -> SkillResponse:
        reminders = self._read_reminders()
        if not reminders:
            return SkillResponse(success=True, message="No reminders set.", data={"reminders": []})
        return SkillResponse(success=True, message="Active reminders listed.", data={"reminders": reminders})

    def _clear_reminders(self) -> SkillResponse:
        self._write_reminders([])
        self.logger.info("Cleared all reminders.")
        return SkillResponse(success=True, message="All reminders cleared.", data={"reminders": []})

    def _read_reminders(self) -> list[dict]:
        try:
            data = json.loads(self.storage.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            self.logger.warning("Corrupted reminders storage; resetting.")
        return []

    def _write_reminders(self, reminders: list[dict]) -> None:
        self.storage.write_text(json.dumps(reminders, indent=2), encoding="utf-8")


__all__ = ["ReminderSkill"]
