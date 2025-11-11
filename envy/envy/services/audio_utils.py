from __future__ import annotations

import audioop
import wave
from pathlib import Path
from typing import Generator, Tuple


def read_wav_mono(
    path: Path,
    target_sample_rate: int,
    chunk_size: int = 4000,
) -> Tuple[int, Generator[bytes, None, None]]:
    """Yield mono PCM16 chunks at the target sample rate."""

    wf = wave.open(str(path), "rb")
    nchannels = wf.getnchannels()
    sampwidth = wf.getsampwidth()
    framerate = wf.getframerate()

    if sampwidth not in (1, 2):
        raise ValueError(f"Unsupported sample width: {sampwidth}")

    state = None

    def generator() -> Generator[bytes, None, None]:
        nonlocal state
        try:
            while True:
                data = wf.readframes(chunk_size)
                if not data:
                    break
                if nchannels > 1:
                    data = audioop.tomono(data, sampwidth, 1, 1)
                if sampwidth == 1:
                    data = audioop.lin2lin(data, 1, 2)
                if framerate != target_sample_rate:
                    data, state = audioop.ratecv(
                        data,
                        2,
                        1,
                        framerate,
                        target_sample_rate,
                        state,
                    )
                yield data
        finally:
            wf.close()

    return target_sample_rate, generator()
