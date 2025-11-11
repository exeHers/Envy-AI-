from __future__ import annotations

import json
import time
from pathlib import Path

from .base import SkillBase


class ReminderSkill(SkillBase):
    name = "reminderskill"
    description = "Schedules simple voice reminders stored locally."
    requires_confirmation = False
    is_envy_skill = True

    def handle(self, context):
        storage = Path(context.config["skills"]["reminder"]["storage_path"])
        storage.parent.mkdir(parents=True, exist_ok=True)
        reminder_text = context.metadata.get("reminder") or context.transcript
        reminders = []
        if storage.exists():
            reminders = json.loads(storage.read_text(encoding="utf-8"))
        entry = {"timestamp": time.time(), "text": reminder_text}
        reminders.append(entry)
        storage.write_text(json.dumps(reminders, indent=2), encoding="utf-8")
        return f"Reminder stored: {reminder_text}"
