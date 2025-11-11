from __future__ import annotations

import logging
import shlex
import subprocess
from pathlib import Path
from typing import List

from .base import Skill, SkillContext, SkillResult

LOGGER = logging.getLogger(__name__)


class SysControlSkill(Skill):
    name = "syscontrol"
    description = "Execute whitelisted system commands inside a sandbox."
    requires_confirmation = True

    def can_handle(self, command: str) -> bool:
        lowered = command.lower()
        return any(keyword in lowered for keyword in ("system", "run", "execute"))

    def execute(self, command: str, context: SkillContext) -> SkillResult:
        LOGGER.info("SysControlSkill evaluating command: %s", command)
        whitelist = context.runtime_config.skills.get("whitelist_commands", [])
        exec_cmd = self._extract_command(command, whitelist)
        if not exec_cmd:
            return SkillResult(
                handled=False,
                response="No whitelisted system command detected.",
            )

        if context.require_confirmation() and not (context.voice_confirmed and context.dashboard_confirmed):
            LOGGER.info("SysControlSkill requires confirmation before execution.")
            return SkillResult(
                handled=False,
                response="Awaiting confirmation before running system command.",
                requires_confirmation=True,
                confirmation_message=f"Confirm execution of: {' '.join(exec_cmd)}",
            )

        sandbox_name = context.runtime_config.security.get("sandbox_workdir", "workspace")
        sandbox = context.workspace_dir / sandbox_name
        sandbox.mkdir(parents=True, exist_ok=True)

        LOGGER.info("Executing whitelisted command in sandbox %s", sandbox)
        completed = subprocess.run(
            exec_cmd,
            cwd=sandbox,
            capture_output=True,
            text=True,
            timeout=15,
        )

        artifacts_dir = context.artifacts_dir / "commands"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        log_path = artifacts_dir / "syscontrol.log"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"$ {' '.join(exec_cmd)}\n")
            handle.write(completed.stdout)
            handle.write(completed.stderr)
            handle.write("\n---\n")

        LOGGER.info("System command completed with return code %s", completed.returncode)
        response = (
            f"Command executed with code {completed.returncode}. Output stored in {log_path.name}."
        )
        return SkillResult(
            handled=True,
            response=response,
            artifacts=[log_path],
        )

    @staticmethod
    def _extract_command(command: str, whitelist: List[str]) -> List[str] | None:
        tokens = shlex.split(command.lower())
        for allowed in whitelist:
            if allowed in tokens:
                # Build a sanitized command: first occurrence plus trailing tokens.
                start = tokens.index(allowed)
                args = tokens[start:]
                sanitized = [allowed]
                for token in args[1:]:
                    if all(ch.isalnum() or ch in (".", "_", "-", "/") for ch in token):
                        sanitized.append(token)
                return sanitized
        return None
