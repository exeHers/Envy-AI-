from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .skill_base import Skill, SkillResult


class ReminderSkill(Skill):
    name = "ReminderSkill"
    description = "Stores simple reminders and persists them to disk."

    def handle(self, instruction: str, context: Dict[str, Any]) -> SkillResult:
        storage_path = Path(self.config.get("reminders", {}).get("storage_path", "./runtime/reminders.json"))
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        reminders = self._load_reminders(storage_path)
        reminder = {
            "id": len(reminders) + 1,
            "text": instruction.strip(),
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        reminders.append(reminder)
        storage_path.write_text(json.dumps(reminders, indent=2), encoding="utf-8")

        return SkillResult(
            status="success",
            message="Reminder captured.",
            data={"reminder": reminder, "storage_path": str(storage_path)},
        )

    def _load_reminders(self, storage_path: Path) -> List[Dict[str, Any]]:
        if storage_path.exists():
            try:
                return json.loads(storage_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:  # pragma: no cover - corrupted file
                return []
        return []
