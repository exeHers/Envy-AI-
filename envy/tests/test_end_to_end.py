from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("ENVY_ROOT", str(ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.router import EnvyRouter


def test_audio_pipeline_creates_code(sample_audio_paths, ensure_models):
    router = EnvyRouter(profile="balanced")
    target_file = Path("test.py")
    if target_file.exists():
        target_file.unlink()

    result = router.handle_audio_session(
        sample_audio_paths["wake"],
        sample_audio_paths["command"],
        voice_confirmed=True,
        dashboard_confirmed=True,
    )

    assert result.wake_detected, "Wake word should be detected"
    assert "test.py" in result.skill_result["output"]
    assert target_file.exists(), "CodeSkill should create test.py in workspace root"
    contents = target_file.read_text(encoding="utf-8").strip()
    assert contents == 'print("hello from envy")'

    tts_path = Path(result.tts_path)
    assert tts_path.exists(), "TTS output must exist"

    provider = result.llm_response["provider"]
    assert provider in {"llama-cpp", "rule-based"}  # remote optional but off by default
