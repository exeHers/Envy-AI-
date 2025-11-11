from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict
from uuid import uuid4

import numpy as np
import soundfile as sf

try:
    from vosk import KaldiRecognizer, Model  # type: ignore
except ImportError:  # pragma: no cover - fallback for environments without vosk
    KaldiRecognizer = None  # type: ignore
    Model = None  # type: ignore

from envy.bus import EventBus
from envy.config import Config
from envy.services.base import ServiceBase

LOGGER = logging.getLogger("wake_listener")


class WakeListenerService(ServiceBase):
    name = "wake_listener"

    def __init__(self, config: Config, bus: EventBus):
        super().__init__(config, bus)
        self._queue: asyncio.Queue[Dict[str, str]] = asyncio.Queue()
        self._model: Model | None = None
        self._model_loaded = False
        self._sample_rate = int(config.get("wake_sample_rate", 16000))
        self._keyword = config.get("wake.keyword", "envy").lower()
        self._model_path = Path(config.get("wake.model"))

    async def enqueue_audio_file(self, audio_path: str, command_audio_path: str | None = None) -> None:
        await self._queue.put({"audio_path": audio_path, "command_audio_path": command_audio_path})

    async def run(self) -> None:
        await self._ensure_model()
        LOGGER.info("Wake listener running with keyword '%s'", self._keyword)
        while True:
            item = await self._queue.get()
            audio_path = item["audio_path"]
            command_audio_path = item.get("command_audio_path")
            detected = await asyncio.to_thread(self._process_audio_file, audio_path)
            if detected:
                detection_id = str(uuid4())
                LOGGER.info("Wake word detected in %s", audio_path)
                await self.bus.publish(
                    "wake.detected",
                    {
                        "audio_path": audio_path,
                        "command_audio_path": command_audio_path,
                        "detection_id": detection_id,
                        "timestamp": time.time(),
                    },
                )
            else:
                LOGGER.debug("Wake word not detected in %s", audio_path)

    async def _ensure_model(self) -> None:
        if self._model_loaded or Model is None:
            return
        if not self._model_path.exists():
            LOGGER.warning("Wake model missing at %s. Wake detection will be naive.", self._model_path)
            self._model_loaded = False
            return
        try:
            self._model = Model(str(self._model_path))
            self._model_loaded = True
            LOGGER.info("Loaded wake model from %s", self._model_path)
        except Exception as exc:  # pragma: no cover - model load errors
            LOGGER.error("Failed to load wake model: %s", exc)
            self._model_loaded = False
            self._model = None

    def _process_audio_file(self, audio_path: str) -> bool:
        if self._model_loaded and self._model and KaldiRecognizer:
            return self._detect_with_vosk(audio_path)
        return self._detect_with_energy(audio_path)

    def _detect_with_vosk(self, audio_path: str) -> bool:
        recognizer = KaldiRecognizer(self._model, self._sample_rate, json.dumps([self._keyword]))
        with sf.SoundFile(audio_path) as audio:
            if audio.samplerate != self._sample_rate:
                data = audio.read(dtype="float32")
                resampled = self._resample_audio(data, audio.samplerate, self._sample_rate)
                chunk = (resampled * 32767).astype(np.int16).tobytes()
                recognizer.AcceptWaveform(chunk)
                result = json.loads(recognizer.FinalResult())
                return self._keyword in result.get("text", "").lower()
            while True:
                data = audio.buffer_read(4000, dtype="int16")
                if not data:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if self._keyword in result.get("text", "").lower():
                        return True
            final = json.loads(recognizer.FinalResult())
            return self._keyword in final.get("text", "").lower()

    def _detect_with_energy(self, audio_path: str) -> bool:
        # Naive fallback: check RMS energy peaks that align with expected speech patterns.
        with sf.SoundFile(audio_path) as audio:
            data = audio.read(dtype="float32")
        energy = np.sqrt(np.mean(np.square(data)))
        LOGGER.debug("Energy for %s: %.4f", audio_path, energy)
        # Threshold chosen experimentally for demo audio samples.
        return energy > 0.02

    def _resample_audio(self, data: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
        if original_rate == target_rate:
            return data
        duration = len(data) / original_rate
        target_samples = int(duration * target_rate)
        return np.interp(
            np.linspace(0, len(data), target_samples, endpoint=False),
            np.arange(len(data)),
            data,
        )
