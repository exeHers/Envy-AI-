from __future__ import annotations

import contextlib
import wave
from pathlib import Path
from typing import Generator, Iterable, Tuple

import numpy as np
import soundfile as sf
from scipy.signal import resample


def read_wav_bytes(path: Path) -> Tuple[bytes, int]:
    with contextlib.closing(wave.open(str(path), "rb")) as wf:
        params = wf.getparams()
        audio_bytes = wf.readframes(params.nframes)
        return audio_bytes, params.framerate


def load_audio(path: Path, target_rate: int = 16000) -> Tuple[np.ndarray, int]:
    audio, rate = sf.read(str(path), dtype="float32")
    if rate != target_rate:
        num_samples = int(len(audio) * target_rate / rate)
        audio = resample(audio, num_samples)
        rate = target_rate
    return audio, rate


def to_int16(audio: np.ndarray) -> np.ndarray:
    return np.clip(audio * 32767, -32768, 32767).astype(np.int16)


def chunk_bytes(data: bytes, chunk_size: int) -> Generator[bytes, None, None]:
    for start in range(0, len(data), chunk_size):
        yield data[start : start + chunk_size]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


__all__ = ["read_wav_bytes", "load_audio", "to_int16", "chunk_bytes", "ensure_dir"]
