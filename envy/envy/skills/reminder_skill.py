from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseSkill, SkillResult


class ReminderSkill(BaseSkill):
    name = "reminder"
    description = "Schedules lightweight reminders persisted locally."

    async def run(self, transcript: str, context: Dict[str, Any]) -> SkillResult:
        lower = transcript.lower()
        reminder_text = self._extract_text(lower)
        minutes = self._extract_minutes(lower)

        if not reminder_text:
            return SkillResult(False, "I could not determine the reminder message.", {})

        eta = datetime.utcnow() + timedelta(minutes=minutes)
        record = {
            "text": reminder_text,
            "due_at": eta.isoformat() + "Z",
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        await asyncio.to_thread(self._persist_reminder, record, context)
        speech = f"Reminder set for {minutes} minute{'s' if minutes != 1 else ''}: {reminder_text}."
        return SkillResult(True, speech, record)

    def _extract_text(self, transcript_lower: str) -> str | None:
        if "remind me to" in transcript_lower:
            return transcript_lower.split("remind me to", 1)[1].strip()
        return None

    def _extract_minutes(self, transcript_lower: str) -> int:
        for token in transcript_lower.split():
            if token.isdigit():
                return max(1, int(token))
        return 5

    def _persist_reminder(self, record: Dict[str, Any], context: Dict[str, Any]) -> None:
        artifacts_dir = Path(context.get("artifacts_dir", "/workspace/envy/artifacts"))
        reminders_path = artifacts_dir / "reminders.json"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        existing: List[Dict[str, Any]] = []
        if reminders_path.exists():
            try:
                existing = json.loads(reminders_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = []
        existing.append(record)
        reminders_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
