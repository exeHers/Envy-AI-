from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import load_config
from ..logger import get_logger


logger = get_logger("skill_manager")


@dataclass
class SkillContext:
    transcript: str
    metadata: Dict[str, Any]
    config: Dict[str, Any]
    artifacts_dir: Path
    confirmation_voice: bool = False
    confirmation_dashboard: bool = False


@dataclass
class SkillExecutionResult:
    skill: str
    success: bool
    output: str
    requires_confirmation: bool
    confirmations_obtained: bool


class SkillManager:
    def __init__(self, skills_path: Optional[Path] = None):
        self.config = load_config()
        self.skills_path = skills_path or Path(__file__).resolve().parents[2] / "skills"
        self.skills: Dict[str, Any] = {}
        self._load_skills()

    def _load_skills(self):
        package_name = "skills"
        logger.info("Loading skills from %s", self.skills_path)
        for module_info in pkgutil.iter_modules([str(self.skills_path)]):
            module_name = f"{package_name}.{module_info.name}"
            module = importlib.import_module(module_name)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if getattr(obj, "is_envy_skill", False):
                    instance = obj()
                    self.skills[instance.name] = instance
                    logger.info("Registered skill: %s", instance.name)

    def execute(self, intent: str, transcript: str, metadata: Dict[str, Any]) -> SkillExecutionResult:
        if not intent.startswith("skill:"):
            return SkillExecutionResult(
                skill="none",
                success=False,
                output=f"No matching skill for intent {intent}.",
                requires_confirmation=False,
                confirmations_obtained=False,
            )

        skill_name = intent.split(":", 1)[1]
        if skill_name not in self.skills:
            return SkillExecutionResult(
                skill=skill_name,
                success=False,
                output=f"Skill {skill_name} not registered.",
                requires_confirmation=False,
                confirmations_obtained=False,
            )

        skill = self.skills[skill_name]
        security_conf = self.config.get("security", {})
        required = security_conf.get("require_confirmation_for", [])
        requires_confirmation = skill.requires_confirmation or skill_name in required

        confirmations_obtained = not requires_confirmation
        artifacts_dir = Path(self.config["runtime"]["artifacts_dir"])
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        context = SkillContext(
            transcript=transcript,
            metadata=metadata,
            config=self.config,
            artifacts_dir=artifacts_dir,
            confirmation_voice=metadata.get("voice_confirmed", False),
            confirmation_dashboard=metadata.get("dashboard_confirmed", False),
        )

        if requires_confirmation and not (context.confirmation_voice and context.confirmation_dashboard):
            logger.warning("Skill %s awaiting confirmations. metadata=%s", skill_name, json.dumps(metadata))
            return SkillExecutionResult(
                skill=skill_name,
                success=False,
                output="Awaiting confirmations.",
                requires_confirmation=True,
                confirmations_obtained=False,
            )

        try:
            output = skill.handle(context)
            return SkillExecutionResult(
                skill=skill_name,
                success=True,
                output=output,
                requires_confirmation=requires_confirmation,
                confirmations_obtained=True,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Skill %s failed: %s", skill_name, exc)
            return SkillExecutionResult(
                skill=skill_name,
                success=False,
                output=str(exc),
                requires_confirmation=requires_confirmation,
                confirmations_obtained=True,
            )
