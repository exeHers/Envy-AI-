"""Wake word listener service using VOSK."""
import json
import queue
import logging
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from typing import Optional, Callable
import threading
import time


class WakeWordListener:
    """Listens for wake word 'Envy' using VOSK."""
    
    def __init__(self, config, logger: Optional[logging.Logger] = None):
        self.config = config.wake_word
        self.logger = logger or logging.getLogger("envy.wake")
        self.model = None
        self.recognizer = None
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.callback: Optional[Callable] = None
        self.thread: Optional[threading.Thread] = None
        
    def initialize(self):
        """Initialize VOSK model."""
        try:
            model_path = self.config.model_path
            self.logger.info(f"Loading VOSK model from {model_path}")
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            self.recognizer.SetWords(True)
            self.logger.info("Wake word listener initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize wake word listener: {e}")
            return False
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio input."""
        if status:
            self.logger.warning(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def process_audio(self):
        """Process audio stream for wake word."""
        keyword = self.config.keyword.lower()
        sensitivity = self.config.sensitivity
        
        while self.is_listening:
            try:
                data = self.audio_queue.get(timeout=0.1)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').lower()
                    
                    if keyword in text:
                        confidence = 1.0  # Simplified - VOSK doesn't provide confidence
                        if confidence >= sensitivity:
                            self.logger.info(f"Wake word '{keyword}' detected!")
                            if self.callback:
                                self.callback()
                else:
                    # Partial result
                    partial = json.loads(self.recognizer.PartialResult())
                    text = partial.get('partial', '').lower()
                    if keyword in text:
                        self.logger.info(f"Wake word '{keyword}' detected (partial)!")
                        if self.callback:
                            self.callback()
                            
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing audio: {e}")
    
    def start(self, callback: Callable):
        """Start listening for wake word."""
        if self.model is None:
            if not self.initialize():
                return False
        
        self.callback = callback
        self.is_listening = True
        
        # Start audio stream
        try:
            self.stream = sd.InputStream(
                samplerate=16000,
                channels=1,
                dtype='int16',
                callback=self.audio_callback,
                blocksize=8000
            )
            self.stream.start()
            
            # Start processing thread
            self.thread = threading.Thread(target=self.process_audio, daemon=True)
            self.thread.start()
            
            self.logger.info("Wake word listener started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start wake word listener: {e}")
            self.is_listening = False
            return False
    
    def stop(self):
        """Stop listening."""
        self.is_listening = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        if self.thread:
            self.thread.join(timeout=2)
        self.logger.info("Wake word listener stopped")
