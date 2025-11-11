from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.logging import RichHandler

DEFAULT_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_BACKUP_COUNT = 3


def setup_logging(settings: Dict[str, Any]) -> None:
    """Configure rich console logging and optional file logs."""

    level_name = settings.get("level", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)

    handlers: list[logging.Handler] = [
        RichHandler(
            console=Console(stderr=True),
            show_time=True,
            log_time_format="[%X]",
            markup=True,
            rich_tracebacks=True,
        )
    ]

    log_file = settings.get("file")
    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                path,
                maxBytes=int(settings.get("max_bytes", DEFAULT_MAX_BYTES)),
                backupCount=int(settings.get("backup_count", DEFAULT_BACKUP_COUNT)),
            )
        )

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )

    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.getLogger(__name__).debug("Logging configured at %s", level_name)
