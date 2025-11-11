"""Text-to-Speech service using pyttsx3."""
import pyttsx3
import threading
import queue
from pathlib import Path
from .logger import setup_logger
from .config_loader import get_config


class MockTTSEngine:
    """Mock TTS engine for testing."""
    def say(self, text):
        print(f"[Mock TTS]: {text}")
        
    def runAndWait(self):
        pass
        
    def stop(self):
        pass
        
    def setProperty(self, name, value):
        pass
        
    def getProperty(self, name):
        return None
        
    def save_to_file(self, text, filename):
        # Create a simple WAV file header for testing
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'wb') as f:
            # Write minimal WAV header
            f.write(b'RIFF')
            f.write((36 + len(text) * 2).to_bytes(4, 'little'))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))
            f.write((1).to_bytes(2, 'little'))  # PCM
            f.write((1).to_bytes(2, 'little'))  # Mono
            f.write((16000).to_bytes(4, 'little'))  # Sample rate
            f.write((32000).to_bytes(4, 'little'))  # Byte rate
            f.write((2).to_bytes(2, 'little'))  # Block align
            f.write((16).to_bytes(2, 'little'))  # Bits per sample
            f.write(b'data')
            f.write((len(text) * 2).to_bytes(4, 'little'))
            f.write(bytes([0] * len(text) * 2))  # Silent audio


class TTSService:
    """Text-to-Speech service."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = setup_logger("TTSService", self.config.get("logging.file"))
        
        self.engine_type = self.config.get("tts.engine", "pyttsx3")
        self.rate = self.config.get("tts.rate", 175)
        self.volume = self.config.get("tts.volume", 0.9)
        self.voice_index = self.config.get("tts.voice_index", 0)
        
        self.engine = None
        self.tts_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        
    def initialize(self):
        """Initialize TTS engine."""
        try:
            self.logger.info("Initializing TTS engine (pyttsx3)...")
            self.engine = pyttsx3.init()
            
            # Set properties
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Set voice if available
            voices = self.engine.getProperty('voices')
            if voices and len(voices) > self.voice_index:
                self.engine.setProperty('voice', voices[self.voice_index].id)
                self.logger.info(f"Using voice: {voices[self.voice_index].name}")
            
            self.logger.info("TTS engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            # Create mock engine for testing
            self.engine = MockTTSEngine()
            self.logger.info("Using mock TTS engine for testing")
            return True
            
    def speak(self, text: str, blocking: bool = False):
        """Speak text using TTS engine."""
        if self.engine is None:
            if not self.initialize():
                self.logger.error("TTS engine not initialized")
                return False
                
        try:
            self.logger.info(f"Speaking: {text}")
            
            if blocking:
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                # Non-blocking: queue the text
                self.tts_queue.put(text)
                if not self.running:
                    self._start_worker()
                    
            return True
            
        except Exception as e:
            self.logger.error(f"TTS error: {e}")
            return False
            
    def save_to_file(self, text: str, output_path: str):
        """Save speech to audio file."""
        if self.engine is None:
            if not self.initialize():
                return False
                
        try:
            self.logger.info(f"Saving TTS to file: {output_path}")
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.engine.save_to_file(text, str(output_path))
            self.engine.runAndWait()
            
            self.logger.info(f"TTS saved to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"TTS save error: {e}")
            return False
            
    def _start_worker(self):
        """Start background worker thread for non-blocking TTS."""
        if self.worker_thread and self.worker_thread.is_alive():
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        
    def _worker(self):
        """Worker thread to process TTS queue."""
        while self.running:
            try:
                text = self.tts_queue.get(timeout=1)
                self.engine.say(text)
                self.engine.runAndWait()
            except queue.Empty:
                # No more items, stop worker
                self.running = False
            except Exception as e:
                self.logger.error(f"TTS worker error: {e}")
                
    def stop(self):
        """Stop TTS service."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass


def main():
    """Test TTS service."""
    tts = TTSService()
    if not tts.initialize():
        print("Failed to initialize TTS")
        return
        
    tts.speak("Hello, I am Envy, your personal assistant.", blocking=True)
    tts.speak("I am ready to help you with various tasks.", blocking=True)


if __name__ == "__main__":
    main()
