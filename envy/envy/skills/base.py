from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envy.config_loader import RuntimeConfig


@dataclass
class SkillResult:
    handled: bool
    response: str
    artifacts: List[Path] = field(default_factory=list)
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None


@dataclass
class SkillContext:
    runtime_config: RuntimeConfig
    workspace_dir: Path
    artifacts_dir: Path
    confirmation_required: bool
    dashboard_confirmed: bool = False
    voice_confirmed: bool = False

    def require_confirmation(self) -> bool:
        security = self.runtime_config.security
        return (
            self.confirmation_required
            or security.get("require_dashboard_confirmation", False)
            and not self.dashboard_confirmed
        )


class Skill(abc.ABC):
    name: str = "base"
    description: str = ""
    requires_confirmation: bool = False

    def __init__(self, runtime_config: RuntimeConfig) -> None:
        self.runtime_config = runtime_config

    @abc.abstractmethod
    def can_handle(self, command: str) -> bool:
        ...

    @abc.abstractmethod
    def execute(self, command: str, context: SkillContext) -> SkillResult:
        ...
