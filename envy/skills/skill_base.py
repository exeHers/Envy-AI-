from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SkillResult:
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False
    confirmation_id: Optional[str] = None


class Skill(ABC):
    """Base class for all Envy skills."""

    name: str = "Skill"
    description: str = ""
    requires_confirmation: bool = False

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config

    @abstractmethod
    def handle(self, instruction: str, context: Dict[str, Any]) -> SkillResult:
        """Process the instruction and return a structured response."""
