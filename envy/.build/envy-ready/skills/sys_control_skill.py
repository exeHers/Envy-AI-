from __future__ import annotations

import subprocess
from pathlib import Path

from .base import SkillBase


class SysControlSkill(SkillBase):
    name = "syscontrol"
    description = "Manages limited system control actions like listing directories."
    requires_confirmation = True
    is_envy_skill = True

    def handle(self, context):
        command = context.metadata.get("command") or "ls"
        whitelist = context.config["security"]["command_whitelist"]
        artifacts_dir = context.artifacts_dir / "syscontrol"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        log_path = artifacts_dir / "syscontrol.log"

        if command not in whitelist:
            raise PermissionError(f"Command {command} not in whitelist.")

        result = subprocess.run(
            [command],
            capture_output=True,
            text=True,
            check=False,
        )
        log_path.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
        return f"Command {command} executed with return code {result.returncode}."
