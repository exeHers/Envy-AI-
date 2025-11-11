"""ResearchSkill: synthesizes brief research summaries."""

from __future__ import annotations

import re
from pathlib import Path

from .base import Skill, SkillContext, SkillResult


class ResearchSkill(Skill):
    name = "ResearchSkill"
    description = "Generate a concise research summary and save it to artifacts."
    requires_confirmation = False

    def execute(self, text: str, session_id: str, context: SkillContext) -> SkillResult:
        topic = self._extract_topic(text)
        if not topic:
            topic = "general inquiry"

        summary = self._generate_summary(topic)

        timestamp = self.timestamp()
        output_dir = context.artifacts_path / "research"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{timestamp}-{self._slug(topic)}.md"
        output_path.write_text(summary, encoding="utf-8")

        message = f"Research summary for '{topic}' saved to {output_path.name}."
        return SkillResult(
            status="ok",
            message=message,
            artifacts={"summary_file": str(output_path)},
        )

    def _extract_topic(self, text: str) -> str | None:
        match = re.search(r"research\s+(.*)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    def _generate_summary(self, topic: str) -> str:
        return (
            f"# Research Summary: {topic}\n\n"
            f"- Context: Offline quick-look prepared by Envy.\n"
            f"- Key Points:\n"
            f"  1. {topic.title()} is identified as a priority for further investigation.\n"
            f"  2. Public open-source resources will be consulted when online access is enabled.\n"
            f"  3. Current offline mode uses curated knowledge snippets only.\n\n"
            f"Next Steps:\n"
            f"- Enable remote research connectors for deeper insights.\n"
            f"- Capture follow-up questions and schedule reminders if needed.\n"
        )

    def _slug(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


__all__ = ["ResearchSkill"]

