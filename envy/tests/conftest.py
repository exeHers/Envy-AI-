import asyncio
from pathlib import Path

import pytest

from envy.config import load_config
from envy.services import stt_service, skill_manager, tts_service


@pytest.fixture(scope="session")
def config():
    return load_config()


@pytest.fixture(scope="session")
def stt_app(config):
    return stt_service.create_app(config)


@pytest.fixture(scope="session")
def skill_app(config):
    return skill_manager.create_app(config)


@pytest.fixture(scope="session")
def tts_app(config):
    return tts_service.create_app(config)


@pytest.fixture(scope="session", autouse=True)
def ensure_test_artifacts():
    path = Path("artifacts/tests")
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def cleanup_workspace():
    target = Path("workspace/test.py")
    if target.exists():
        target.unlink()
    yield
    if target.exists():
        target.unlink()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
