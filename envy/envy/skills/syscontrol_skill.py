from __future__ import annotations

import asyncio
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseSkill, SkillResult


class SysControlSkill(BaseSkill):
    name = "syscontrol"
    description = "Executes safe system commands from a whitelist."

    async def run(self, transcript: str, context: Dict[str, Any]) -> SkillResult:
        lower = transcript.lower()
        command = self._extract_command(lower)
        if not command:
            return SkillResult(False, "I did not recognize a system command.", {})

        whitelist: List[str] = context.get("command_whitelist", [])
        if command[0] not in whitelist:
            return SkillResult(False, f"{command[0]} is not in the safe command whitelist.", {})

        confirmed = bool(context.get("confirmed"))
        if not confirmed:
            speech = (
                "This command may affect the system. Please confirm by voice and in the dashboard before I execute it."
            )
            return SkillResult(
                False,
                speech,
                {"command": command},
                requires_confirmation=True,
            )

        result = await asyncio.to_thread(self._execute_command, command, context)
        return SkillResult(
            True,
            f"I ran {command[0]} and captured the output.",
            {"command": command, "output": result},
        )

    def needs_confirmation(self, transcript: str) -> bool:
        return True

    def _extract_command(self, transcript_lower: str) -> List[str] | None:
        markers = ["run", "execute", "start command"]
        for marker in markers:
            if marker in transcript_lower:
                after = transcript_lower.split(marker, 1)[1].strip()
                if after:
                    return shlex.split(after)
        return None

    def _execute_command(self, command: List[str], context: Dict[str, Any]) -> str:
        sandbox_dir = Path(context.get("sandbox_dir", "/workspace"))
        try:
            completed = subprocess.run(
                command,
                cwd=sandbox_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=15,
            )
            return completed.stdout.strip()
        except subprocess.CalledProcessError as exc:
            return exc.stdout.strip()
