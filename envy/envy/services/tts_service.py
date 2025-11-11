from __future__ import annotations

import asyncio
import logging
import math
import shutil
import time
from pathlib import Path
from typing import Tuple

import numpy as np
import soundfile as sf

try:  # pragma: no cover - optional dependency
    import pyttsx3
except ImportError:  # pragma: no cover
    pyttsx3 = None  # type: ignore

from envy.bus import EventBus
from envy.config import Config
from envy.services.base import ServiceBase

LOGGER = logging.getLogger("tts_service")


class TextToSpeechService(ServiceBase):
    name = "tts_service"

    def __init__(self, config: Config, bus: EventBus):
        super().__init__(config, bus)
        runtime_dir = Path(config.get("paths.runtime_dir", "./runtime")).resolve()
        self._audio_dir = runtime_dir / "tts"
        self._audio_dir.mkdir(parents=True, exist_ok=True)
        self._artifacts_dir = Path(config.get("paths.artifacts_dir", "./artifacts")).resolve()
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._engine = None

    async def run(self) -> None:
        queue = await self.bus.subscribe("router.response")
        while True:
            event = await queue.get()
            text = event.payload.get("text", "")
            if not text:
                continue
            await self._stream_partial(text)
            audio_path, used_engine = await asyncio.to_thread(self._synthesize, text)
            artifact_path = self._store_artifact(audio_path)
            LOGGER.info("TTS completed (engine=%s) artifact=%s", "pyttsx3" if used_engine else "tone", artifact_path)
            await self.bus.publish(
                "tts.completed",
                {
                    "text": text,
                    "audio_path": audio_path,
                    "artifact_path": artifact_path,
                    "used_engine": used_engine,
                    "timestamp": time.time(),
                },
            )

    async def _stream_partial(self, text: str) -> None:
        words = text.split()
        partial: list[str] = []
        for word in words:
            partial.append(word)
            await self.bus.publish(
                "tts.partial",
                {"text": " ".join(partial)},
            )
            await asyncio.sleep(0.05)

    def _synthesize(self, text: str) -> Tuple[str, bool]:
        timestamp = int(time.time() * 1000)
        audio_path = self._audio_dir / f"tts-{timestamp}.wav"
        if pyttsx3:
            try:
                engine = self._get_engine()
                engine.save_to_file(text, str(audio_path))
                engine.runAndWait()
                LOGGER.info("TTS synthesized via pyttsx3 to %s", audio_path)
                return str(audio_path), True
            except Exception as exc:  # pragma: no cover - audio backend issues
                LOGGER.warning("pyttsx3 synthesis failed (%s), falling back to tone", exc)
        self._generate_tone(text, audio_path)
        return str(audio_path), False

    def _store_artifact(self, audio_path: str) -> str:
        target = self._artifacts_dir / "tts-output.wav"
        try:
            shutil.copy(audio_path, target)
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Unable to copy TTS output to artifact: %s", exc)
        return str(target)

    def _get_engine(self):
        if self._engine or not pyttsx3:
            return self._engine
        self._engine = pyttsx3.init()
        rate = self.config.get("tts.rate", 180)
        volume = self.config.get("tts.volume", 0.8)
        voice = self.config.get("tts.voice")
        try:
            self._engine.setProperty("rate", rate)
            self._engine.setProperty("volume", volume)
            if voice:
                self._engine.setProperty("voice", voice)
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Unable to configure pyttsx3 voice properties: %s", exc)
        return self._engine

    def _generate_tone(self, text: str, audio_path: Path) -> None:
        sample_rate = 16000
        duration_per_word = 0.15
        words = max(1, len(text.split()))
        total_duration = min(5.0, words * duration_per_word)
        t = np.linspace(0, total_duration, int(sample_rate * total_duration), endpoint=False)
        frequency = 440
        waveform = 0.1 * np.sin(2 * math.pi * frequency * t)
        sf.write(audio_path, waveform, sample_rate)
        LOGGER.info("Fallback tone generated at %s", audio_path)
