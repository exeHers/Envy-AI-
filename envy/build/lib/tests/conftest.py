from __future__ import annotations

import json
from pathlib import Path
from typing import Generator

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
TEST_ARTIFACTS = ARTIFACTS_DIR / "tests"
MODELS_DIR = ROOT_DIR / "models" / "vosk-model-small-en-us-0.15"


@pytest.fixture(scope="session", autouse=True)
def ensure_artifact_dirs() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    TEST_ARTIFACTS.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def ensure_models() -> None:
    if not MODELS_DIR.exists():
        raise RuntimeError(
            "Vosk model missing. Run scripts/download_models.sh before executing tests."
        )


@pytest.fixture(autouse=True)
def record_test_log(request) -> Generator[None, None, None]:
    log_path = TEST_ARTIFACTS / f"{request.node.name}.json"
    payload = {"test": request.node.name, "status": "running"}
    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    yield
    payload["status"] = "passed"
    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@pytest.fixture
def sample_audio_paths() -> dict[str, Path]:
    wake = ROOT_DIR / "data" / "audio_samples" / "wake_envy.wav"
    command = ROOT_DIR / "data" / "audio_samples" / "command_create_test.wav"
    return {"wake": wake, "command": command}
