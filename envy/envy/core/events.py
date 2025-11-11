from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable, DefaultDict, List

EventCallback = Callable[[dict], Awaitable[None]]


class EventBus:
    """Simple in-process Pub/Sub event bus used by the router."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[EventCallback]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, event_type: str, payload: dict) -> None:
        async with self._lock:
            subscribers = list(self._subscribers[event_type])
        await asyncio.gather(*(subscriber(payload) for subscriber in subscribers), return_exceptions=True)

    async def subscribe(self, event_type: str, callback: EventCallback) -> None:
        async with self._lock:
            self._subscribers[event_type].append(callback)

    async def unsubscribe(self, event_type: str, callback: EventCallback) -> None:
        async with self._lock:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
