import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO", logs_dir: str | None = None) -> None:
    log_level_upper = log_level.upper()
    logging.basicConfig(
        level=getattr(logging, log_level_upper, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=_build_handlers(logs_dir),
    )


def _build_handlers(logs_dir: str | None):
    console_handler = logging.StreamHandler(sys.stdout)
    handlers = [console_handler]
    if logs_dir:
        Path(logs_dir).mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(Path(logs_dir) / "envy.log")
        file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        handlers.append(file_handler)
    return handlers
