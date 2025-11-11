"""Skill manager microservice."""

from __future__ import annotations

import argparse
import importlib
import inspect
import logging
import pkgutil
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from ..config import EnvyConfig, load_config
from ..logging_config import configure_logging
from skills.base import Skill, SkillContext, SkillResult

LOGGER = logging.getLogger("envy.skills")


class SkillRequest(BaseModel):
    skill: str
    text: str
    session_id: str


class SkillResponse(BaseModel):
    status: str
    message: str
    artifacts: Dict[str, str] = {}
    requires_confirmation: bool = False
    confirmation_id: Optional[str] = None


class SkillRegistry:
    def __init__(self, config: EnvyConfig):
        self.config = config
        config_path = Path(__file__).resolve().parents[2] / "config" / "envy.yaml"
        self.context = SkillContext(
            config_path=config_path,
            artifacts_path=config.artifacts_path,
            sandbox_paths=config.safety.sandbox_paths,
        )
        self.skills: Dict[str, Skill] = {}
        self._load_skills()

    def _load_skills(self) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        skill_paths = [
            Path(path) if Path(path).is_absolute() else (base_dir / path)
            for path in self.config.skill_paths
        ]
        for skill_path in skill_paths:
            if not skill_path.exists():
                LOGGER.warning("Skill path does not exist: %s", skill_path)
                continue
            package_name = skill_path.name
            module_prefix = f"skills."
            for _, module_name, _ in pkgutil.iter_modules([str(skill_path)]):
                if module_name == "base":
                    continue
                module = importlib.import_module(f"skills.{module_name}")
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Skill) and obj is not Skill:
                        instance = obj()
                        self.skills[instance.name] = instance
                        LOGGER.info("Loaded skill %s from %s", instance.name, module_name)

    def execute(self, name: str, text: str, session_id: str) -> SkillResult:
        if name not in self.skills:
            raise ValueError(f"Unknown skill '{name}'")
        skill = self.skills[name]
        return skill.execute(text, session_id, self.context)


def create_app(config: EnvyConfig) -> FastAPI:
    registry = SkillRegistry(config)
    app = FastAPI(title="Envy Skill Manager", version="0.1.0")

    @app.get("/skills")
    async def list_skills():
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "requires_confirmation": skill.requires_confirmation,
            }
            for skill in registry.skills.values()
        ]

    @app.post("/skills/execute", response_model=SkillResponse)
    async def execute(request: SkillRequest):
        try:
            result = registry.execute(request.skill, request.text, request.session_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return SkillResponse(
            status=result.status,
            message=result.message,
            artifacts=result.artifacts,
            requires_confirmation=result.requires_confirmation,
            confirmation_id=result.confirmation_id,
        )

    @app.get("/health")
    async def health():
        return {"status": "ok", "skills": list(registry.skills.keys())}

    return app


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Run the Envy skill manager service.")
    parser.add_argument("--config", type=str, default=str(CONFIG_PATH := Path(__file__).resolve().parents[2] / "config" / "envy.yaml"))
    parser.add_argument("--host", type=str, help="Override host binding")
    parser.add_argument("--port", type=int, help="Override port binding")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))
    service_conf = config.services["skill_manager"]
    host = args.host or service_conf.host
    port = args.port or service_conf.port

    configure_logging(config, "skill_manager")
    app = create_app(config)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    main()

