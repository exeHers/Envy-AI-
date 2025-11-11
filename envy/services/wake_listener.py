"""Wake word listener service using VOSK."""
import os
import json
import queue
import sounddevice as sd
try:
    from vosk import Model, KaldiRecognizer
except ImportError:
    from .mock_vosk import Model, KaldiRecognizer
from pathlib import Path
import threading
import time
from .logger import setup_logger
from .config_loader import get_config


class WakeListener:
    """Lightweight wake word detector using VOSK."""
    
    def __init__(self, callback=None):
        self.config = get_config()
        self.logger = setup_logger("WakeListener", self.config.get("logging.file"))
        
        self.keyword = self.config.get("wake_word.keyword", "envy").lower()
        self.sample_rate = self.config.get("wake_word.sample_rate", 16000)
        self.sensitivity = self.config.get("wake_word.sensitivity", 0.5)
        
        # Model path
        model_path = self.config.get("wake_word.model_path")
        if model_path:
            base_dir = Path(__file__).parent.parent
            full_model_path = base_dir / model_path
            if not full_model_path.exists():
                self.logger.warning(f"VOSK model not found at {full_model_path}, using fallback")
                # Try to find any vosk model
                models_dir = base_dir / "models"
                if models_dir.exists():
                    vosk_models = list(models_dir.glob("vosk-model*"))
                    if vosk_models:
                        full_model_path = vosk_models[0]
                        self.logger.info(f"Using VOSK model: {full_model_path}")
        else:
            full_model_path = None
            
        self.model_path = full_model_path
        self.callback = callback
        self.running = False
        self.model = None
        self.recognizer = None
        self.audio_queue = queue.Queue()
        self.thread = None
        
    def initialize(self):
        """Initialize VOSK model."""
        try:
            if self.model_path and self.model_path.exists():
                self.logger.info(f"Loading VOSK model from {self.model_path}")
                self.model = Model(str(self.model_path))
                self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
                self.recognizer.SetWords(True)
                self.logger.info("VOSK model loaded successfully")
                return True
            else:
                self.logger.error(f"VOSK model not found at {self.model_path}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to initialize VOSK model: {e}")
            return False
            
    def audio_callback(self, indata, frames, time_info, status):
        """Audio input callback."""
        if status:
            self.logger.debug(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))
        
    def process_audio(self):
        """Process audio from queue and detect wake word."""
        self.logger.info(f"Wake listener started, listening for '{self.keyword}'...")
        
        while self.running:
            try:
                data = self.audio_queue.get(timeout=1)
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower()
                    
                    if self.keyword in text:
                        self.logger.info(f"Wake word detected: {text}")
                        if self.callback:
                            threading.Thread(target=self.callback, daemon=True).start()
                else:
                    # Partial result
                    partial = json.loads(self.recognizer.PartialResult())
                    text = partial.get("partial", "").lower()
                    if self.keyword in text:
                        self.logger.info(f"Wake word detected (partial): {text}")
                        if self.callback:
                            threading.Thread(target=self.callback, daemon=True).start()
                            
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing audio: {e}")
                
    def start(self):
        """Start listening for wake word."""
        if not self.initialize():
            self.logger.error("Failed to initialize wake listener")
            return False
            
        self.running = True
        
        # Start audio processing thread
        self.thread = threading.Thread(target=self.process_audio, daemon=True)
        self.thread.start()
        
        # Start audio input stream
        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=self.audio_callback
            ):
                self.logger.info("Audio stream started")
                while self.running:
                    time.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Audio stream error: {e}")
            self.running = False
            return False
            
        return True
        
    def stop(self):
        """Stop listening."""
        self.logger.info("Stopping wake listener...")
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)


def main():
    """Test wake listener."""
    def on_wake():
        print(">>> WAKE WORD DETECTED! <<<")
        
    listener = WakeListener(callback=on_wake)
    try:
        listener.start()
    except KeyboardInterrupt:
        listener.stop()
        print("\nStopped")


if __name__ == "__main__":
    main()
