from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from services.skill_manager import SkillContext


@dataclass
class SkillBase(ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    requires_confirmation: ClassVar[bool] = False
    is_envy_skill: ClassVar[bool] = False

    @abstractmethod
    def handle(self, context: SkillContext) -> str:
        """Execute the skill with the provided context."""
