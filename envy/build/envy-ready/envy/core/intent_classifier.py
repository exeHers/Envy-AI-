"""Simple keyword-based intent classifier."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class IntentResult:
    name: str
    confidence: float
    text: str


class IntentClassifier:
    """Rule-based intent classifier with deterministic behavior."""

    def classify(self, text: str) -> Optional[IntentResult]:
        lowered = text.lower().strip()
        if not lowered:
            return None
        if "create" in lowered and ".py" in lowered:
            return IntentResult("CodeSkill", 0.9, lowered)
        if lowered.startswith("research") or "research" in lowered:
            return IntentResult("ResearchSkill", 0.85, lowered)
        if "remind" in lowered or "reminder" in lowered:
            return IntentResult("ReminderSkill", 0.7, lowered)
        if "shutdown" in lowered or "restart" in lowered or "system" in lowered:
            return IntentResult("SysControlSkill", 0.6, lowered)
        return IntentResult("LLMResponse", 0.5, lowered)

