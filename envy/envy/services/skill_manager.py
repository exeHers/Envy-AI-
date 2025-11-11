from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Sequence, Type

from envy.config_loader import RuntimeConfig
from envy.skills.base import Skill, SkillContext, SkillResult
from envy.skills.code_skill import CodeSkill
from envy.skills.reminder_skill import ReminderSkill
from envy.skills.research_skill import ResearchSkill
from envy.skills.sys_control_skill import SysControlSkill

LOGGER = logging.getLogger(__name__)


class SkillManager:
    """Loads and dispatches skills based on the configured whitelist."""

    BUILTIN_SKILLS: Dict[str, Type[Skill]] = {
        CodeSkill.name: CodeSkill,
        ResearchSkill.name: ResearchSkill,
        SysControlSkill.name: SysControlSkill,
        ReminderSkill.name: ReminderSkill,
    }

    def __init__(
        self,
        runtime_config: RuntimeConfig,
        workspace_dir: Path,
        artifacts_dir: Path,
    ) -> None:
        self.runtime_config = runtime_config
        self.workspace_dir = workspace_dir
        self.artifacts_dir = artifacts_dir
        enabled = runtime_config.skills.get("enabled", [])
        self.skills: List[Skill] = []
        for key in enabled:
            skill_cls = self.BUILTIN_SKILLS.get(key)
            if skill_cls:
                self.skills.append(skill_cls(runtime_config))
            else:
                LOGGER.warning("Unknown skill '%s' configured; skipping.", key)

        LOGGER.info("SkillManager loaded skills: %s", [skill.name for skill in self.skills])

    def dispatch(
        self,
        command: str,
        voice_confirmed: bool = False,
        dashboard_confirmed: bool = False,
    ) -> SkillResult:
        LOGGER.info("Dispatching command to skills: %s", command)

        for skill in self.skills:
            if not skill.can_handle(command):
                continue

            requires_confirmation = (
                skill.requires_confirmation
                and self.runtime_config.skills.get("destructive_requires_confirmation", True)
            )

            context = SkillContext(
                runtime_config=self.runtime_config,
                workspace_dir=self.workspace_dir,
                artifacts_dir=self.artifacts_dir,
                confirmation_required=requires_confirmation,
                voice_confirmed=voice_confirmed,
                dashboard_confirmed=dashboard_confirmed,
            )

            result = skill.execute(command, context)
            if requires_confirmation and not (voice_confirmed and dashboard_confirmed):
                result.requires_confirmation = True
                result.confirmation_message = result.confirmation_message or (
                    "Skill execution pending confirmation."
                )
                result.handled = False
            return result

        LOGGER.info("No skill handled the command: %s", command)
        return SkillResult(
            handled=False,
            response="No matching skill found. Falling back to LLM adapter.",
        )
