"""Base skill definitions for Envy assistant."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class SkillContext:
    config_path: Path
    artifacts_path: Path
    sandbox_paths: list[str]


@dataclass
class SkillResult:
    status: str
    message: str
    artifacts: Dict[str, str] = field(default_factory=dict)
    requires_confirmation: bool = False
    confirmation_id: Optional[str] = None


class Skill:
    name: str = "Skill"
    description: str = ""
    requires_confirmation: bool = False

    def execute(self, text: str, session_id: str, context: SkillContext) -> SkillResult:  # pragma: no cover - abstract
        raise NotImplementedError

    @staticmethod
    def timestamp() -> str:
        return dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")

