#!/usr/bin/env python3
"""
Wake Word Listener Service - Continuously listens for "Envy" wake word
Uses VOSK for low-CPU keyword spotting
"""

import os
import sys
import json
import queue
import logging
import sounddevice as sd
from vosk import Model, KaldiRecognizer

logger = logging.getLogger(__name__)


class WakeListener:
    """Lightweight wake word detector using VOSK"""
    
    def __init__(self, config):
        self.config = config
        self.wake_config = config.get('wake_word', {})
        self.keyword = self.wake_config.get('keyword', 'envy').lower()
        self.sample_rate = self.wake_config.get('sample_rate', 16000)
        self.chunk_size = self.wake_config.get('chunk_size', 4096)
        self.sensitivity = self.wake_config.get('sensitivity', 0.5)
        
        self.model = None
        self.recognizer = None
        self.audio_queue = queue.Queue()
        self.running = False
        
        logger.info(f"WakeListener initialized for keyword: '{self.keyword}'")
    
    def load_model(self):
        """Load VOSK small model for wake word detection"""
        models_dir = self.config.get('general', {}).get('models_dir', './models')
        model_path = os.path.join(models_dir, 'vosk-model-small-en-us-0.15')
        
        # Check if model exists
        if not os.path.exists(model_path):
            logger.warning(f"VOSK model not found at {model_path}")
            logger.info("Attempting to download model...")
            self._download_model(model_path)
        
        try:
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)
            logger.info(f"VOSK model loaded from {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load VOSK model: {e}")
            return False
    
    def _download_model(self, model_path):
        """Download VOSK small model if not present"""
        import urllib.request
        import zipfile
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        zip_path = model_path + ".zip"
        
        logger.info(f"Downloading VOSK model from {model_url}...")
        try:
            urllib.request.urlretrieve(model_url, zip_path)
            logger.info("Extracting model...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(model_path))
            os.remove(zip_path)
            logger.info("Model downloaded and extracted successfully")
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            raise
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def start(self, on_wake_callback=None):
        """Start listening for wake word"""
        if not self.load_model():
            logger.error("Cannot start wake listener without model")
            return False
        
        self.running = True
        logger.info("Wake listener started. Say 'Envy' to activate...")
        
        try:
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=self.chunk_size,
                                   dtype='int16', channels=1, callback=self.audio_callback):
                while self.running:
                    data = self.audio_queue.get()
                    
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get('text', '').lower()
                        
                        if self.keyword in text:
                            logger.info(f"Wake word detected: '{text}'")
                            if on_wake_callback:
                                on_wake_callback()
                    else:
                        # Partial result (for debugging)
                        partial = json.loads(self.recognizer.PartialResult())
                        if partial.get('partial'):
                            logger.debug(f"Partial: {partial['partial']}")
        
        except Exception as e:
            logger.error(f"Wake listener error: {e}")
            return False
        
        return True
    
    def stop(self):
        """Stop listening"""
        self.running = False
        logger.info("Wake listener stopped")


def main():
    """Standalone test of wake listener"""
    logging.basicConfig(level=logging.INFO)
    
    # Minimal config for testing
    config = {
        'general': {'models_dir': './models'},
        'wake_word': {
            'keyword': 'envy',
            'sample_rate': 16000,
            'chunk_size': 4096,
            'sensitivity': 0.5
        }
    }
    
    listener = WakeListener(config)
    
    def on_wake():
        print("\n🎤 WAKE WORD DETECTED! Envy is listening...\n")
    
    try:
        listener.start(on_wake_callback=on_wake)
    except KeyboardInterrupt:
        print("\nStopping wake listener...")
        listener.stop()


if __name__ == "__main__":
    main()
