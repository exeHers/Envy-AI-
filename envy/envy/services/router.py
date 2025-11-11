from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from envy.services.llm_adapter import LLMAdapter
from envy.services.skill_manager import SkillManager
from envy.skills.base import SkillResult

LOGGER = logging.getLogger(__name__)


@dataclass
class RouterResult:
    response: str
    used_llm: bool
    skill_result: SkillResult


class ConversationRouter:
    def __init__(self, skill_manager: SkillManager, llm_adapter: LLMAdapter) -> None:
        self.skill_manager = skill_manager
        self.llm_adapter = llm_adapter
        self.conversation: List[dict] = []

    def handle(self, command: str) -> RouterResult:
        LOGGER.info("Router handling command: %s", command)
        skill_result = self.skill_manager.dispatch(command)
        used_llm = False
        response_text = skill_result.response

        if not skill_result.handled:
            LOGGER.info("No skill handled command; invoking LLM adapter.")
            response_text = self.llm_adapter.generate(self.conversation, command)
            used_llm = True

        self.conversation.append({"role": "user", "content": command})
        self.conversation.append({"role": "assistant", "content": response_text})

        LOGGER.info("Router produced response (LLM=%s): %s", used_llm, response_text)

        return RouterResult(
            response=response_text,
            used_llm=used_llm,
            skill_result=skill_result,
        )
