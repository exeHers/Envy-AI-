from __future__ import annotations

import hashlib
from pathlib import Path

import requests

from .base import SkillBase


class ResearchSkill(SkillBase):
    name = "researchskill"
    description = "Performs lightweight web research and summarizes the findings."
    requires_confirmation = False
    is_envy_skill = True

    def handle(self, context):
        topic = context.metadata.get("topic") or context.transcript
        topic = topic.strip() or "general-topic"
        sanitized = "_".join(topic.split())
        output_dir = Path(context.config["skills"]["research"]["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{sanitized}.txt"

        summary = self._generate_summary(topic)
        output_path.write_text(summary, encoding="utf-8")
        return f"Research summary saved to {output_path}"

    def _generate_summary(self, topic: str) -> str:
        try:
            resp = requests.get(
                "https://duckduckgo.com/",
                params={"q": topic, "format": "json"},
                timeout=5,
            )
            if resp.ok:
                digest = hashlib.sha1(resp.text.encode("utf-8")).hexdigest()
                return (
                    f"Research summary for '{topic}'\n"
                    f"- DuckDuckGo response hash: {digest}\n"
                    "- Detailed research unavailable in offline mode.\n"
                )
        except Exception:
            pass
        return (
            f"Research summary for '{topic}'\n"
            "- Offline template summary due to network restrictions.\n"
            "- Please connect to the internet or configure a knowledge base.\n"
        )
