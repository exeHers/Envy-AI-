"""Utility helpers for spawning and supervising subprocesses."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


def python_entrypoint(module: str, args: Optional[List[str]] = None, env: Optional[Dict[str, str]] = None) -> subprocess.Popen:
    cmd = [sys.executable, "-m", module]
    if args:
        cmd.extend(args)
    return subprocess.Popen(cmd, env=env)


def ensure_executable(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    mode = path.stat().st_mode
    path.chmod(mode | 0o111)

