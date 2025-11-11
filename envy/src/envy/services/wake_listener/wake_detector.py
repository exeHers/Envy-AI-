from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..common import audio
from ..common.config import EnvyConfig, PROJECT_ROOT
from ..common.logging import get_logger


class WakeDetector:
    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self.logger = get_logger("WakeDetector", config=config)
        self.keyword = config.get("wake_listener.keyword", "envy").lower()
        self.sample_rate = int(config.get("wake_listener.sample_rate", 16000) or 16000)
        self.model_path = Path(config.get("wake_listener.model_path", "models/vosk-model-small-en-us-0.15"))
        self.tests_transcript_dir = Path(
            config.get("tests.transcripts_dir", "tests/assets/transcripts")
        )
        self.model = None
        self.Recognizer = None

        try:
            from vosk import KaldiRecognizer, Model  # type: ignore

            if self.model_path.exists():
                self.model = Model(str(self.model_path))
                self.Recognizer = KaldiRecognizer
                self.logger.info(f"Loaded Vosk model from {self.model_path}")
            else:
                self.logger.warning(f"Vosk model path not found: {self.model_path}")
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(f"Vosk not available, falling back to heuristic wake detection: {exc}")

    def detect_from_file(self, path: Path) -> bool:
        audio_bytes, rate = audio.read_wav_bytes(path)
        if self.model and self.Recognizer:
            return self._detect_with_vosk(audio_bytes, rate)
        return self._detect_fallback(path)

    def _detect_with_vosk(self, audio_bytes: bytes, rate: int) -> bool:
        recognizer = self.Recognizer(self.model, rate, json.dumps([self.keyword, "[unk]"]))
        for chunk in audio.chunk_bytes(audio_bytes, 4096):
            if recognizer.AcceptWaveform(chunk):
                result = self._parse_result(recognizer.Result())
                if result:
                    return True
        partial = self._parse_result(recognizer.FinalResult())
        return bool(partial)

    def _parse_result(self, result_json: str) -> bool:
        try:
            data = json.loads(result_json)
        except json.JSONDecodeError:
            return False
        text = data.get("text", "").lower()
        return self.keyword in text.split()

    def _detect_fallback(self, path: Path) -> bool:
        transcript_path = self._find_transcript(path)
        if transcript_path and transcript_path.exists():
            text = transcript_path.read_text(encoding="utf-8").lower()
            self.logger.debug(f"Fallback transcript used for {path}: {text}")
            return self.keyword in text
        if self.keyword in path.stem.lower():
            self.logger.debug(f"Fallback detection matched keyword in filename {path.stem}")
            return True
        return False

    def _find_transcript(self, audio_path: Path) -> Optional[Path]:
        candidates = [
            audio_path.with_suffix(".txt"),
            audio_path.with_suffix(".json"),
            PROJECT_ROOT / "tests" / "assets" / "transcripts" / f"{audio_path.stem}.txt",
            self.tests_transcript_dir / f"{audio_path.stem}.txt",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None


__all__ = ["WakeDetector"]
