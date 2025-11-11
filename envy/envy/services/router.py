from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from envy.bus import EventBus
from envy.config import Config
from envy.services.base import ServiceBase
from envy.services.llm_adapter import LLMAdapter

LOGGER = logging.getLogger("router_service")


class RouterService(ServiceBase):
    name = "router_service"

    def __init__(self, config: Config, bus: EventBus, llm: LLMAdapter):
        super().__init__(config, bus)
        self.llm = llm
        self._pending_confirmations: Dict[str, Dict[str, Any]] = {}

    async def run(self) -> None:
        transcript_queue = await self.bus.subscribe("stt.transcript")
        skill_result_queue = await self.bus.subscribe("skill.result")
        while True:
            transcript_task = asyncio.create_task(transcript_queue.get())
            skill_task = asyncio.create_task(skill_result_queue.get())
            done, pending = await asyncio.wait(
                [transcript_task, skill_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in done:
                event = task.result()
                if event.type == "stt.transcript":
                    await self._handle_transcript(event.payload)
                elif event.type == "skill.result":
                    await self._handle_skill_result(event.payload)

    async def _handle_transcript(self, payload: Dict[str, Any]) -> None:
        text = payload.get("text", "")
        transcript_id = payload.get("transcript_id")
        normalized = text.lower().strip()
        if normalized.startswith("envy"):
            normalized = normalized[len("envy") :].strip(",. ")

        if await self._check_voice_confirmation(normalized):
            return

        skill_name = self._classify(normalized)
        context = {
            "transcript_id": transcript_id,
            "raw_text": text,
            "wake_event": payload.get("wake_event", {}),
        }
        if skill_name:
            LOGGER.info("Routing instruction to skill %s", skill_name)
            await self.bus.publish(
                "skill.execute",
                {"skill": skill_name, "instruction": normalized, "context": context},
            )
            return

        llm_result = await self.llm.generate(normalized, context={"strategy": None})
        LOGGER.info("LLMAdapter (%s) responding with: %s", llm_result.strategy, llm_result.text)
        await self.bus.publish(
            "router.response",
            {
                "source": "llm",
                "skill": None,
                "text": llm_result.text,
                "strategy": llm_result.strategy,
                "used_remote": llm_result.used_remote,
                "context": context,
            },
        )

    async def _handle_skill_result(self, payload: Dict[str, Any]) -> None:
        status = payload.get("status")
        skill_name = payload.get("skill")
        message = payload.get("message", "")
        confirmation_id = payload.get("confirmation_id")

        if status == "pending_confirmation" and confirmation_id:
            LOGGER.info("Awaiting confirmation for %s (%s)", skill_name, confirmation_id)
            self._pending_confirmations[confirmation_id] = {
                "skill": skill_name,
                "message": message,
                "voice_confirmed": False,
            }
            await self.bus.publish(
                "router.response",
                {
                    "source": "skill",
                    "skill": skill_name,
                    "text": f"{message} Say 'confirm' and approve in the dashboard.",
                    "status": status,
                    "confirmation_id": confirmation_id,
                },
            )
            return

        if confirmation_id and confirmation_id in self._pending_confirmations:
            self._pending_confirmations.pop(confirmation_id, None)

        response_text = self._build_response_text(status, message, payload.get("data"))
        LOGGER.info("Skill %s completed with status=%s message=%s", skill_name, status, message)
        await self.bus.publish(
            "router.response",
            {
                "source": "skill",
                "skill": skill_name,
                "text": response_text,
                "status": status,
                "data": payload.get("data"),
            },
        )

    async def _check_voice_confirmation(self, text: str) -> bool:
        if not self._pending_confirmations:
            return False
        if text in {"confirm", "yes", "yes confirm", "go ahead", "please confirm"}:
            confirmation_id, info = next(iter(self._pending_confirmations.items()))
            if info.get("voice_confirmed"):
                await self.bus.publish(
                    "router.response",
                    {
                        "source": "security",
                        "text": "Voice confirmation already captured. Approve in the dashboard to proceed.",
                    },
                )
                return True
            info["voice_confirmed"] = True
            await self.bus.publish(
                "security.voice_confirmed",
                {"confirmation_id": confirmation_id, "skill": info["skill"]},
            )
            await self.bus.publish(
                "router.response",
                {
                    "source": "security",
                    "text": "Voice confirmation received. Complete the approval in the dashboard.",
                    "status": "voice_confirmed",
                    "confirmation_id": confirmation_id,
                },
            )
            return True
        return False

    def _classify(self, text: str) -> Optional[str]:
        lowered = text.lower()
        if any(token in lowered for token in ("create", "write", "make")) and ".py" in lowered:
            return "CodeSkill"
        if "research" in lowered or "study" in lowered or "summary" in lowered:
            return "ResearchSkill"
        if "remind" in lowered or "reminder" in lowered:
            return "ReminderSkill"
        if any(keyword in lowered for keyword in ("list files", "current directory", "show file", "delete", "shutdown")):
            return "SysControlSkill"
        return None

    def _build_response_text(self, status: str, message: str, data: Optional[Dict[str, Any]]) -> str:
        if status == "success":
            return message
        if status == "blocked":
            return message
        if status == "denied":
            return f"Action denied: {message}"
        if status == "error":
            return f"Something went wrong: {message}"
        return message or "Action completed."
