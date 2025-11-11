from __future__ import annotations

from pathlib import Path

from envy.assistant import AssistantEngine, bootstrap_assistant


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_wake_word_and_code_skill(tmp_path) -> None:
    repo_root = get_repo_root()
    overrides = {"security": {"sandbox_workdir": "test_workspace"}}
    assistant = bootstrap_assistant(
        repo_root=repo_root,
        config_path=repo_root / "config" / "envy.yaml",
        profile="balanced",
        overrides=overrides,
        with_dashboard=False,
    )

    audio_file = repo_root / "tests" / "data" / "wake_command.wav"
    workspace_dir = repo_root / "test_workspace"
    if workspace_dir.exists():
        for item in workspace_dir.iterdir():
            if item.is_file():
                item.unlink()

    result = assistant.process_audio_file(audio_file, auto_confirm=True)

    created_file = workspace_dir / "test.py"
    assert result.wake_detected is True
    assert created_file.exists()
    assert 'hello from envy' in created_file.read_text(encoding="utf-8")
    assert result.tts_path is not None and result.tts_path.exists()
    assert result.used_llm is False


def test_llm_fallback_response() -> None:
    repo_root = get_repo_root()
    overrides = {"security": {"sandbox_workdir": "test_workspace"}}
    assistant = bootstrap_assistant(
        repo_root=repo_root,
        config_path=repo_root / "config" / "envy.yaml",
        profile="balanced",
        overrides=overrides,
        with_dashboard=False,
    )

    router_result = assistant.router.handle("explain the mission status")
    assert router_result.used_llm is True
    assert "Envy" in router_result.response
