#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
ARTIFACTS_DIR="${ROOT_DIR}/artifacts/tests"
LOG_FILE="${ARTIFACTS_DIR}/acceptance.log"

mkdir -p "${ARTIFACTS_DIR}"

if [ ! -d "${VENV_DIR}" ]; then
  echo "Virtual environment missing. Run install_envy.sh first." | tee "${LOG_FILE}"
  exit 1
fi

source "${VENV_DIR}/bin/activate"

run_step() {
  local name="$1"
  shift
  echo "== ${name} ==" | tee -a "${LOG_FILE}"
  "$@" | tee -a "${LOG_FILE}"
}

run_step "Wake Word Test" python - <<'PY'
from pathlib import Path
from envy.config import load_config
from envy.wake_listener import WakeListener, WakeEvent
import asyncio

async def main():
    config = load_config()
    detected = []
    async def on_detect(event: WakeEvent):
        detected.append(event)
    listener = WakeListener(config, on_detect)
    sample = Path("tests/data/wake_test.txt")
    await listener.detect_from_audio_file(sample)
    print("wake_detected=", bool(detected))

asyncio.run(main())
PY

run_step "Code Skill Test" python -m envy.cli simulate --transcript "Envy, create test.py that prints hello from envy"
run_step "Research Skill Test" python -m envy.cli simulate --transcript "Envy, research local models"
run_step "TTS Check" python - <<'PY'
from envy.config import load_config
from envy.services.orchestrator import AssistantRuntime
import asyncio

async def main():
    runtime = AssistantRuntime(load_config())
    await runtime.tts.speak("Acceptance test synthesis", filename="acceptance.wav", play_audio=False)
    print("tts_ready=True")

asyncio.run(main())
PY

echo "Acceptance run complete. Logs at ${LOG_FILE}"
