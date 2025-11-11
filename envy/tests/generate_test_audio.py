from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import soundfile as sf

try:  # pragma: no cover
    import pyttsx3
except ImportError:  # pragma: no cover
    pyttsx3 = None  # type: ignore


TEST_AUDIO_DIR = Path(__file__).resolve().parent / "audio"
TEST_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def synthesize_with_pyttsx3(text: str, path: Path) -> bool:
    if not pyttsx3:
        return False
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.save_to_file(text, str(path))
        engine.runAndWait()
        return True
    except Exception:
        return False


def resample_to_16k(path: Path) -> None:
    data, samplerate = sf.read(path)
    target_rate = 16000
    if samplerate == target_rate:
        return
    duration = len(data) / samplerate
    target_samples = int(duration * target_rate)
    resampled = np.interp(
        np.linspace(0, len(data), target_samples, endpoint=False),
        np.arange(len(data)),
        data if data.ndim == 1 else data[:, 0],
    )
    sf.write(path, resampled, target_rate)


def tone_fallback(text: str, path: Path) -> None:
    words = max(1, len(text.split()))
    sample_rate = 16000
    duration = words * 0.3
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    waveform = 0.2 * np.sin(2 * math.pi * 440 * t)
    sf.write(path, waveform, sample_rate)


def create_audio_samples() -> None:
    pairs = [
        ("Envy", TEST_AUDIO_DIR / "wake_envy.wav"),
        ("Envy create test dot p y that prints hello", TEST_AUDIO_DIR / "command_create_test.wav"),
        ("Envy how is the system status today", TEST_AUDIO_DIR / "command_smalltalk.wav"),
    ]
    for text, path in pairs:
        success = synthesize_with_pyttsx3(text, path)
        if not success:
            tone_fallback(text, path)
        resample_to_16k(path)


if __name__ == "__main__":
    create_audio_samples()
