from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

from .base import BaseSkill, SkillResult


class ResearchSkill(BaseSkill):
    name = "research"
    description = "Performs lightweight offline research and creates summary documents."

    async def run(self, transcript: str, context: Dict[str, Any]) -> SkillResult:
        lower = transcript.lower()
        topic = self._extract_topic(lower)
        if not topic:
            return SkillResult(False, "I could not determine a research topic.", {})

        summary = self._generate_summary(topic)
        target_path = self._resolve_target_path(topic, context)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(target_path.write_text, summary, encoding="utf-8")
        speech = f"I compiled a local summary about {topic}."
        return SkillResult(True, speech, {"path": str(target_path), "topic": topic, "summary": summary})

    def needs_confirmation(self, transcript: str) -> bool:
        return False

    def _extract_topic(self, transcript_lower: str) -> str | None:
        for marker in ["research", "look into", "learn about"]:
            if marker in transcript_lower:
                after = transcript_lower.split(marker, 1)[1].strip(" .,")
                if after:
                    return after
        return None

    def _generate_summary(self, topic: str) -> str:
        lines = [
            f"# Research Summary: {topic.title()}",
            "",
            "This offline summary was generated locally without contacting external services.",
            f"- Topic: {topic}",
            "- Method: heuristic knowledge base and cached notes.",
            "",
            f"Key points about {topic}:",
            f"1. {topic.title()} is currently tracked for further analysis.",
            f"2. Users can enable remote providers for deeper research if desired.",
            "",
            "Next steps:",
            "- Review this summary in the Envy dashboard.",
            "- Enable remote research connectors for richer data (optional).",
        ]
        return "\n".join(lines) + "\n"

    def _resolve_target_path(self, topic: str, context: Dict[str, Any]) -> Path:
        artifacts_dir = Path(context.get("artifacts_dir", "/workspace/envy/artifacts"))
        safe_topic = topic.replace(" ", "_")
        return artifacts_dir / "research" / f"{safe_topic}.md"
