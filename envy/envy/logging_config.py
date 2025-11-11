"""Logging utilities for Envy services."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from .config import EnvyConfig


def configure_logging(config: EnvyConfig, service_name: str, level: int = logging.INFO) -> None:
    """Configure Python logging for a specific service."""
    artifacts_dir = config.artifacts_path
    log_dir = artifacts_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{service_name}.log"

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def get_logger(name: str, level: int = logging.INFO, log_file: Optional[Path] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(handler)
    return logger

