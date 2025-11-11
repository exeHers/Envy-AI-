from __future__ import annotations

import logging
import pathlib
from typing import Optional

from .config import load_config


_LOGGER: Optional[logging.Logger] = None


def get_logger(name: str = "envy") -> logging.Logger:
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER.getChild(name) if name != "envy" else _LOGGER

    config = load_config()
    runtime = config.get("runtime", {})
    logs_dir = pathlib.Path(runtime.get("logs_dir", "artifacts/logs"))
    logs_dir.mkdir(parents=True, exist_ok=True)
    logfile = logs_dir / "envy.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(logfile, encoding="utf-8"),
            logging.StreamHandler()
        ],
    )
    _LOGGER = logging.getLogger("envy")
    return _LOGGER.getChild(name) if name != "envy" else _LOGGER
