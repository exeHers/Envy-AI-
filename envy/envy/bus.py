from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Event:
    type: str
    payload: Dict[str, Any]


class EventBus:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers: Dict[str, list[asyncio.Queue[Event]]] = {}

    async def publish(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        event = Event(type=event_type, payload=payload or {})
        await self._queue.put(event)
        for queue in self._subscribers.get(event_type, []):
            await queue.put(event)

    async def subscribe(self, event_type: str) -> asyncio.Queue[Event]:
        queue: asyncio.Queue[Event] = asyncio.Queue()
        self._subscribers.setdefault(event_type, []).append(queue)
        return queue

    async def next_event(self) -> Event:
        return await self._queue.get()
