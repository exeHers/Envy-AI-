from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, Set

from .config import EnvyConfig
from .logging import get_logger


@dataclass
class PendingAction:
    action_id: str
    intent: str
    description: str
    required_channels: Set[str] = field(default_factory=set)
    confirmed_channels: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    timeout_seconds: int = 45

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.timeout_seconds

    def confirm(self, channel: str) -> None:
        self.confirmed_channels.add(channel)

    def is_fully_confirmed(self) -> bool:
        return self.required_channels.issubset(self.confirmed_channels)


class SecurityManager:
    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self.logger = get_logger("SecurityManager", config=config)
        self.pending: Dict[str, PendingAction] = {}

    def requires_confirmation(self, intent: str, transcript: str) -> bool:
        destructive_keywords = set(self.config.get("skills.destructive_keywords", []))
        for keyword in destructive_keywords:
            if keyword.lower() in transcript.lower():
                return True
        double_confirm = set(self.config.get("skills.requires_double_confirmation", []))
        return intent in double_confirm

    def create_pending(self, intent: str, description: str) -> PendingAction:
        action_id = str(uuid.uuid4())
        required_channels = set()
        if self.config.get("security.voice_confirmation", True):
            required_channels.add("voice")
        if self.config.get("security.dashboard_confirmation", True):
            required_channels.add("dashboard")
        timeout = self.config.get("security.confirmation_timeout_seconds", 45)
        pending = PendingAction(
            action_id=action_id,
            intent=intent,
            description=description,
            required_channels=required_channels,
            timeout_seconds=timeout,
        )
        self.pending[action_id] = pending
        self.logger.info(f"Created pending action {action_id} requiring {required_channels}")
        return pending

    def confirm(self, action_id: str, channel: str) -> bool:
        pending = self.pending.get(action_id)
        if not pending:
            raise KeyError(f"Unknown pending action {action_id}")
        if pending.is_expired():
            self.pending.pop(action_id, None)
            raise TimeoutError(f"Pending action {action_id} expired")
        pending.confirm(channel)
        self.logger.info(f"Action {action_id} confirmed by {channel}")
        if pending.is_fully_confirmed():
            self.pending.pop(action_id, None)
            self.logger.info(f"Action {action_id} fully confirmed")
            return True
        return False

    def cleanup(self) -> None:
        expired = [action_id for action_id, pending in self.pending.items() if pending.is_expired()]
        for action_id in expired:
            self.logger.warning(f"Cleaning up expired action {action_id}")
            self.pending.pop(action_id, None)


__all__ = ["SecurityManager", "PendingAction"]
