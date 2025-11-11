from __future__ import annotations

import asyncio
import importlib
import logging
import pkgutil
from typing import Dict, Optional, Type

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ...skills.base import BaseSkill, SkillResult

logger = logging.getLogger("envy.skill_manager")


class SkillExecutionRequest(BaseModel):
    skill_name: str
    transcript: str
    context: Dict[str, object] = {}


class SkillExecutionResponse(BaseModel):
    success: bool
    speech: str
    data: Dict[str, object] = {}
    requires_confirmation: bool = False


class SkillManager:
    def __init__(self, package: str = "envy.skills", config: Dict[str, object] | None = None):
        self.package = package
        self.config = config or {}
        self._skills: Dict[str, BaseSkill] = {}

    def load_skills(self, allowed: Optional[list[str]] = None) -> None:
        allowed_set = set(allowed) if allowed else None
        package_module = importlib.import_module(self.package)
        for module_info in pkgutil.iter_modules(package_module.__path__):
            if module_info.name in {"base"}:
                continue
            module = importlib.import_module(f"{self.package}.{module_info.name}")
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and issubclass(obj, BaseSkill) and obj is not BaseSkill:
                    skill: BaseSkill = obj(config=self.config.get(obj.name, {}))
                    if allowed_set and skill.name not in allowed_set:
                        continue
                    self._skills[skill.name] = skill
                    logger.info("Loaded skill %s from %s", skill.name, module_info.name)

    def available_skills(self) -> Dict[str, str]:
        return {name: skill.description for name, skill in self._skills.items()}

    async def execute(self, skill_name: str, transcript: str, context: Dict[str, object]) -> SkillResult:
        if skill_name not in self._skills:
            raise KeyError(f"Skill '{skill_name}' not loaded")
        skill = self._skills[skill_name]
        merged_context = dict(context)
        merged_context.setdefault("artifacts_dir", "/workspace/envy/artifacts")
        merged_context.setdefault("command_whitelist", self.config.get("command_whitelist", []))
        merged_context.setdefault("sandbox_dir", "/workspace")
        result = await skill.run(transcript, merged_context)
        confirmed = bool(merged_context.get("confirmed"))
        if skill.needs_confirmation(transcript) and not confirmed and not result.success:
            result.requires_confirmation = True
        return result


def create_app(skill_manager: SkillManager) -> FastAPI:
    app = FastAPI(title="Envy Skill Manager")

    @app.on_event("startup")
    async def startup_event():
        allowed = skill_manager.config.get("enabled_skills")
        skill_manager.load_skills(allowed=allowed)

    @app.get("/skills")
    async def list_skills():
        return skill_manager.available_skills()

    @app.post("/execute", response_model=SkillExecutionResponse)
    async def execute(request: SkillExecutionRequest):
        try:
            result = await skill_manager.execute(request.skill_name, request.transcript, request.context)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return SkillExecutionResponse(
            success=result.success,
            speech=result.speech,
            data=result.data,
            requires_confirmation=result.requires_confirmation,
        )

    return app
