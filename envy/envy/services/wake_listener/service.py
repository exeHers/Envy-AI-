from __future__ import annotations

import io
import logging
import threading
from dataclasses import dataclass
from typing import Callable, Optional

import wave
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

logger = logging.getLogger("envy.wake_listener")


try:
    import sounddevice as sd  # type: ignore
except (ImportError, OSError):  # pragma: no cover - optional
    sd = None


try:
    import vosk  # type: ignore
except ImportError:  # pragma: no cover - optional
    vosk = None


WakeCallback = Callable[[dict], None]


@dataclass
class WakeConfig:
    model_path: Optional[str] = None
    sensitivity: float = 0.4
    sample_rate: int = 16000
    keyword: str = "envy"
    live_listen: bool = False


class WakeListenerService:
    def __init__(self, config: WakeConfig, on_wake: Optional[WakeCallback] = None):
        self.config = config
        self.on_wake = on_wake
        self._model = None
        self._listening_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        if vosk and self.config.model_path:
            try:
                self._model = vosk.Model(self.config.model_path)
            except Exception as exc:  # pragma: no cover - runtime guard
                logger.error("Failed to load Vosk wake model: %s", exc)
        else:
            logger.warning("Vosk model unavailable; wake detection will use stub fallback.")

    def start_live_listening(self) -> None:
        if not self.config.live_listen or sd is None:
            logger.info("Live listening disabled by config.")
            return
        if self._listening_thread and self._listening_thread.is_alive():
            return

        self._stop_event.clear()
        self._listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listening_thread.start()
        logger.info("Wake listener live thread started.")

    def stop_live_listening(self) -> None:
        self._stop_event.set()
        if self._listening_thread and self._listening_thread.is_alive():
            self._listening_thread.join(timeout=1)

    def detect_from_audio(self, wav_bytes: bytes) -> bool:
        if self._model:
            detected = self._detect_with_vosk(wav_bytes)
        else:
            detected = self._detect_stub(wav_bytes)
        if detected:
            logger.info("Wake word detected (API input).")
        return detected

    def _detect_with_vosk(self, wav_bytes: bytes) -> bool:
        buffer = io.BytesIO(wav_bytes)
        with wave.open(buffer, "rb") as wf:
            recognizer = vosk.KaldiRecognizer(self._model, wf.getframerate(), f'["{self.config.keyword}"]')
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    result = recognizer.Result()
                    if self.config.keyword in result.lower():
                        return True
        final = recognizer.FinalResult()
        return self.config.keyword in final.lower()

    def _detect_stub(self, wav_bytes: bytes) -> bool:
        # Very small heuristic: treat non-empty audio as wake trigger during tests.
        return bool(wav_bytes)

    def _listen_loop(self) -> None:  # pragma: no cover - hardware loop
        block_duration = 0.5
        if sd is None:
            logger.warning("sounddevice unavailable; cannot enter live listening loop.")
            return
        try:
            with sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=1,
                blocksize=int(self.config.sample_rate * block_duration),
                dtype="int16",
            ) as stream:
                recognizer = None
                if self._model:
                    recognizer = vosk.KaldiRecognizer(
                        self._model, self.config.sample_rate, f'["{self.config.keyword}"]'
                    )
                while not self._stop_event.is_set():
                    frames, _ = stream.read(int(self.config.sample_rate * block_duration))
                    data = frames.copy(order="C").tobytes()
                    detected = False
                    if recognizer:
                        if recognizer.AcceptWaveform(data):
                            result = recognizer.Result()
                            detected = self.config.keyword in result.lower()
                    else:
                        detected = self._detect_stub(data)
                    if detected:
                        logger.info("Wake word detected (live).")
                        if self.on_wake:
                            self.on_wake({"source": "live", "keyword": self.config.keyword})
        except Exception as exc:
            logger.error("Live listening failed: %s", exc)


class WakeDetectResponse(BaseModel):
    wake_detected: bool
    keyword: str


def create_app(service: WakeListenerService) -> FastAPI:
    app = FastAPI(title="Envy Wake Listener")

    @app.on_event("startup")
    async def startup_event():
        service.start_live_listening()

    @app.on_event("shutdown")
    async def shutdown_event():
        service.stop_live_listening()

    @app.post("/detect", response_model=WakeDetectResponse)
    async def detect(file: UploadFile = File(...)):
        data = await file.read()
        detected = service.detect_from_audio(data)
        if detected and service.on_wake:
            service.on_wake({"source": "api", "keyword": service.config.keyword})
        return WakeDetectResponse(wake_detected=detected, keyword=service.config.keyword)

    return app
