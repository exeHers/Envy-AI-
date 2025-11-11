"""ReminderSkill: stores lightweight reminders locally."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .base import Skill, SkillContext, SkillResult


class ReminderSkill(Skill):
    name = "ReminderSkill"
    description = "Capture reminders and persist them locally."
    requires_confirmation = False

    def execute(self, text: str, session_id: str, context: SkillContext) -> SkillResult:
        reminder_text = self._extract_reminder(text)
        if not reminder_text:
            return SkillResult(
                status="failed",
                message="Could not parse reminder content.",
            )

        reminder = {
            "session_id": session_id,
            "text": reminder_text,
            "timestamp": self.timestamp(),
        }
        reminder_path = context.artifacts_path / "reminders.yaml"
        reminders = self._load_reminders(reminder_path)
        reminders.append(reminder)
        reminder_path.parent.mkdir(parents=True, exist_ok=True)
        reminder_path.write_text(yaml.safe_dump(reminders), encoding="utf-8")

        message = f"Reminder recorded: {reminder_text}"
        return SkillResult(
            status="ok",
            message=message,
            artifacts={"reminder_file": str(reminder_path)},
        )

    def _extract_reminder(self, text: str) -> str | None:
        match = re.search(r"remind(?:er)?(?: me)? to (.*)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _load_reminders(self, path: Path):
        if path.exists():
            try:
                return yaml.safe_load(path.read_text(encoding="utf-8")) or []
            except Exception:
                return []
        return []


__all__ = ["ReminderSkill"]

