from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from .base import Skill, SkillContext, SkillResult

LOGGER = logging.getLogger(__name__)


class ResearchSkill(Skill):
    name = "research"
    description = "Collect quick desk research and save summaries."

    def can_handle(self, command: str) -> bool:
        lowered = command.lower()
        return "research" in lowered or "investigate" in lowered

    def execute(self, command: str, context: SkillContext) -> SkillResult:
        LOGGER.info("ResearchSkill handling command: %s", command)
        topic = command.split("research", 1)[-1].strip() or "topic"
        slug = "".join(ch for ch in topic.lower().replace(" ", "-") if ch.isalnum() or ch == "-")

        research_dir = context.artifacts_dir / "research"
        research_dir.mkdir(parents=True, exist_ok=True)
        summary_path = research_dir / f"{slug or 'summary'}.md"

        summary = (
            f"# Research summary: {topic}\n\n"
            f"- Generated: {datetime.utcnow().isoformat()}Z\n"
            "- Sources: Offline knowledge base placeholder.\n"
            "- Highlights: Envy captured key talking points for quick review.\n"
            "\n"
            "This is a stub summary. Connect a remote or local knowledge service to enrich it.\n"
        )
        summary_path.write_text(summary, encoding="utf-8")

        LOGGER.info("Research summary saved to %s", summary_path)

        return SkillResult(
            handled=True,
            response=f"Research summary stored at {summary_path.name}.",
            artifacts=[summary_path],
        )
