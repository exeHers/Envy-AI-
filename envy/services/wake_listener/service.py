from __future__ import annotations

import json
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
import vosk

from ..config import load_config, resolve_profile
from ..logger import get_logger


logger = get_logger("wake_listener")


@dataclass
class WakeWordDetectorResult:
    detected: bool
    transcript: str
    confidence: float


class WakeListener:
    """
    Vosk-based wake word detector for the Envy assistant.
    """

    def __init__(self, config_path: Optional[Path] = None, profile: Optional[str] = None):
        self.config = load_config(config_path)
        self.profile = resolve_profile(self.config, profile)
        self.wake_word = self.config["assistant"]["wake_word"].lower()
        self.model_path = self.profile["stt"]["model"]
        self.frame_samples = self.profile["wake_listener"]["frame_samples"]
        self.threshold = self.profile["wake_listener"]["detect_threshold"]
        self._recognizer = None
        self._model = None

    def _load_model(self):
        if self._model is None:
            model_path = Path(self.model_path)
            if not model_path.exists():
                raise FileNotFoundError(
                    f"Vosk model not found at {model_path}. Run scripts/download_models.sh first."
                )
            logger.info("Loading Vosk model from %s", model_path)
            self._model = vosk.Model(str(model_path))
            grammar = json.dumps([self.wake_word, ""])
            self._recognizer = vosk.KaldiRecognizer(self._model, 16000, grammar)

    def detect_from_file(self, wav_path: str | Path) -> WakeWordDetectorResult:
        """
        Run wake-word detection on an audio file.
        """
        self._load_model()
        wav_path = Path(wav_path)
        if not wav_path.exists():
            raise FileNotFoundError(wav_path)

        with wave.open(str(wav_path), "rb") as wf:
            if wf.getframerate() != 16000 or wf.getnchannels() != 1:
                raise ValueError("Wake audio must be mono 16kHz.")
            transcript = ""
            confidence = 0.0
            while True:
                data = wf.readframes(self.frame_samples)
                if len(data) == 0:
                    break
                if self._recognizer.AcceptWaveform(data):
                    result = json.loads(self._recognizer.Result())
                    transcript += " " + result.get("text", "")
                    confidence = max(confidence, result.get("confidence", 0.0))
                else:
                    partial = json.loads(self._recognizer.PartialResult())
                    partial_text = partial.get("partial", "")
                    if self.wake_word in partial_text.lower():
                        transcript += " " + partial_text
                        confidence = max(confidence, self.threshold + 0.1)
            final_result = json.loads(self._recognizer.FinalResult())
            transcript += " " + final_result.get("text", "")
            confidence = max(confidence, final_result.get("confidence", 0.0))
            detected = self.wake_word in transcript.lower()
            logger.info(
                "Wake word analysis for %s: detected=%s transcript='%s' confidence=%.2f",
                wav_path,
                detected,
                transcript.strip(),
                confidence,
            )
            return WakeWordDetectorResult(detected=detected, transcript=transcript.strip(), confidence=confidence)

    def listen(self, on_detect: Callable[[], None], device: Optional[int] = None):
        """
        Start microphone listener. When wake word detected, call on_detect.
        """
        self._load_model()
        logger.info("Starting wake listener on device=%s", device or "default")

        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning("Audio callback status: %s", status)
            data = (indata * 32768).astype(np.int16).tobytes()
            if self._recognizer.AcceptWaveform(data):
                result = json.loads(self._recognizer.Result())
                text = result.get("text", "").lower()
                confidence = result.get("confidence", 0.0)
                if self.wake_word in text and confidence >= self.threshold:
                    logger.info("Wake word detected in live audio: %s", text)
                    on_detect()

        with sd.InputStream(
            samplerate=16000,
            blocksize=self.frame_samples,
            dtype="int16",
            channels=1,
            device=device,
            callback=audio_callback,
        ):
            logger.info("Wake listener streaming. Press Ctrl+C to stop.")
            try:
                while True:
                    sd.sleep(1000)
            except KeyboardInterrupt:
                logger.info("Wake listener stopped by user.")
