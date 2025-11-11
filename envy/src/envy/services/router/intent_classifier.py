from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional

from ..common.config import EnvyConfig
from ..common.logging import get_logger


@dataclass
class IntentResult:
    intent: str
    skill: Optional[str]
    confidence: float
    parameters: Dict[str, str]


class IntentClassifier:
    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self.logger = get_logger("IntentClassifier", config=config)

    def classify(self, transcript: str) -> IntentResult:
        text = transcript.lower()
        if not text.strip():
            return IntentResult(intent="fallback.idle", skill=None, confidence=0.0, parameters={})

        if "remind" in text or "reminder" in text:
            reminder_text = transcript.split("remind", 1)[-1].strip() or transcript
            return IntentResult(
                intent="reminder.add",
                skill="reminder_skill",
                confidence=0.8,
                parameters={"text": reminder_text},
            )

        if "research" in text:
            topic_match = re.search(r"research\s+(?P<topic>.+)", transcript, re.IGNORECASE)
            topic = topic_match.group("topic").strip() if topic_match else transcript
            return IntentResult(
                intent="research.summary",
                skill="research_skill",
                confidence=0.85,
                parameters={"topic": topic},
            )

        if "shutdown" in text or "restart" in text or "reboot" in text:
            command = "shutdown" if "shutdown" in text else "reboot"
            return IntentResult(
                intent="sys_control.execute",
                skill="sys_control_skill",
                confidence=0.9,
                parameters={"command": command},
            )

        if "create" in text and ".py" in text:
            match = re.search(r"create\s+(?P<file>[\w./-]+\.py)", transcript, re.IGNORECASE)
            file_path = match.group("file") if match else "workspace/test.py"
            return IntentResult(
                intent="code.create_file",
                skill="code_skill",
                confidence=0.95,
                parameters={"file_path": file_path},
            )

        if "list reminders" in text:
            return IntentResult("reminder.list", "reminder_skill", 0.7, {})

        self.logger.debug(f"Defaulting to fallback intent for transcript: {transcript}")
        return IntentResult(intent="fallback.chat", skill=None, confidence=0.5, parameters={})


__all__ = ["IntentClassifier", "IntentResult"]
