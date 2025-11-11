import asyncio
from pathlib import Path
from typing import Dict
from urllib.parse import urlparse

import httpx
import pytest

from envy.config import EnvyConfig
from envy.services.router_service import AudioCommandRequest, RouterService, TextCommandRequest
from envy.services.stt_service import STTEngine
from envy.services.wake_listener import WakeDetector


class LocalAsyncClient:
    """Route httpx requests directly to ASGI apps without network sockets."""

    def __init__(self, app_map: Dict[str, object]):
        self.app_map = app_map

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        parsed = urlparse(url)
        key = f"{parsed.hostname}:{parsed.port}"
        app = self.app_map.get(key)
        if not app:
            raise RuntimeError(f"No ASGI app registered for {key}")
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url=f"http://{key}") as client:
            return await client.request(method, parsed.path, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def aclose(self):
        return


def append_log(message: str) -> None:
    log_path = Path("artifacts/tests/acceptance.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def service_client(config: EnvyConfig, stt_app, skill_app, tts_app) -> LocalAsyncClient:
    mapping = {
        f"{config.services['stt'].host}:{config.services['stt'].port}": stt_app,
        f"{config.services['skill_manager'].host}:{config.services['skill_manager'].port}": skill_app,
        f"{config.services['tts'].host}:{config.services['tts'].port}": tts_app,
    }
    return LocalAsyncClient(mapping)


def test_wake_word_detection(config):
    detector = WakeDetector(config)
    audio_path = Path("assets/audio/wake_demo.wav")
    triggered, confidence, transcript = detector.detect_from_file(audio_path)
    append_log(f"Wake detection -> triggered={triggered} confidence={confidence:.2f} transcript='{transcript}'")
    assert triggered
    assert "envy" in transcript.lower()


def test_stt_transcription(config):
    engine = STTEngine(config)
    audio_path = Path("assets/audio/command_create_test.wav")
    response = engine.transcribe_file(audio_path, stream=True)
    append_log(f"STT transcript: {response.text}")
    assert "create test.py" in response.text
    assert response.source in {"vosk", "transcript-cache"}


@pytest.mark.asyncio
async def test_code_skill_pipeline(config, stt_app, skill_app, tts_app, cleanup_workspace):
    client = service_client(config, stt_app, skill_app, tts_app)
    router = RouterService(config, client=client)
    audio_path = Path("assets/audio/command_create_test.wav")
    result = await router.process_audio(AudioCommandRequest(audio_path=str(audio_path)))

    append_log(f"Router response (code skill): intent={result['intent']} tts_engine={result['tts'].get('engine')}")

    skill_result = result["skill_result"]
    created_file = Path(skill_result["artifacts"]["created_file"])
    assert created_file.exists()
    assert 'hello from envy' in created_file.read_text(encoding="utf-8")

    tts_info = result["tts"]
    assert "audio_path" in tts_info
    tts_path = Path(tts_info["audio_path"])
    assert tts_path.exists()


@pytest.mark.asyncio
async def test_research_skill_pipeline(config, stt_app, skill_app, tts_app):
    client = service_client(config, stt_app, skill_app, tts_app)
    router = RouterService(config, client=client)

    text_request = TextCommandRequest(text="Envy, research local greenhouse designs")
    result = await router.process_text(text_request)

    append_log(f"Research skill result: {result['skill_result']['status']}")

    summary_path = Path(result["skill_result"]["artifacts"]["summary_file"])
    assert summary_path.exists()
    content = summary_path.read_text(encoding="utf-8")
    assert "Research Summary" in content
    assert "greenhouse" in content.lower()

