from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def prepare_models() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "download_models.sh"
    subprocess.run(["bash", str(script), "--profile", "balanced"], check=True, cwd=repo_root)
