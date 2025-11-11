from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Dict

DEFAULT_LOGGING: Dict[str, object] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


def setup_logging(logs_dir: str) -> None:
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    config = dict(DEFAULT_LOGGING)
    file_handler_name = "file"
    config["handlers"][file_handler_name] = {
        "class": "logging.handlers.RotatingFileHandler",
        "level": "DEBUG",
        "formatter": "standard",
        "filename": str(Path(logs_dir) / "envy.log"),
        "maxBytes": 5 * 1024 * 1024,
        "backupCount": 2,
    }
    config["root"]["handlers"] = ["console", file_handler_name]
    logging.config.dictConfig(config)
