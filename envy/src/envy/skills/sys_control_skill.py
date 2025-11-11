from __future__ import annotations

import re

from .base import BaseSkill, SkillRequest, SkillResponse
from ..services.common.config import EnvyConfig, PROJECT_ROOT
from ..services.common.logging import get_logger


class SysControlSkill(BaseSkill):
    name = "sys_control_skill"
    intents = ("sys_control.execute",)

    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self.logger = get_logger("SysControlSkill", config=config)
        self.whitelist = set(config.get("skills.command_whitelist", []))
        self.pending_dir = (PROJECT_ROOT / "artifacts" / "pending_commands").resolve()

    def setup(self) -> None:
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    def handle(self, request: SkillRequest) -> SkillResponse:
        command = request.parameters.get("command") or self._infer_command(request.transcript)
        if command not in self.whitelist:
            return SkillResponse(success=False, message=f"Command '{command}' not permitted by whitelist.")
        pending_file = self.pending_dir / f"{request.session_id}.sh"
        pending_file.write_text(f"# Pending command for session {request.session_id}\n{command}\n", encoding="utf-8")
        self.logger.info(f"Queued command '{command}' for session {request.session_id}")
        return SkillResponse(
            success=True,
            message=f"Command '{command}' queued pending confirmation.",
            data={"command": command, "pending_file": str(pending_file)},
            requires_confirmation=True,
        )

    def _infer_command(self, transcript: str) -> str:
        match = re.search(r"(?:run|execute)\s+([a-zA-Z0-9_-]+)", transcript)
        if match:
            return match.group(1)
        return "ls"


__all__ = ["SysControlSkill"]
