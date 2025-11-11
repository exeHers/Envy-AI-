"""
Service entry points for the Envy assistant.

Each submodule exposes a FastAPI application and supporting runtime code.
"""

from . import common  # noqa: F401

__all__ = [
    "wake_listener",
    "stt_service",
    "router",
    "skill_manager",
    "tts_service",
    "web_dashboard",
    "common",
]
