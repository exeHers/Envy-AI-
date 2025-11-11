from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import psutil

from envy.services.common.config import PROJECT_ROOT, load_config
from envy.services.router.intent_classifier import IntentClassifier
from envy.services.router.llm_adapter import LLMAdapter
from envy.services.stt_service.stt_engine import STTEngine
from envy.services.tts_service.tts_engine import TTSEngine
from envy.services.wake_listener.wake_detector import WakeDetector
from envy.skills.base import SkillRequest
from envy.skills.code_skill import CodeSkill

REPORT_PATH = PROJECT_ROOT / "artifacts" / "perf-report.txt"


def sample_gpu() -> Dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,utilization.memory,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        values = result.stdout.strip().split(",")
        if len(values) >= 4:
            gpu_util, mem_util, mem_used, mem_total = [v.strip() for v in values[:4]]
            return {
                "gpu_util_percent": float(gpu_util),
                "gpu_memory_util_percent": float(mem_util),
                "gpu_memory_used_mb": float(mem_used),
                "gpu_memory_total_mb": float(mem_total),
            }
    except Exception:  # noqa: BLE001
        pass
    return {"gpu_available": False}


def run_session(config) -> Dict[str, Any]:
    wake = WakeDetector(config)
    stt = STTEngine(config)
    classifier = IntentClassifier(config)
    code_skill = CodeSkill(config)
    code_skill.setup()
    tts = TTSEngine(config)
    llm = LLMAdapter(config)

    audio_path = PROJECT_ROOT / "tests" / "assets" / "audio" / "wake_create_test.wav"
    start = time.perf_counter()
    wake_detected = wake.detect_from_file(audio_path)
    stt_result = stt.transcribe_file(audio_path)
    intent = classifier.classify(stt_result.text)
    skill_response = code_skill.handle(
        SkillRequest(
            session_id="perf",
            intent=intent.intent,
            transcript=stt_result.text,
            parameters=intent.parameters,
        )
    )
    llm_response = llm.respond("Status report", {"intent": "fallback.chat"})
    tts_result = tts.synthesize("Performance run complete.", session_id="perf")
    duration = time.perf_counter() - start

    return {
        "wake_detected": wake_detected,
        "transcript": stt_result.text,
        "intent": intent.intent,
        "skill_success": skill_response.success,
        "llm_engine": llm_response["engine"],
        "tts_engine": tts_result["engine"],
        "duration_seconds": duration,
    }


def main() -> None:
    config = load_config()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    cpu_before = psutil.cpu_percent(interval=None)
    mem_before = psutil.virtual_memory()._asdict()

    session_data = run_session(config)

    cpu_after = psutil.cpu_percent(interval=None)
    mem_after = psutil.virtual_memory()._asdict()
    gpu_data = sample_gpu()

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "profile": config.profile,
        "cpu_before_percent": cpu_before,
        "cpu_after_percent": cpu_after,
        "memory_before": mem_before,
        "memory_after": mem_after,
        "gpu": gpu_data,
        "session": session_data,
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[perf] Report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
