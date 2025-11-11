"""
ReminderSkill: store reminders in persistent storage.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from .base import BaseSkill, SkillContext, SkillResult


class ReminderSkill(BaseSkill):
    name = "reminder"
    description = "Schedule simple reminders."
    destructive = False

    def matches(self, transcript: str) -> bool:
        lowered = transcript.lower()
        return "remind" in lowered or "reminder" in lowered

    async def execute(self, context: SkillContext) -> SkillResult:
        reminder_text, due = self._parse_reminder(context.transcript)
        if not reminder_text:
            return SkillResult(success=False, message="Could not parse reminder request.")

        reminders_file = context.data_dir / "reminders.json"
        reminders_file.parent.mkdir(parents=True, exist_ok=True)

        reminders = await asyncio.to_thread(self._load_reminders, reminders_file)
        reminders.append({"text": reminder_text, "due": due.isoformat() if due else None})
        await asyncio.to_thread(self._save_reminders, reminders_file, reminders)

        return SkillResult(
            success=True,
            message=f"Reminder captured: '{reminder_text}' for {due.isoformat() if due else 'anytime'}",
            artifact_path=reminders_file,
            metadata={"reminders": reminders},
        )

    def _parse_reminder(self, transcript: str):
        lowered = transcript.lower()
        match = re.search(r"remind me (?:to|that)?\s*(?P<text>.*)", lowered)
        text = match.group("text").strip() if match else transcript.strip()

        time_match = re.search(r"in (\d+) (minutes?|hours?)", lowered)
        due: datetime | None = None
        if time_match:
            quantity = int(time_match.group(1))
            unit = time_match.group(2)
            if unit.startswith("hour"):
                due = datetime.utcnow() + timedelta(hours=quantity)
            else:
                due = datetime.utcnow() + timedelta(minutes=quantity)

        return text, due

    def _load_reminders(self, path: Path) -> List[dict]:
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _save_reminders(self, path: Path, reminders: List[dict]) -> None:
        path.write_text(json.dumps(reminders, indent=2), encoding="utf-8")
