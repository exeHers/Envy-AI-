from __future__ import annotations

import subprocess
import uuid
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf

from ..common.audio import ensure_dir
from ..common.config import EnvyConfig, PROJECT_ROOT
from ..common.logging import get_logger


class TTSEngine:
    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self.logger = get_logger("TTSEngine", config=config)
        output_dir = Path(config.get("tts.output_dir", "artifacts/tts"))
        self.output_dir = (PROJECT_ROOT / output_dir).resolve()
        ensure_dir(self.output_dir)
        self.engine_name = "fallback-tone"
        self.play_command = config.get("tts.play_command", "")
        self._pyttsx3 = None

        if config.get("tts.engine", "pyttsx3") == "pyttsx3":
            try:
                import pyttsx3  # type: ignore

                self._pyttsx3 = pyttsx3.init()
                voice = config.get("tts.voice")
                if voice:
                    self._pyttsx3.setProperty("voice", voice)
                self._pyttsx3.setProperty("rate", config.get("tts.rate", 180))
                self._pyttsx3.setProperty("volume", config.get("tts.volume", 0.9))
                self.engine_name = "pyttsx3"
                self.logger.info("pyttsx3 TTS engine initialised.")
            except Exception as exc:  # noqa: BLE001
                self.logger.warning(f"pyttsx3 unavailable, falling back to tone synthesis: {exc}")
                self._pyttsx3 = None

    def synthesize(self, text: str, session_id: Optional[str] = None, play: bool = False) -> dict:
        file_name = f"{session_id or uuid.uuid4().hex}.wav"
        path = self.output_dir / file_name
        if self._pyttsx3:
            self._speak_pyttsx3(text, path)
        else:
            self._generate_tone(text, path)
        if play and self.play_command:
            self._play_audio(path)
        self.logger.info(f"Synthesised speech saved to {path}")
        return {"path": str(path), "engine": self.engine_name}

    def _speak_pyttsx3(self, text: str, path: Path) -> None:
        assert self._pyttsx3 is not None
        self._pyttsx3.save_to_file(text, str(path))
        self._pyttsx3.runAndWait()

    def _generate_tone(self, text: str, path: Path) -> None:
        sample_rate = 16000
        duration_per_char = 0.08
        tones = []
        for char in text:
            freq = 220 + (ord(char) % 50) * 10
            t = np.linspace(0, duration_per_char, int(sample_rate * duration_per_char), False)
            tone = 0.3 * np.sin(2 * np.pi * freq * t)
            tones.append(tone)
            tones.append(np.zeros(int(sample_rate * 0.02)))
        if not tones:
            tones.append(np.zeros(int(sample_rate * 0.2)))
        audio = np.concatenate(tones).astype(np.float32)
        sf.write(str(path), audio, sample_rate)
        self.engine_name = "tone-fallback"

    def _play_audio(self, path: Path) -> None:
        try:
            subprocess.run([self.play_command, str(path)], check=False)
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(f"Audio playback failed: {exc}")


__all__ = ["TTSEngine"]
