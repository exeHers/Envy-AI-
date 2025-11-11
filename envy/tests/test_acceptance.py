import asyncio
from pathlib import Path

import pytest

from envy.config import load_config
from envy.llm_adapter import LLMAdapter
from envy.services.orchestrator import AssistantRuntime
from envy.wake_listener import WakeListener, WakeEvent


@pytest.mark.asyncio
async def test_wake_word_detection():
    config = load_config()
    events: list[WakeEvent] = []

    async def on_detect(event: WakeEvent) -> None:
        events.append(event)

    listener = WakeListener(config, on_detect)
    sample_path = Path(__file__).parent / "data" / "wake_test.txt"
    event = await listener.detect_from_audio_file(sample_path)
    assert event is not None
    assert events, "Expected wake listener to emit an event."


@pytest.mark.asyncio
async def test_code_skill_creates_workspace_file(tmp_path):
    config = load_config()
    runtime = AssistantRuntime(config)
    transcript = "Envy, create test.py that prints hello from envy"
    outcome = await runtime.simulate_session(transcript)
    assert outcome.success, outcome.message
    target = Path("workspace") / "test.py"
    assert target.exists()
    assert 'hello from envy' in target.read_text()


@pytest.mark.asyncio
async def test_research_skill_creates_summary():
    config = load_config()
    runtime = AssistantRuntime(config)
    topic = "Envy, research local models"
    outcome = await runtime.simulate_session(topic)
    assert outcome.success
    research_dir = config.artifacts_dir / "research"
    files = list(research_dir.glob("*.txt"))
    assert files, "Expected research summary file."


@pytest.mark.asyncio
async def test_tts_output_generated():
    config = load_config()
    runtime = AssistantRuntime(config)
    await runtime.tts.speak("Testing one two three", filename="test-output.wav", play_audio=False)
    tts_dir = config.artifacts_dir / "tts"
    assert any(tts_dir.iterdir()), "Expected TTS artifacts to exist."


@pytest.mark.asyncio
async def test_llm_rule_fallback():
    config = load_config()
    adapter = LLMAdapter(config)
    result = await adapter.generate("Greet the user briefly.")
    assert result.text
    assert result.backend in {"rule", "llama_cpp", "remote"}
