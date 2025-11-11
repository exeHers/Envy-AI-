"""Wake word listener service using VOSK."""
import json
import logging
import queue
import sounddevice as sd
import vosk
from pathlib import Path
from typing import Optional, Callable
import threading


logger = logging.getLogger(__name__)


class WakeWordListener:
    """Listens for wake word 'Envy' using VOSK."""
    
    def __init__(self, config, wake_callback: Callable[[], None]):
        self.config = config
        self.wake_callback = wake_callback
        self.model_path = config.get("wake.model_path", "models/vosk-model-small-en-us-0.22")
        self.keyword = config.get("wake.keyword", "envy").lower()
        self.sensitivity = config.get("wake.sensitivity", 0.5)
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.model: Optional[vosk.Model] = None
        self.rec: Optional[vosk.KaldiRecognizer] = None
        self.audio_queue = queue.Queue()
        
    def _load_model(self):
        """Load VOSK model."""
        model_path = Path(self.model_path)
        if not model_path.exists():
            logger.warning(f"VOSK model not found at {model_path}. Using fallback.")
            # Try to use a minimal model or download
            return False
        
        try:
            self.model = vosk.Model(str(model_path))
            self.rec = vosk.KaldiRecognizer(self.model, 16000)
            self.rec.SetWords(True)
            logger.info(f"Loaded VOSK model from {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load VOSK model: {e}")
            return False
    
    def _audio_callback(self, indata, frames, time, status):
        """Audio input callback."""
        if status:
            logger.warning(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def _process_audio(self):
        """Process audio stream for wake word detection."""
        if not self.rec:
            return
        
        while self.running:
            try:
                data = self.audio_queue.get(timeout=1.0)
                if self.rec.AcceptWaveform(data):
                    result = json.loads(self.rec.Result())
                    words = result.get("result", [])
                    for word_info in words:
                        word = word_info.get("word", "").lower()
                        if self.keyword in word:
                            logger.info(f"Wake word '{self.keyword}' detected!")
                            self.wake_callback()
                else:
                    # Partial result
                    partial = json.loads(self.rec.PartialResult())
                    text = partial.get("partial", "").lower()
                    if self.keyword in text:
                        logger.info(f"Wake word '{self.keyword}' detected (partial)!")
                        self.wake_callback()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
    
    def start(self):
        """Start wake word listener."""
        if self.running:
            return
        
        if not self._load_model():
            logger.error("Cannot start wake word listener: model not loaded")
            return False
        
        self.running = True
        
        # Start audio stream
        try:
            with sd.RawInputStream(
                samplerate=16000,
                channels=1,
                dtype='int16',
                blocksize=8000,
                callback=self._audio_callback
            ):
                self._process_audio()
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            self.running = False
            return False
    
    def start_async(self):
        """Start wake word listener in background thread."""
        if self.running:
            return
        
        self.thread = threading.Thread(target=self.start, daemon=True)
        self.thread.start()
        logger.info("Wake word listener started in background")
    
    def stop(self):
        """Stop wake word listener."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logger.info("Wake word listener stopped")
