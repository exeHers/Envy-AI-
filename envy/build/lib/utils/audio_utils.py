"""Audio helper utilities."""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Generator, Iterable, Tuple

import numpy as np


def read_wave_chunks(path: Path, chunk_size: int) -> Generator[Tuple[bytes, int], None, None]:
    """Yield audio frames from a WAV file."""
    with wave.open(str(path), "rb") as wf:
        sample_rate = wf.getframerate()
        while True:
            data = wf.readframes(chunk_size)
            if not data:
                break
            yield data, sample_rate


def normalize_audio(samples: Iterable[float]) -> np.ndarray:
    arr = np.array(list(samples), dtype=np.float32)
    if arr.size == 0:
        return arr
    max_val = np.max(np.abs(arr))
    if max_val > 0:
        arr /= max_val
    return arr


def save_wave(path: Path, audio_data: bytes, sample_rate: int = 16000, channels: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)

