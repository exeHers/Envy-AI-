"""
Wake Word Listener Service
Uses VOSK for lightweight "Envy" keyword detection
MIT License
"""

import os
import json
import queue
import sounddevice as sd
import vosk
import logging
from pathlib import Path
from typing import Callable, Optional
import threading

from .config_manager import get_config

logger = logging.getLogger(__name__)


class WakeListener:
    """Continuous wake word listener using VOSK"""
    
    def __init__(self, on_wake_callback: Callable[[], None]):
        self.config = get_config()
        self.on_wake_callback = on_wake_callback
        self.running = False
        self.audio_queue = queue.Queue()
        self.model = None
        self.recognizer = None
        
        # Configuration
        self.keyword = self.config.get('wake.keyword', 'envy').lower()
        self.sample_rate = self.config.get('wake.sample_rate', 16000)
        self.sensitivity = self.config.get('wake.sensitivity', 0.5)
        self.model_path = self.config.get('wake.model_path', 'models/vosk-model-small-en-us-0.15')
        
        logger.info(f"WakeListener initialized for keyword: '{self.keyword}'")
    
    def load_model(self):
        """Load VOSK model"""
        try:
            base_dir = Path(__file__).parent.parent
            model_full_path = base_dir / self.model_path
            
            if not model_full_path.exists():
                raise FileNotFoundError(
                    f"VOSK model not found at {model_full_path}. "
                    "Run scripts/download_models.sh to download required models."
                )
            
            logger.info(f"Loading VOSK model from {model_full_path}")
            vosk.SetLogLevel(-1)  # Suppress VOSK logs
            self.model = vosk.Model(str(model_full_path))
            self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)
            
            logger.info("VOSK model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load VOSK model: {e}")
            raise
    
    def audio_callback(self, indata, frames, time, status):
        """Audio input callback"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Add audio data to queue
        self.audio_queue.put(bytes(indata))
    
    def process_audio(self):
        """Process audio from queue and detect wake word"""
        logger.info("Audio processing thread started")
        
        while self.running:
            try:
                data = self.audio_queue.get(timeout=1)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').lower()
                    
                    if text:
                        logger.debug(f"Recognized: {text}")
                        
                        # Check for wake word
                        if self.keyword in text.split():
                            logger.info(f"Wake word '{self.keyword}' detected!")
                            self.on_wake_callback()
                else:
                    # Partial result
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get('partial', '').lower()
                    
                    if partial_text and self.keyword in partial_text.split():
                        logger.info(f"Wake word '{self.keyword}' detected (partial)!")
                        self.on_wake_callback()
                        # Clear recognizer state
                        self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
                        
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
    
    def start(self):
        """Start listening for wake word"""
        if self.running:
            logger.warning("WakeListener already running")
            return
        
        try:
            # Load model if not already loaded
            if self.model is None:
                self.load_model()
            
            self.running = True
            
            # Start audio processing thread
            self.process_thread = threading.Thread(target=self.process_audio, daemon=True)
            self.process_thread.start()
            
            # Start audio input stream
            logger.info(f"Starting audio input stream (sample rate: {self.sample_rate} Hz)")
            self.stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=self.audio_callback
            )
            self.stream.start()
            
            logger.info("WakeListener started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start WakeListener: {e}")
            self.running = False
            raise
    
    def stop(self):
        """Stop listening"""
        if not self.running:
            return
        
        logger.info("Stopping WakeListener...")
        self.running = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        if hasattr(self, 'process_thread'):
            self.process_thread.join(timeout=2)
        
        logger.info("WakeListener stopped")
    
    def is_running(self) -> bool:
        """Check if listener is running"""
        return self.running
