from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any, Dict

from envy.bus import EventBus
from envy.config import Config


class ServiceBase:
    name = "service"

    def __init__(self, config: Config, bus: EventBus):
        self.config = config
        self.bus = bus
        self.logger = logging.getLogger(self.name)
        self._task: asyncio.Task[Any] | None = None

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self.logger.info("Starting service")
        self._task = asyncio.create_task(self.run(), name=f"{self.name}-task")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self.logger.info("Service stopped")

    async def run(self) -> None:  # pragma: no cover - to be implemented by subclass
        raise NotImplementedError
