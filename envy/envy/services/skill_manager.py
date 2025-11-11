from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict
from uuid import uuid4

from envy.bus import EventBus
from envy.config import Config
from envy.services.base import ServiceBase
from skills import Skill, SkillResult, available_skills

LOGGER = logging.getLogger("skill_manager")


class SkillManagerService(ServiceBase):
    name = "skill_manager"

    def __init__(self, config: Config, bus: EventBus):
        super().__init__(config, bus)
        self._skills: Dict[str, Skill] = {}
        self._pending: Dict[str, Dict[str, Any]] = {}
        self._semaphore = asyncio.Semaphore(config.get("max_parallel_skills", 1))

    def _get_skill(self, skill_name: str) -> Skill:
        if skill_name not in self._skills:
            registry = available_skills()
            if skill_name not in registry:
                raise ValueError(f"Skill '{skill_name}' not registered.")
            self._skills[skill_name] = registry[skill_name](self.config.data.get("skills", {}))
        return self._skills[skill_name]

    async def run(self) -> None:
        execute_queue = await self.bus.subscribe("skill.execute")
        confirm_queue = await self.bus.subscribe("security.confirmed")
        while True:
            execute_task = asyncio.create_task(execute_queue.get())
            confirm_task = asyncio.create_task(confirm_queue.get())
            done, pending = await asyncio.wait(
                [execute_task, confirm_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in done:
                event = task.result()
                if event.type == "skill.execute":
                    await self._handle_execute(event.payload)
                elif event.type == "security.confirmed":
                    await self._handle_confirmation(event.payload)

    async def _handle_execute(self, payload: Dict[str, Any]) -> None:
        skill_name = payload["skill"]
        instruction = payload["instruction"]
        context = payload.get("context", {})
        force = payload.get("force", False)
        confirmation_id = payload.get("confirmation_id")
        LOGGER.info("Executing skill %s", skill_name)

        skill_context = dict(context)
        skill_context["force"] = force

        async with self._semaphore:
            try:
                skill = self._get_skill(skill_name)
                result: SkillResult = await asyncio.to_thread(skill.handle, instruction, skill_context)
            except Exception as exc:  # pragma: no cover - execution
                LOGGER.exception("Skill execution failed: %s", exc)
                await self.bus.publish(
                    "skill.result",
                    {
                        "skill": skill_name,
                        "status": "error",
                        "message": str(exc),
                        "context": context,
                    },
                )
                return

        if result.requires_confirmation and not force:
            confirmation_id = confirmation_id or str(uuid4())
            self._pending[confirmation_id] = {
                "skill": skill_name,
                "instruction": instruction,
                "context": context,
            }
            await self.bus.publish(
                "security.confirmation_required",
                {
                    "confirmation_id": confirmation_id,
                    "skill": skill_name,
                    "instruction": instruction,
                    "message": result.message,
                },
            )
            await self.bus.publish(
                "skill.result",
                {
                    "skill": skill_name,
                    "status": "pending_confirmation",
                    "message": result.message,
                    "confirmation_id": confirmation_id,
                },
            )
            return

        if result.requires_confirmation and force:
            await self.bus.publish(
                "skill.result",
                {
                    "skill": skill_name,
                    "status": "denied",
                    "message": result.message,
                    "context": context,
                },
            )
            return

        if confirmation_id:
            self._pending.pop(confirmation_id, None)

        await self.bus.publish(
            "skill.result",
            {
                "skill": skill_name,
                "status": result.status,
                "message": result.message,
                "data": result.data or {},
                "context": context,
            },
        )

    async def _handle_confirmation(self, payload: Dict[str, Any]) -> None:
        confirmation_id = payload.get("confirmation_id")
        if not confirmation_id or confirmation_id not in self._pending:
            LOGGER.warning("Received confirmation for unknown action: %s", confirmation_id)
            return

        pending = self._pending.pop(confirmation_id)
        pending["force"] = True
        pending["confirmation_id"] = confirmation_id
        LOGGER.info("Re-executing skill %s after confirmation", pending["skill"])
        await self._handle_execute(pending)
