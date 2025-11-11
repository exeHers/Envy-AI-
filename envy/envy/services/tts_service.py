from __future__ import annotations

import logging
import wave
from contextlib import suppress
from pathlib import Path
from typing import Optional

import numpy as np

LOGGER = logging.getLogger(__name__)

try:
    import pyttsx3
except Exception:  # pragma: no cover - optional dependency
    pyttsx3 = None  # type: ignore
    LOGGER.warning("pyttsx3 not available. TTS will degrade to tone synthesis.")


class TextToSpeechService:
    def __init__(self, engine_name: str = "pyttsx3", voice: Optional[str] = None, rate: int = 170):
        self.engine_name = engine_name
        self.voice = voice
        self.rate = rate
        self._engine = self._init_engine()

    def _init_engine(self):
        if self.engine_name != "pyttsx3" or pyttsx3 is None:
            return None
        LOGGER.debug("Initialising pyttsx3 engine (voice=%s, rate=%s)", self.voice, self.rate)
        engine = pyttsx3.init()
        engine.setProperty("rate", self.rate)
        if self.voice:
            with suppress(Exception):
                engine.setProperty("voice", self.voice)
        return engine

    def synthesize(self, text: str, output_path: Path) -> Path:
        LOGGER.info("Synthesizing speech to %s", output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self._engine:
            try:
                self._engine.save_to_file(text, str(output_path))
                self._engine.runAndWait()
                LOGGER.info("TTS synthesis complete using pyttsx3.")
                return output_path
            except Exception as exc:  # pragma: no cover - fallback path
                LOGGER.error("pyttsx3 synthesis failed: %s", exc)

        LOGGER.warning("Falling back to tone-based synthesis.")
        self._generate_tone(text, output_path)
        return output_path

    def _generate_tone(self, text: str, output_path: Path, duration: float = 2.0) -> None:
        sample_rate = 22050
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        base_freq = 440
        # Simple amplitude modulation based on text length.
        amplitude = min(1.0, 0.3 + len(text) / 100.0)
        waveform = amplitude * np.sin(2 * np.pi * base_freq * t)
        waveform = np.int16(waveform * 32767)

        with wave.open(str(output_path), "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(waveform.tobytes())

        LOGGER.info("Tone synthesis complete (fallback).")
