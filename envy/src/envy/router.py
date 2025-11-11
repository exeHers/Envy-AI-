"""
Router coordinates transcripts, intent classification, and skill execution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .config import EnvyConfig
from .llm_adapter import LLMAdapter
from .skills import build_skill_registry
from .skills.base import BaseSkill, SkillContext

_LOGGER = logging.getLogger(__name__)


@dataclass
class RouterOutcome:
    transcript: str
    skill: Optional[str]
    success: bool
    message: str
    requires_confirmation: bool = False
    artifact_path: Optional[Path] = None
    metadata: Dict[str, object] | None = None
    llm_backend: str | None = None


@dataclass
class IntentDecision:
    skill: Optional[str]
    is_confirmation: bool
    llm_backend: Optional[str] = None


class IntentClassifier:
    """
    Lightweight classifier with rule-based heuristics backed by LLM fallback.
    """

    def __init__(self, llm_adapter: LLMAdapter):
        self._llm = llm_adapter

    async def determine_skill(
        self,
        transcript: str,
        skills: Dict[str, BaseSkill],
        pending: Dict[str, SkillContext],
    ) -> IntentDecision:
        lowered = transcript.lower()
        if "confirm" in lowered or lowered.strip() in {"yes", "yeah", "do it"}:
            target_skill = None
            if len(pending) == 1:
                target_skill = next(iter(pending))
            else:
                for skill in pending:
                    if skill in lowered:
                        target_skill = skill
                        break
            if target_skill:
                return IntentDecision(skill=target_skill, is_confirmation=True)

        # Rule-based heuristics
        if any(keyword in lowered for keyword in ["create", "file", "code"]):
            return IntentDecision(skill="code", is_confirmation=False)
        if "research" in lowered or "look up" in lowered:
            return IntentDecision(skill="research", is_confirmation=False)
        if "remind" in lowered or "reminder" in lowered:
            return IntentDecision(skill="reminder", is_confirmation=False)
        if any(keyword in lowered for keyword in ["shutdown", "restart", "run command", "execute"]):
            return IntentDecision(skill="sys_control", is_confirmation=False)

        # Ask LLM for fallback classification
        prompt = (
            "You are an intent classifier. Read the transcript and respond with one of the skill names: "
            f"{', '.join(skills.keys())}. Transcript: {transcript}"
        )
        result = await self._llm.generate(prompt, system_prompt="Intent classifier")
        backend = result.backend
        suggestion = result.text.strip().lower()
        _LOGGER.debug("LLM intent suggestion (%s): %s", backend, suggestion)
        for skill in skills:
            if skill in suggestion:
                return IntentDecision(skill=skill, is_confirmation=False, llm_backend=backend)
        return IntentDecision(skill=None, is_confirmation=False, llm_backend=backend)


class SkillRouter:
    def __init__(
        self,
        config: EnvyConfig,
        llm_adapter: LLMAdapter,
        skills_path: Optional[Path] = None,
    ) -> None:
        self.config = config
        self.llm = llm_adapter
        self.skills: Dict[str, BaseSkill] = build_skill_registry(skills_path)
        self.classifier = IntentClassifier(self.llm)
        self._pending_destructive: Dict[str, SkillContext] = {}
        self.dashboard_confirmations: Dict[str, bool] = {}

    async def handle_transcript(
        self,
        transcript: str,
        *,
        voice_confirmed: bool = False,
        dashboard_confirmed: bool = False,
    ) -> RouterOutcome:
        transcript = transcript.strip()
        if not transcript:
            return RouterOutcome(transcript=transcript, skill=None, success=False, message="Empty transcript.")

        decision = await self.classifier.determine_skill(transcript, self.skills, self._pending_destructive)
        skill_name = decision.skill
        if not skill_name or skill_name not in self.skills:
            return RouterOutcome(
                transcript=transcript,
                skill=None,
                success=False,
                message="No matching skill.",
                llm_backend=decision.llm_backend or self.llm.config.llm.default_backend,
            )

        skill = self.skills[skill_name]

        whitelist = self.config.skills.whitelist
        if whitelist and skill_name in whitelist and not whitelist[skill_name]:
            return RouterOutcome(
                transcript=transcript,
                skill=skill_name,
                success=False,
                message="Skill disabled in configuration.",
            )

        requires_confirmation = (
            skill.destructive
            or self.config.security.destructive_confirmation
            and skill_name in ("sys_control",)
            or self.config.skills.requires_confirmation.get(skill_name, False)
        )

        context = SkillContext(
            artifacts_dir=self.config.artifacts_dir,
            data_dir=self.config.data_dir,
            transcript=transcript,
            config={
                "workspace_root": str((Path.cwd() / "workspace").resolve()),
                "command_whitelist": self.config.security.command_whitelist,
            },
        )

        if decision.is_confirmation:
            voice_confirmed = True
            dashboard_confirmed = self.dashboard_confirmations.get(skill_name, False)

        if requires_confirmation and not (voice_confirmed and dashboard_confirmed):
            self._pending_destructive[skill_name] = context
            return RouterOutcome(
                transcript=transcript,
                skill=skill_name,
                success=False,
                message="Confirmation required before executing this skill.",
                requires_confirmation=True,
            )

        if requires_confirmation and skill_name in self._pending_destructive:
            context = self._pending_destructive.pop(skill_name)
            self.dashboard_confirmations.pop(skill_name, None)

        try:
            result = await skill.execute(context)
        except Exception as exc:  # pragma: no cover - defensive
            _LOGGER.exception("Skill %s execution failure: %s", skill_name, exc)
            return RouterOutcome(
                transcript=transcript,
                skill=skill_name,
                success=False,
                message=f"Skill execution failed: {exc}",
            )

        return RouterOutcome(
            transcript=transcript,
            skill=skill_name,
            success=result.success,
            message=result.message,
            requires_confirmation=result.requires_confirmation,
            artifact_path=result.artifact_path,
            metadata=result.metadata,
            llm_backend=self.llm.config.llm.default_backend,
        )

    def register_dashboard_confirmation(self, skill: str) -> None:
        self.dashboard_confirmations[skill] = True
