from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .skill_base import Skill, SkillResult


class ResearchSkill(Skill):
    name = "ResearchSkill"
    description = "Generates a concise research summary and stores it on disk."

    def handle(self, instruction: str, context: Dict[str, Any]) -> SkillResult:
        research_root = Path(self.config.get("research_root", "./workspace/research")).resolve()
        research_root.mkdir(parents=True, exist_ok=True)

        topic = self._extract_topic(instruction)
        if not topic:
            return SkillResult(
                status="failed",
                message="I could not determine the research topic. Please rephrase.",
            )

        slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
        summary_path = research_root / f"{slug}-summary.txt"
        summary = self._generate_summary(topic, context)
        summary_path.write_text(summary, encoding="utf-8")

        metadata_path = research_root / f"{slug}-meta.json"
        metadata = {"topic": topic, "summary_file": str(summary_path), "generated_at": datetime.utcnow().isoformat() + "Z"}
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        return SkillResult(
            status="success",
            message=f"Research summary saved to {summary_path}",
            data={"topic": topic, "summary_file": str(summary_path), "metadata_file": str(metadata_path)},
        )

    def _extract_topic(self, instruction: str) -> str:
        match = re.search(r"(?:research|study|summarize)\s+(?P<topic>.+)", instruction, re.IGNORECASE)
        if match:
            return match.group("topic").strip().rstrip(".")
        return instruction.strip()

    def _generate_summary(self, topic: str, context: Dict[str, Any]) -> str:
        summary_lines = [
            f"Research Topic: {topic}",
            "",
            "Key Findings:",
            "- This is a locally generated placeholder summary.",
            "- Replace this with deeper research using the optional remote connectors.",
            "",
            "Next Steps:",
            "- Use `scripts/download_models.sh` to enable richer LLM support.",
            "- Enable remote endpoints in `config/envy.yaml` if you opt in to free APIs.",
        ]
        return "\n".join(summary_lines)
