from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from .config import EnvyConfig, load_config


def _config_profile() -> Optional[str]:
    return os.getenv("ENVY_PROFILE")


def _config_path() -> Optional[str]:
    return os.getenv("ENVY_CONFIG_PATH")


@lru_cache(maxsize=1)
def _cached_config() -> EnvyConfig:
    return load_config(
        path=_config_path() or None,
        profile=_config_profile() or None,
    )


def get_config() -> EnvyConfig:
    return _cached_config()


def verify_secret(
    secret: Optional[str] = Header(default=None, alias="x-envy-secret"),
    config: EnvyConfig = Depends(get_config),
) -> None:
    expected = config.get("messaging.shared_secret", "change-me-envy")
    if expected and secret != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid shared secret")


__all__ = ["get_config", "verify_secret"]
