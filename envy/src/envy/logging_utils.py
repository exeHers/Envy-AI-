"""
Shared logging configuration helpers.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional


def setup_logging(level: str = "INFO", log_dir: Optional[Path] = None, service_name: str = "envy") -> None:
    """
    Configure structured logging for Envy services.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )

    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        service_log = log_dir / f"{service_name}.log"
        file_handler = logging.FileHandler(service_log, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        logging.getLogger().addHandler(file_handler)

    logging.getLogger("uvicorn").setLevel(os.environ.get("UVICORN_LOG_LEVEL", "WARNING").upper())
    logging.getLogger("asyncio").setLevel(logging.WARNING)
