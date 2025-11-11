"""SysControlSkill: handles system control requests with confirmation."""

from __future__ import annotations

import hashlib
import re

from .base import Skill, SkillContext, SkillResult


class SysControlSkill(Skill):
    name = "SysControlSkill"
    description = "Request system-level actions such as shutdown or restart (requires confirmation)."
    requires_confirmation = True

    def execute(self, text: str, session_id: str, context: SkillContext) -> SkillResult:
        action = self._identify_action(text)
        if not action:
            return SkillResult(
                status="no_action",
                message="No recognized system control action found.",
            )

        confirmation_id = self._confirmation_id(action, session_id)
        message = (
            f"System control action '{action}' requested. Awaiting voice and dashboard confirmation."
        )
        return SkillResult(
            status="pending_confirmation",
            message=message,
            requires_confirmation=True,
            confirmation_id=confirmation_id,
            artifacts={"requested_action": action},
        )

    def _identify_action(self, text: str) -> str | None:
        lowered = text.lower()
        if "shutdown" in lowered:
            return "shutdown"
        if "restart" in lowered or "reboot" in lowered:
            return "restart"
        if "sleep" in lowered:
            return "sleep"
        return None

    def _confirmation_id(self, action: str, session_id: str) -> str:
        digest = hashlib.sha256(f"{session_id}:{action}".encode("utf-8")).hexdigest()
        return digest[:12]


__all__ = ["SysControlSkill"]

