from __future__ import annotations

import json
from pathlib import Path

from envy.services.common.config import load_config, PROJECT_ROOT
from envy.services.router.intent_classifier import IntentClassifier
from envy.services.router.llm_adapter import LLMAdapter
from envy.services.stt_service.stt_engine import STTEngine
from envy.services.tts_service.tts_engine import TTSEngine
from envy.services.wake_listener.wake_detector import WakeDetector
from envy.skills.base import SkillRequest
from envy.skills.code_skill import CodeSkill

ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "tests"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = ARTIFACT_DIR / "acceptance-log.jsonl"


def log_event(name: str, **payload):
    record = {"event": name, **payload}
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def test_wake_word_detection():
    config = load_config()
    detector = WakeDetector(config)
    audio_path = PROJECT_ROOT / "tests" / "assets" / "audio" / "wake_only.wav"
    assert detector.detect_from_file(audio_path) is True
    log_event("wake_word", audio=str(audio_path))


def test_code_skill_creates_file(tmp_path):
    config = load_config()
    stt = STTEngine(config)
    classifier = IntentClassifier(config)
    code_skill = CodeSkill(config)
    code_skill.setup()

    audio_path = PROJECT_ROOT / "tests" / "assets" / "audio" / "wake_create_test.wav"
    transcription = stt.transcribe_file(audio_path)
    log_event("stt", text=transcription.text, engine=transcription.engine)

    intent = classifier.classify(transcription.text)
    log_event("intent", intent=intent.intent, skill=intent.skill, parameters=intent.parameters)

    # Clean up target file before test
    target_relative = config.get("tests.expected_code_skill_file", "workspace/test.py")
    target_path = (PROJECT_ROOT / target_relative).resolve()
    if target_path.exists():
        target_path.unlink()

    request = SkillRequest(
        session_id="test-session",
        intent=intent.intent,
        transcript=transcription.text,
        parameters=intent.parameters,
    )
    response = code_skill.handle(request)
    assert response.success is True
    assert target_path.exists()
    content = target_path.read_text(encoding="utf-8")
    assert "hello from envy" in content
    log_event("code_skill", path=str(target_path), content=content.strip())


def test_tts_generates_audio(tmp_path):
    config = load_config()
    tts = TTSEngine(config)
    result = tts.synthesize("Envy reporting in.", session_id="pytest")
    audio_path = Path(result["path"])
    assert audio_path.exists()
    assert audio_path.stat().st_size > 0
    log_event("tts", path=str(audio_path), engine=result["engine"])


def test_llm_rule_based_fallback():
    config = load_config()
    llm = LLMAdapter(config)
    response = llm.respond("Tell me a joke", {"intent": "fallback.chat"})
    assert isinstance(response["text"], str)
    assert response["text"]
    log_event("llm_fallback", engine=response["engine"], text=response["text"])
