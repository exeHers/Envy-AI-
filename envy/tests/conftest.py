import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def configure_envy_config():
    os.environ.setdefault("ENVY_CONFIG_PATH", str(PROJECT_ROOT / "config" / "envy.yaml"))
    os.environ.setdefault("ENVY_PROFILE", "balanced")
    yield
