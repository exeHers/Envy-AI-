from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SkillRequest:
    session_id: str
    intent: str
    transcript: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillResponse:
    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    confirmation_id: Optional[str] = None


class BaseSkill:
    name: str = "base"
    intents: tuple[str, ...] = ()

    def setup(self) -> None:  # noqa: D401 - optional
        """Perform optional setup when the skill is loaded."""

    def can_handle(self, intent: str) -> bool:
        return intent in self.intents

    def handle(self, request: SkillRequest) -> SkillResponse:
        raise NotImplementedError


__all__ = ["SkillRequest", "SkillResponse", "BaseSkill"]
