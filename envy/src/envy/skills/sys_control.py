"""
SysControlSkill: executes whitelisted system commands with confirmations.
"""

from __future__ import annotations

import asyncio
import shlex
from pathlib import Path

from .base import BaseSkill, SkillContext, SkillResult


class SysControlSkill(BaseSkill):
    name = "sys_control"
    description = "Run whitelisted system commands."
    destructive = True

    def matches(self, transcript: str) -> bool:
        lowered = transcript.lower()
        return any(keyword in lowered for keyword in ["run", "execute", "restart service", "shutdown"])

    async def execute(self, context: SkillContext) -> SkillResult:
        whitelist = context.config.get("command_whitelist", {})
        if not isinstance(whitelist, dict):
            whitelist = {}

        command = self._extract_command(context.transcript)
        if not command:
            return SkillResult(success=False, message="Could not parse system command request.")

        if command not in whitelist:
            return SkillResult(
                success=False,
                message="Command not whitelisted; edit config/envy.yaml to allow it.",
                requires_confirmation=True,
            )

        if not whitelist[command]:
            return SkillResult(
                success=False,
                message="Command explicitly disabled in whitelist.",
                requires_confirmation=True,
            )

        args = shlex.split(command)
        result = await asyncio.to_thread(self._run_command, args, Path(context.config.get("workspace_root", ".")))

        return SkillResult(
            success=result["returncode"] == 0,
            message=result["stdout"] or result["stderr"] or "Command executed.",
            metadata=result,
            requires_confirmation=True,
        )

    def _extract_command(self, transcript: str) -> str | None:
        lowered = transcript.lower()
        if lowered.startswith("envy"):
            lowered = lowered[len("envy") :].strip()
        markers = ["run", "execute", "start", "shutdown", "restart"]
        for marker in markers:
            idx = lowered.find(marker)
            if idx != -1:
                return transcript[idx:].replace(marker, "", 1).strip()
        return None

    def _run_command(self, args: list[str], cwd: Path) -> dict[str, str | int]:
        import subprocess

        try:
            completed = subprocess.run(
                args,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                check=False,
            )
            return {
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        except Exception as exc:  # pragma: no cover - defensive
            return {"returncode": -1, "stdout": "", "stderr": str(exc)}
