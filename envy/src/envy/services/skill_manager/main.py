from __future__ import annotations

import importlib
import inspect
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Dict, Optional, Type

import typer
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..common.config import EnvyConfig
from ..common.deps import get_config, verify_secret
from ..common.logging import get_logger
from ...skills.base import BaseSkill, SkillRequest, SkillResponse


class SkillExecutionRequest(BaseModel):
    session_id: str
    intent: str
    skill: str
    transcript: str
    parameters: dict = Field(default_factory=dict)


class SkillExecutionResponse(BaseModel):
    success: bool
    message: str
    data: dict = Field(default_factory=dict)
    requires_confirmation: bool = False
    confirmation_id: Optional[str] = None


def _load_skill_class(module_name: str) -> Type[BaseSkill]:
    module = importlib.import_module(f"envy.skills.{module_name}")
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, BaseSkill) and obj is not BaseSkill:
            return obj
    raise ImportError(f"No skill class found in module {module_name}")


class SkillRegistry:
    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self.logger = get_logger("SkillRegistry", config=config)
        self.skills: Dict[str, BaseSkill] = {}
        max_workers = config.get("concurrency.max_skills", 2) or 2
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._load_skills()

    def _load_skills(self) -> None:
        enabled = self.config.get("skills.enabled", [])
        for module_name in enabled:
            try:
                skill_class = _load_skill_class(module_name)
                skill: BaseSkill = skill_class(self.config)
                skill.setup()
                self.skills[skill.name] = skill
                self.logger.info(f"Loaded skill: {skill.name}")
            except Exception as exc:  # noqa: BLE001
                self.logger.error(f"Failed to load skill {module_name}: {exc}")

    def execute(self, request: SkillExecutionRequest) -> SkillResponse:
        skill = self.skills.get(request.skill)
        if not skill:
            raise ValueError(f"Skill '{request.skill}' is not loaded.")
        if not skill.can_handle(request.intent):
            raise ValueError(f"Skill '{request.skill}' cannot handle intent '{request.intent}'.")
        skill_request = SkillRequest(
            session_id=request.session_id,
            intent=request.intent,
            transcript=request.transcript,
            parameters=request.parameters or {},
        )
        future = self.executor.submit(skill.handle, skill_request)
        timeout = self.config.get("skill_manager.timeout_seconds", 25)
        try:
            return future.result(timeout=timeout)
        except TimeoutError as exc:
            self.logger.error(f"Skill {skill.name} timed out for session {request.session_id}")
            future.cancel()
            raise TimeoutError(f"Skill {skill.name} timed out") from exc


def create_app() -> FastAPI:
    config = get_config()
    logger = get_logger("SkillManagerService", config=config)
    registry = SkillRegistry(config)

    app = FastAPI(title="Envy Skill Manager", version="0.1.0")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "skills": list(registry.skills.keys())}

    @app.get("/skills", dependencies=[Depends(verify_secret)])
    async def list_skills() -> dict:
        return {"skills": list(registry.skills.keys())}

    @app.post("/execute", response_model=SkillExecutionResponse, dependencies=[Depends(verify_secret)])
    async def execute_skill(request: SkillExecutionRequest) -> SkillExecutionResponse:
        try:
            result = registry.execute(request)
        except (ValueError, TimeoutError) as exc:
            logger.error(f"Skill execution error: {exc}")
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"Unhandled skill execution error: {exc}")
            raise HTTPException(status_code=500, detail="Skill execution failed")
        return SkillExecutionResponse(
            success=result.success,
            message=result.message,
            data=result.data,
            requires_confirmation=result.requires_confirmation,
            confirmation_id=result.confirmation_id,
        )

    return app


app = create_app()


def main(
    host: str = typer.Option("0.0.0.0", help="Host for the skill manager service."),
    port: int = typer.Option(8204, help="Port for the skill manager service."),
    reload: bool = typer.Option(False, help="Enable autoreload (development only)."),
) -> None:
    uvicorn.run("envy.services.skill_manager.main:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    typer.run(main)
