from __future__ import annotations

import re
from pathlib import Path

from .base import BaseSkill, SkillRequest, SkillResponse
from ..services.common.config import EnvyConfig, PROJECT_ROOT
from ..services.common.logging import get_logger


class CodeSkill(BaseSkill):
    name = "code_skill"
    intents = ("code.create_file", "code.append_file")

    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self.logger = get_logger("CodeSkill", config=config)
        sandbox_root = Path(config.get("skills.sandbox_root", "."))
        self.sandbox_root = (PROJECT_ROOT / sandbox_root).resolve()
        self.default_target = (PROJECT_ROOT / config.get("tests.expected_code_skill_file", "workspace/test.py")).resolve()

    def setup(self) -> None:
        self.sandbox_root.mkdir(parents=True, exist_ok=True)

    def handle(self, request: SkillRequest) -> SkillResponse:
        if request.intent == "code.create_file":
            return self._handle_create_file(request)
        if request.intent == "code.append_file":
            return self._handle_append_file(request)
        return SkillResponse(success=False, message=f"Unsupported intent {request.intent}")

    def _handle_create_file(self, request: SkillRequest) -> SkillResponse:
        target_path = self._determine_path(request)
        content = request.parameters.get(
            "content",
            'print("hello from envy")\n',
        )
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        self.logger.info(f"Created file at {target_path}")
        return SkillResponse(success=True, message=f"Created file at {target_path}", data={"path": str(target_path)})

    def _handle_append_file(self, request: SkillRequest) -> SkillResponse:
        target_path = self._determine_path(request)
        addition = request.parameters.get("append", "# Appended by Envy\n")
        with target_path.open("a", encoding="utf-8") as handle:
            handle.write(addition)
        self.logger.info(f"Appended to file at {target_path}")
        return SkillResponse(success=True, message=f"Appended to file at {target_path}", data={"path": str(target_path)})

    def _determine_path(self, request: SkillRequest) -> Path:
        path_param = request.parameters.get("file_path")
        if path_param:
            candidate_path = Path(path_param)
            if candidate_path.is_absolute():
                candidate = candidate_path
            elif not candidate_path.parent or str(candidate_path.parent) == ".":
                candidate = (self.default_target.parent / candidate_path.name).resolve()
            else:
                candidate = (self.sandbox_root / candidate_path).resolve()
        else:
            candidate = self._infer_path_from_transcript(request.transcript)
        if not str(candidate).startswith(str(self.sandbox_root)):
            raise PermissionError(f"Path {candidate} is outside the sandbox root {self.sandbox_root}")
        return candidate

    def _infer_path_from_transcript(self, transcript: str) -> Path:
        pattern = re.compile(r"(?:create|make)\s+(?P<file>[\w./-]+\.py)", re.IGNORECASE)
        match = pattern.search(transcript)
        if match:
            filename = match.group("file")
            candidate = Path(filename)
            if not candidate.parent or str(candidate.parent) == ".":
                return (self.default_target.parent / candidate.name).resolve()
            return (self.sandbox_root / candidate).resolve()
        if "test" in transcript.lower():
            return self.default_target
        return self.default_target


__all__ = ["CodeSkill"]
