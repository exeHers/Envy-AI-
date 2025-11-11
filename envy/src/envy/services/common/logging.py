from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import sys

from loguru import logger

from .config import EnvyConfig, PROJECT_ROOT


_LOGGER_CONFIGURED = False


def _configure_logger(config: Optional[EnvyConfig]) -> None:
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return

    log_level = (config.get("logging.level", "INFO") if config else "INFO").upper()
    logs_dir = (
        Path(config.get("runtime.logs_dir", "artifacts/logs"))
        if config
        else PROJECT_ROOT / "artifacts" / "logs"
    )
    logs_dir = (PROJECT_ROOT / logs_dir).resolve() if not logs_dir.is_absolute() else logs_dir
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(sys.stderr, level=log_level, colorize=True)
    log_file = logs_dir / "envy.log"
    rotation_mb = config.get("logging.rotation_mb", 10) if config else 10
    retention_days = config.get("logging.retention_days", 14) if config else 14
    logger.add(
        log_file,
        level=log_level,
        rotation=f"{rotation_mb} MB",
        retention=f"{retention_days} days",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )

    logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
    _LOGGER_CONFIGURED = True


def get_logger(name: str, config: Optional[EnvyConfig] = None):
    _configure_logger(config)
    return logger.bind(component=name)


__all__ = ["get_logger"]
