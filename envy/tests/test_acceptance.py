from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "tests"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
LOG_PATH = ARTIFACTS / f"acceptance-{int(time.time())}.log"


def _log(message: str) -> None:
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


@pytest.fixture(scope="session")
def envy_process():
    subprocess.run(["pkill", "-f", "envy.runtime.launcher"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    subprocess.run(["pkill", "-f", "uvicorn"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    cmd = ["./run_envy_local.sh", "--profile", "low", "--no-gui"]
    proc = subprocess.Popen(cmd, cwd=ROOT, preexec_fn=os.setsid)
    _log("Launched Envy process for tests.")
    base_url = "http://127.0.0.1:7000"
    client = httpx.Client(timeout=5.0)
    for _ in range(30):
        try:
            resp = client.get(f"{base_url}/health")
            if resp.status_code == 200:
                _log("Router health endpoint reachable.")
                break
        except httpx.HTTPError:
            time.sleep(1)
    else:
        proc.terminate()
        pytest.fail("Envy router did not start in time.")
    yield proc
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=10)
    except ProcessLookupError:
        pass
    subprocess.run(["pkill", "-f", "envy.runtime.launcher"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    subprocess.run(["pkill", "-f", "uvicorn"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    _log("Envy process terminated after tests.")


def test_wake_word_detection(envy_process):
    url = "http://127.0.0.1:7001/detect"
    with httpx.Client(timeout=10.0) as client, (ROOT / "data/test_wake.wav").open("rb") as audio:
        response = client.post(url, files={"file": ("test_wake.wav", audio, "audio/wav")})
    data = response.json()
    _log(f"Wake listener response: {data}")
    assert data["wake_detected"] is True
    log_file = ROOT / "logs" / "envy.log"
    if log_file.exists():
        contents = log_file.read_text(encoding="utf-8")
        assert "Wake word detected" in contents


def test_code_skill_pipeline(envy_process):
    router_url = "http://127.0.0.1:7000/process"
    audio_path = str((ROOT / "data/test_command_create.wav").resolve())
    with httpx.Client(timeout=30.0) as client:
        response = client.post(router_url, json={"audio_path": audio_path})
    data = response.json()
    _log(f"Router pipeline response: {json.dumps(data, indent=2)}")
    assert data["intent"] == "code"
    target = Path("/workspace/test.py")
    assert target.exists()
    content = target.read_text(encoding="utf-8").strip()
    assert content == 'print("hello from envy")'


def test_tts_output_created(envy_process):
    tts_file = ROOT / "artifacts" / "tts-output.wav"
    for _ in range(10):
        if tts_file.exists() and tts_file.stat().st_size > 0:
            break
        time.sleep(1)
    assert tts_file.exists()
    _log(f"TTS output located at {tts_file}")


def test_llm_fallback(envy_process):
    url = "http://127.0.0.1:7005/complete"
    payload = {"prompt": "Who are you?", "persona": "neutral"}
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, json=payload)
    data = response.json()
    _log(f"LLM adapter response: {data}")
    assert "Envy" in data["text"]
    assert data["provider"] in {"stub", "llama_cpp", "remote"}
