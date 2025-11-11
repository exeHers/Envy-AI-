from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SkillResult:
    success: bool
    speech: str
    data: Dict[str, Any]
    requires_confirmation: bool = False


class BaseSkill(abc.ABC):
    name: str
    description: str

    def __init__(self, config: Dict[str, Any] | None = None):
        self.config = config or {}

    @abc.abstractmethod
    async def run(self, transcript: str, context: Dict[str, Any]) -> SkillResult:
        ...

    def needs_confirmation(self, transcript: str) -> bool:
        return False
