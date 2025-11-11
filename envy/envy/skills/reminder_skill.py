from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from .base import Skill, SkillContext, SkillResult

LOGGER = logging.getLogger(__name__)


class ReminderSkill(Skill):
    name = "reminder"
    description = "Schedule lightweight reminders persisted to disk."

    def can_handle(self, command: str) -> bool:
        return "remind" in command.lower()

    def execute(self, command: str, context: SkillContext) -> SkillResult:
        LOGGER.info("ReminderSkill handling command: %s", command)
        reminder_dir = context.artifacts_dir / "reminders"
        reminder_dir.mkdir(parents=True, exist_ok=True)
        reminder_path = reminder_dir / "reminders.json"

        reminder = {
            "created": datetime.utcnow().isoformat() + "Z",
            "command": command.strip(),
            "due": (datetime.utcnow() + timedelta(minutes=5)).isoformat() + "Z",
        }

        reminders = []
        if reminder_path.exists():
            with reminder_path.open("r", encoding="utf-8") as handle:
                try:
                    reminders = json.load(handle)
                except json.JSONDecodeError:
                    reminders = []

        reminders.append(reminder)
        with reminder_path.open("w", encoding="utf-8") as handle:
            json.dump(reminders, handle, indent=2)

        LOGGER.info("Reminder stored at %s", reminder_path)

        return SkillResult(
            handled=True,
            response="Reminder scheduled and logged.",
            artifacts=[reminder_path],
        )
