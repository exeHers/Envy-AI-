"""
Main orchestrator tying together wake detection, STT, routing, and TTS.
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import uvicorn

from ..config import EnvyConfig, load_config
from ..logging_utils import setup_logging
from ..llm_adapter import LLMAdapter
from ..router import RouterOutcome, SkillRouter
from ..stt_service import STTService
from ..tts_service import TTSService
from ..wake_listener import WakeEvent, WakeListener
from ..web.dashboard import DashboardState, create_app

_LOGGER = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import sounddevice as sd
except (ImportError, OSError):  # pragma: no cover - optional dependency
    sd = None  # type: ignore


@dataclass
class CommandInput:
    kind: str  # "text" OR "audio_file"
    payload: str


class AssistantRuntime:
    def __init__(self, config: Optional[EnvyConfig] = None) -> None:
        self.config = config or load_config()
        setup_logging(log_dir=self.config.artifacts_dir / "logs", service_name="envy")

        self.tts = TTSService(self.config.artifacts_dir)
        self.llm = LLMAdapter(self.config)
        self.router = SkillRouter(self.config, self.llm, skills_path=self.config.custom_skills_dir)
        self.stt = STTService(self.config)
        self._wake_queue: "asyncio.Queue[WakeEvent]" = asyncio.Queue()
        self._command_queue: "asyncio.Queue[CommandInput]" = asyncio.Queue()
        self.wake_listener = WakeListener(self.config, self._on_wake_detected)
        self._tasks: list[asyncio.Task] = []
        self._running = False
        self.dashboard_state = DashboardState(config=self.config)
        self.dashboard_app = create_app(self.dashboard_state, on_confirm=self._on_dashboard_confirm)
        self._dashboard_server: Optional[uvicorn.Server] = None

    async def _on_wake_detected(self, event: WakeEvent) -> None:
        _LOGGER.info("Wake word detected from %s (confidence %.2f)", event.source, event.confidence)
        await self._wake_queue.put(event)

    async def start(self, *, headless: bool = False) -> None:
        if self._running:
            return
        self._running = True
        self._headless = headless
        self.config.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.config.data_dir.mkdir(parents=True, exist_ok=True)

        self._tasks.append(asyncio.create_task(self._wake_consumer(), name="wake-consumer"))
        if self.wake_listener:
            self._tasks.append(asyncio.create_task(self.wake_listener.run(), name="wake-listener"))

        if not headless:
            dash_config = uvicorn.Config(
                self.dashboard_app,
                host=self.config.dashboard.host,
                port=self.config.dashboard.port,
                log_level="info",
                loop="asyncio",
            )
            self._dashboard_server = uvicorn.Server(dash_config)
            self._tasks.append(asyncio.create_task(self._dashboard_server.serve(), name="dashboard"))
        else:
            _LOGGER.info("Headless mode: dashboard not started.")

        _LOGGER.info("Assistant runtime started (headless=%s).", headless)

    async def stop(self) -> None:
        self._running = False
        if hasattr(self.wake_listener, "stop"):
            await self.wake_listener.stop()
        if self._dashboard_server:
            self._dashboard_server.should_exit = True
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        _LOGGER.info("Assistant runtime stopped.")

    async def _wake_consumer(self) -> None:
        while self._running:
            event = await self._wake_queue.get()
            try:
                command = await asyncio.wait_for(self._command_queue.get(), timeout=10)
            except asyncio.TimeoutError:
                if sd is not None:
                    temp_path = await self._record_audio_to_file()
                    command = CommandInput(kind="audio_file", payload=str(temp_path))
                else:
                    _LOGGER.warning("No command provided after wake word; ignoring.")
                    continue

            await self._process_command(command)

    async def _process_command(self, command: CommandInput) -> RouterOutcome:
        if command.kind == "text":
            transcript = command.payload
        elif command.kind == "audio_file":
            transcript = await self.stt.transcribe_file(Path(command.payload))
        else:
            transcript = command.payload

        lowered = transcript.lower()
        if "confirm" in lowered or lowered in {"yes", "yeah"}:
            for entry in self.dashboard_state.pending_confirmations.values():
                entry["voice"] = True

        outcome = await self.router.handle_transcript(transcript)
        if outcome.success:
            await self.tts.speak(outcome.message)
        else:
            await self.tts.speak(f"Unable to complete request: {outcome.message}")

        if outcome.requires_confirmation and outcome.skill:
            self.dashboard_state.pending_confirmations.setdefault(outcome.skill, {"voice": False, "dashboard": False})
        elif outcome.skill and outcome.skill in self.dashboard_state.pending_confirmations:
            self.dashboard_state.pending_confirmations.pop(outcome.skill, None)

        return outcome

    async def enqueue_transcript(self, transcript: str) -> None:
        await self._command_queue.put(CommandInput(kind="text", payload=transcript))

    async def enqueue_audio_file(self, path: Path) -> None:
        await self._command_queue.put(CommandInput(kind="audio_file", payload=str(path)))

    async def simulate_session(self, transcript: str) -> RouterOutcome:
        await self._on_wake_detected(WakeEvent(transcript="envy", confidence=0.9, source="simulation"))
        await self.enqueue_transcript(transcript)
        return await self._process_command(CommandInput(kind="text", payload=transcript))

    async def _record_audio_to_file(self) -> Path:
        if sd is None:
            raise RuntimeError("sounddevice is not available.")
        duration = 5
        sample_rate = self.config.audio.sample_rate
        _LOGGER.info("Recording audio for %s seconds after wake word.", duration)
        recording = await asyncio.to_thread(
            sd.rec,
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
        )
        await asyncio.to_thread(sd.wait)
        temp_file = Path(tempfile.gettempdir()) / "envy-command.wav"
        await asyncio.to_thread(self._write_wav, temp_file, recording, sample_rate)
        return temp_file

    def _write_wav(self, path: Path, data, sample_rate: int) -> None:
        import wave

        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(data.tobytes())

    def _on_dashboard_confirm(self, skill: str) -> None:
        self.router.register_dashboard_confirmation(skill)
        entry = self.dashboard_state.pending_confirmations.setdefault(skill, {"voice": False, "dashboard": False})
        entry["dashboard"] = True


async def run(profile: str = "balanced", headless: bool = False) -> None:
    config = load_config(profile=profile)
    runtime = AssistantRuntime(config)
    await runtime.start(headless=headless)
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:  # pragma: no cover - runtime
        pass
    finally:
        await runtime.stop()
