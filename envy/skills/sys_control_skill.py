from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .skill_base import Skill, SkillResult


class SysControlSkill(Skill):
    name = "SysControlSkill"
    description = "Executes sandboxed system control commands with confirmation for destructive actions."
    requires_confirmation = True

    def handle(self, instruction: str, context: Dict[str, Any]) -> SkillResult:
        command_tokens = self._parse_instruction(instruction)
        if not command_tokens:
            return SkillResult(
                status="failed",
                message="I could not parse a supported system command from that request.",
            )

        sandbox = self.config.get("sandbox", {})
        allowed_commands = sandbox.get("allowed_commands", [])
        command_name = command_tokens[0]
        force = context.get("force", False)

        if command_name not in allowed_commands:
            if force:
                return SkillResult(
                    status="blocked",
                    message=f"The command '{command_name}' is blocked in demo mode for safety.",
                    data={"command": command_tokens},
                )
            return SkillResult(
                status="needs_confirmation",
                message=f"The command '{command_name}' requires confirmation.",
                data={"command": command_tokens},
                requires_confirmation=True,
            )

        try:
            output = subprocess.check_output(command_tokens, stderr=subprocess.STDOUT, timeout=10)
            message = output.decode("utf-8", errors="ignore").strip()
        except subprocess.CalledProcessError as exc:  # pragma: no cover - error path
            message = exc.output.decode("utf-8", errors="ignore")
            return SkillResult(
                status="error",
                message=f"Command '{' '.join(command_tokens)}' failed.",
                data={"output": message},
            )

        return SkillResult(
            status="success",
            message=f"Command '{' '.join(command_tokens)}' executed successfully.",
            data={"output": message},
        )

    def _parse_instruction(self, instruction: str) -> Optional[List[str]]:
        text = instruction.lower()
        if "list" in text and "files" in text:
            return ["ls"]
        if "current directory" in text or "where am i" in text or "present working directory" in text:
            return ["pwd"]
        if "show file" in text:
            parts = instruction.split("show file", 1)[-1].strip().split()
            if parts:
                file_path = parts[0]
                safe_path = Path(file_path)
                if safe_path.exists():
                    return ["cat", str(safe_path)]
        if any(word in text for word in ("delete", "remove", "shutdown", "power off", "format")):
            return ["rm", "-rf", "/"]  # placeholder to force confirmation
        return None
