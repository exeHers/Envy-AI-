"""
Text-to-speech service using pyttsx3 with file output.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional dependency
    import pyttsx3
except ImportError:  # pragma: no cover - optional dependency
    pyttsx3 = None  # type: ignore

_LOGGER = logging.getLogger(__name__)


class TTSService:
    def __init__(self, artifacts_dir: Path) -> None:
        self.artifacts_dir = artifacts_dir
        self._engine = None
        self._lock = asyncio.Lock()

    async def speak(self, text: str, filename: Optional[str] = None, play_audio: bool = False) -> Path:
        """
        Synthesize speech and optionally play it locally.
        """
        safe_dir = self.artifacts_dir / "tts"
        safe_dir.mkdir(parents=True, exist_ok=True)
        target = safe_dir / (filename or "tts-output.wav")

        if pyttsx3 is None:
            _LOGGER.warning("pyttsx3 not installed; writing transcript instead of audio.")
            target.write_text(text, encoding="utf-8")
            return target

        async with self._lock:
            if self._engine is None:
                try:
                    self._engine = pyttsx3.init()
                    self._engine.setProperty("rate", 180)
                except Exception as exc:  # pragma: no cover - audio backend issues
                    _LOGGER.warning("pyttsx3 init failed (%s); writing text fallback.", exc)
                    target = target.with_suffix(".txt")
                    target.write_text(text, encoding="utf-8")
                    return target
            try:
                await asyncio.to_thread(self._engine.save_to_file, text, str(target))
                await asyncio.to_thread(self._engine.runAndWait)
            except Exception as exc:  # pragma: no cover - audio backend issues
                _LOGGER.warning("pyttsx3 error (%s); writing text fallback.", exc)
                target = target.with_suffix(".txt")
                target.write_text(text, encoding="utf-8")

        if play_audio:
            await self._play_audio(target)

        _LOGGER.info("TTS rendered to %s", target)
        return target

    async def _play_audio(self, path: Path) -> None:
        if not path.exists():
            return
        if path.suffix != ".wav":
            _LOGGER.info("Skipping playback for non-audio file %s", path)
            return
        try:
            import simpleaudio  # type: ignore  # pragma: no cover - optional
        except ImportError:  # pragma: no cover - optional dependency
            _LOGGER.info("simpleaudio not available; skipping playback.")
            return

        import wave  # pragma: no cover - optional dependency

        with wave.open(str(path), "rb") as wf:
            audio = wf.readframes(wf.getnframes())
            play_obj = simpleaudio.play_buffer(audio, wf.getnchannels(), wf.getsampwidth(), wf.getframerate())
            play_obj.wait_done()
