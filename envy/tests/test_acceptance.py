from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .generate_test_audio import create_audio_samples

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_TEST_DIR = PROJECT_ROOT / "artifacts" / "tests"
ARTIFACT_TEST_DIR.mkdir(parents=True, exist_ok=True)
WORKSPACE_OUT = PROJECT_ROOT / "workspace"
WORKSPACE_OUT.mkdir(parents=True, exist_ok=True)

def test_end_to_end_voice_flow():
    create_audio_samples()

    wake = PROJECT_ROOT / "tests" / "audio" / "wake_envy.wav"
    command_create = PROJECT_ROOT / "tests" / "audio" / "command_create_test.wav"
    command_smalltalk = PROJECT_ROOT / "tests" / "audio" / "command_smalltalk.wav"

    # Ensure clean state
    target_file = WORKSPACE_OUT / "test.py"
    if target_file.exists():
        target_file.unlink()

    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    cmd = [
        sys.executable,
        "-m",
        "envy.main",
        "--profile",
        "balanced",
        "--no-gui",
        "--once",
        "--simulation-grace",
        "8",
        "--simulate-audio",
        f"{wake}:{command_create}",
        "--simulate-audio",
        f"{wake}:{command_smalltalk}",
    ]

    process = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )

    log_path = ARTIFACT_TEST_DIR / "acceptance-run.log"
    log_path.write_text(process.stdout + "\n--- STDERR ---\n" + process.stderr, encoding="utf-8")

    assert process.returncode == 0, f"Runtime exited with {process.returncode}: see {log_path}"

    envy_log = (PROJECT_ROOT / "logs" / "envy.log").read_text(encoding="utf-8")
    wake_detected = "Wake word detected" in envy_log
    tts_output = PROJECT_ROOT / "artifacts" / "tts-output.wav"
    llm_used = "LLMAdapter" in envy_log

    assert wake_detected, "Wake word should be detected and logged."
    assert target_file.exists(), "CodeSkill must create workspace/test.py"
    assert 'print("hello from envy")' in target_file.read_text(encoding="utf-8")
    assert tts_output.exists(), "TTS output artifact missing"
    assert llm_used, "LLM adapter response not detected in logs"

    results = {
        "wake_detected": wake_detected,
        "code_skill_file": str(target_file),
        "tts_output": str(tts_output),
        "llm_used": llm_used,
        "log_file": str(log_path),
    }
    (ARTIFACT_TEST_DIR / "acceptance_results.json").write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )
