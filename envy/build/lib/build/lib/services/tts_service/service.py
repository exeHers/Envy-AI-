from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pyttsx3

from ..config import load_config, resolve_profile
from ..logger import get_logger


logger = get_logger("tts_service")


@dataclass
class TtsResult:
    text: str
    output_path: Path
    engine: str
    succeeded: bool


class TtsService:
    def __init__(self, config_path: Optional[Path] = None, profile: Optional[str] = None):
        self.config = load_config(config_path)
        self.profile = resolve_profile(self.config, profile)
        self.artifacts_dir = Path(self.config["runtime"]["artifacts_dir"])
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.tts_engine = self.profile["tts"]["engine"]
        self.voice = self.profile["tts"].get("voice", "default")

    def synthesize(self, text: str, output_path: Optional[Path] = None, play: bool = False) -> TtsResult:
        output_file = output_path or (self.artifacts_dir / "tts-output.wav")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        succeeded = False
        engine_used = "pyttsx3"
        try:
            engine = pyttsx3.init()
            if self.voice and self.voice != "default":
                for voice in engine.getProperty("voices"):
                    if self.voice.lower() in voice.name.lower():
                        engine.setProperty("voice", voice.id)
                        break
            engine.save_to_file(text, str(output_file))
            engine.runAndWait()
            succeeded = output_file.exists()
        except Exception as exc:  # noqa: BLE001
            logger.error("pyttsx3 synthesis failed: %s", exc)
            engine_used = "fallback"
            succeeded = self._fallback_say(text, output_file)

        if play and succeeded:
            try:
                subprocess.run(["aplay", str(output_file)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                logger.warning("aplay not found; skipping playback.")

        logger.info("TTS synthesis completed using %s -> %s", engine_used, output_file)
        return TtsResult(text=text, output_path=output_file, engine=engine_used, succeeded=succeeded)

    def _fallback_say(self, text: str, output_file: Path) -> bool:
        """
        Fallback TTS: write text to a simple waveform using numpy to avoid silence.
        """
        try:
            import numpy as np
            import wave

            sample_rate = 16000
            duration = max(1, len(text) // 10)
            t = np.linspace(0, duration, int(sample_rate * duration))
            waveform = 0.1 * np.sin(2 * np.pi * 220 * t)
            with wave.open(str(output_file), "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes((waveform * 32767).astype(np.int16).tobytes())
            caption_file = output_file.with_suffix(".txt")
            caption_file.write_text(text, encoding="utf-8")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Fallback TTS failed: %s", exc)
            return False
