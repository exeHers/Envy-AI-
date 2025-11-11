from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

from .base import BaseSkill, SkillResult


class CodeSkill(BaseSkill):
    name = "code"
    description = "Creates or edits small code files on request."

    async def run(self, transcript: str, context: Dict[str, Any]) -> SkillResult:
        lower = transcript.lower()
        if "create" in lower and ".py" in lower:
            filename = self._extract_filename(lower)
            if not filename:
                return SkillResult(False, "I could not find the filename to create.", {})

            content = self._extract_content(lower)
            if not content:
                content = 'print("hello from envy")'

            target_path = self._resolve_target_path(filename)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(target_path.write_text, content + "\n", encoding="utf-8")
            return SkillResult(
                True,
                f"I created {target_path.name} with your requested content.",
                {"path": str(target_path), "content": content},
            )

        return SkillResult(False, "I did not recognize a coding request.", {})

    def needs_confirmation(self, transcript: str) -> bool:
        lower = transcript.lower()
        if any(word in lower for word in ["delete", "remove", "wipe", "format"]):
            return True
        return False

    def _extract_filename(self, transcript_lower: str) -> str | None:
        tokens = [token.strip(".,!?:;\"'") for token in transcript_lower.split()]
        for token in tokens:
            if token.endswith(".py"):
                return token
        return None

    def _extract_content(self, transcript_lower: str) -> str | None:
        marker = "prints"
        if marker in transcript_lower:
            after = transcript_lower.split(marker, 1)[1].strip()
            if after:
                return f'print("{after}")'
        return None

    def _resolve_target_path(self, filename: str) -> Path:
        workspace_root = Path("/workspace")
        safe_name = filename.replace("/", "_")
        return workspace_root / safe_name
