"""
Wake word listener using VOSK for keyword spotting
Continuously listens for the wake word "Envy" with minimal CPU usage
"""
import json
import queue
import sys
import sounddevice as sd
import vosk
from pathlib import Path
from typing import Callable, Optional
import logging
import threading
import time

from services.config_loader import get_config


class WakeListener:
    """Listen for wake word using VOSK"""
    
    def __init__(self, on_wake: Callable = None):
        self.config = get_config()
        self.on_wake = on_wake
        self.logger = logging.getLogger("WakeListener")
        
        # Load wake word config
        self.keyword = self.config.get('wake_word.keyword', 'envy').lower()
        self.sensitivity = self.config.get('wake_word.sensitivity', 0.5)
        model_path = self.config.get('wake_word.model_path', 'models/vosk-model-small-en-us-0.15')
        
        # Resolve model path
        base_dir = Path(__file__).parent.parent
        self.model_path = base_dir / model_path
        
        # Audio settings
        self.sample_rate = 16000
        self.block_size = 4000  # ~0.25s chunks for low latency
        
        # State
        self.running = False
        self.model = None
        self.recognizer = None
        self.audio_queue = queue.Queue()
        self._thread = None
        
        self.logger.info(f"WakeListener initialized for keyword: '{self.keyword}'")
    
    def load_model(self):
        """Load VOSK model"""
        if not self.model_path.exists():
            self.logger.warning(f"Model not found at {self.model_path}, using fallback mode")
            # In fallback mode, we'll do simple keyword matching on any recognized text
            return False
        
        try:
            self.model = vosk.Model(str(self.model_path))
            self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)
            self.logger.info("VOSK model loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load VOSK model: {e}")
            return False
    
    def audio_callback(self, indata, frames, time_info, status):
        """Audio input callback"""
        if status:
            self.logger.warning(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def process_audio(self):
        """Process audio stream and detect wake word"""
        wake_detected_count = 0
        
        while self.running:
            try:
                data = self.audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            
            if self.recognizer is None:
                # Fallback mode: no real recognition
                continue
            
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get('text', '').lower()
                
                if text:
                    self.logger.debug(f"Recognized: {text}")
                    
                    # Check for wake word
                    if self.keyword in text:
                        wake_detected_count += 1
                        self.logger.info(f"Wake word detected! (count: {wake_detected_count})")
                        
                        if self.on_wake:
                            # Call wake callback in separate thread to avoid blocking
                            threading.Thread(target=self.on_wake, daemon=True).start()
            else:
                # Partial result
                partial = json.loads(self.recognizer.PartialResult())
                partial_text = partial.get('partial', '').lower()
                
                if partial_text and self.keyword in partial_text:
                    # Early detection in partial result
                    pass  # Could trigger here for lower latency
    
    def start(self):
        """Start listening for wake word"""
        if self.running:
            self.logger.warning("WakeListener already running")
            return
        
        self.logger.info("Starting wake word listener...")
        
        # Load model
        model_loaded = self.load_model()
        if not model_loaded:
            self.logger.warning("Running in fallback mode without VOSK model")
        
        self.running = True
        
        # Start audio processing thread
        self._thread = threading.Thread(target=self.process_audio, daemon=True)
        self._thread.start()
        
        # Start audio stream
        try:
            self.stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                dtype='int16',
                channels=1,
                callback=self.audio_callback
            )
            self.stream.start()
            self.logger.info("Wake word listener started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start audio stream: {e}")
            self.running = False
            raise
    
    def stop(self):
        """Stop listening"""
        if not self.running:
            return
        
        self.logger.info("Stopping wake word listener...")
        self.running = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        if self._thread:
            self._thread.join(timeout=2.0)
        
        self.logger.info("Wake word listener stopped")
    
    def test_detection(self, test_audio_path: str = None) -> bool:
        """Test wake word detection with audio file or live mic"""
        self.logger.info("Testing wake word detection...")
        
        if test_audio_path:
            # Test with audio file
            import soundfile as sf
            data, samplerate = sf.read(test_audio_path)
            
            if self.recognizer is None:
                self.load_model()
            
            if self.recognizer:
                # Resample if needed
                if samplerate != self.sample_rate:
                    from scipy import signal
                    data = signal.resample(data, int(len(data) * self.sample_rate / samplerate))
                
                # Convert to int16
                data = (data * 32767).astype('int16')
                
                # Process
                if self.recognizer.AcceptWaveform(data.tobytes()):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').lower()
                    self.logger.info(f"Test recognized: {text}")
                    
                    if self.keyword in text:
                        self.logger.info("✓ Wake word detected in test!")
                        return True
                    else:
                        self.logger.warning("✗ Wake word NOT detected in test")
                        return False
        
        return False


def main():
    """Test wake listener standalone"""
    logging.basicConfig(level=logging.INFO)
    
    def on_wake():
        print("\n*** WAKE WORD DETECTED! ***\n")
    
    listener = WakeListener(on_wake=on_wake)
    listener.start()
    
    try:
        print("Listening for wake word 'Envy'... (Ctrl+C to stop)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        listener.stop()


if __name__ == "__main__":
    main()
