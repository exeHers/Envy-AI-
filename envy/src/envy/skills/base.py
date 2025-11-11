"""
Base definitions for Envy skills.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class SkillContext:
    artifacts_dir: Path
    data_dir: Path
    transcript: str
    config: Dict[str, object] = field(default_factory=dict)


@dataclass
class SkillResult:
    success: bool
    message: str
    requires_confirmation: bool = False
    artifact_path: Optional[Path] = None
    metadata: Dict[str, object] = field(default_factory=dict)


class BaseSkill(abc.ABC):
    name: str = "base"
    description: str = "Base skill"
    destructive: bool = False

    @abc.abstractmethod
    def matches(self, transcript: str) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def execute(self, context: SkillContext) -> SkillResult:
        raise NotImplementedError
