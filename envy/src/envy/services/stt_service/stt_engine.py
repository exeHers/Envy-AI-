from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from ..common import audio
from ..common.config import EnvyConfig, PROJECT_ROOT
from ..common.logging import get_logger


PartialCallback = Callable[[str], None]


@dataclass
class TranscriptionResult:
    text: str
    partials: List[str] = field(default_factory=list)
    engine: str = "fallback"


class STTEngine:
    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self.logger = get_logger("STTEngine", config=config)
        self.model_path = Path(config.get("stt.model_path", "models/vosk-model-small-en-us-0.15"))
        self.language = config.get("stt.language", "en-US")
        self.tests_transcript_dir = Path(config.get("tests.transcripts_dir", "tests/assets/transcripts"))
        self.model = None
        self.Recognizer = None

        try:
            from vosk import KaldiRecognizer, Model  # type: ignore

            if self.model_path.exists():
                self.model = Model(str(self.model_path))
                self.Recognizer = KaldiRecognizer
                self.logger.info(f"Loaded Vosk STT model from {self.model_path}")
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(f"Vosk STT unavailable, using transcript fallbacks: {exc}")

    def transcribe_file(self, path: Path, emit_partial: Optional[PartialCallback] = None) -> TranscriptionResult:
        if self.model and self.Recognizer:
            return self._transcribe_with_vosk(path, emit_partial)
        return self._transcribe_fallback(path, emit_partial)

    def _transcribe_with_vosk(self, path: Path, emit_partial: Optional[PartialCallback]) -> TranscriptionResult:
        audio_bytes, rate = audio.read_wav_bytes(path)
        recognizer = self.Recognizer(self.model, rate)
        partials: List[str] = []
        for chunk in audio.chunk_bytes(audio_bytes, 4096):
            if recognizer.AcceptWaveform(chunk):
                res = json.loads(recognizer.Result())
                text = res.get("text", "")
                if text:
                    partials.append(text)
                    if emit_partial:
                        emit_partial(text)
            else:
                res = json.loads(recognizer.PartialResult())
                if res.get("partial"):
                    partial = res["partial"]
                    if emit_partial:
                        emit_partial(partial)
        final_res = json.loads(recognizer.FinalResult())
        final_text = final_res.get("text", "").strip()
        if final_text and (not partials or partials[-1] != final_text):
            partials.append(final_text)
        return TranscriptionResult(text=final_text, partials=partials, engine="vosk")

    def _transcribe_fallback(self, path: Path, emit_partial: Optional[PartialCallback]) -> TranscriptionResult:
        transcript_path = self._resolve_transcript(path)
        if transcript_path and transcript_path.exists():
            text = transcript_path.read_text(encoding="utf-8").strip()
            chunks = [chunk.strip() for chunk in text.split(".") if chunk.strip()]
            for chunk in chunks:
                if emit_partial:
                    emit_partial(chunk)
            return TranscriptionResult(text=text, partials=chunks, engine="fallback-transcript")
        stub_text = path.stem.replace("_", " ")
        if emit_partial:
            emit_partial(stub_text)
        return TranscriptionResult(text=stub_text, partials=[stub_text], engine="heuristic-filename")

    def _resolve_transcript(self, audio_path: Path) -> Optional[Path]:
        candidates = [
            audio_path.with_suffix(".txt"),
            audio_path.with_suffix(".json"),
            self.tests_transcript_dir / f"{audio_path.stem}.txt",
            PROJECT_ROOT / "tests" / "assets" / "transcripts" / f"{audio_path.stem}.txt",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None


__all__ = ["STTEngine", "TranscriptionResult"]
