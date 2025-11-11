#!/usr/bin/env python3
"""
Wake Word Listener Service
Uses VOSK for continuous keyword spotting with minimal CPU usage.
"""

import json
import logging
import queue
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import sounddevice as sd
    import vosk
except ImportError:
    print("ERROR: Missing dependencies. Run: pip install sounddevice vosk")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WakeWordListener:
    """Continuous wake word detection using VOSK."""
    
    def __init__(self, config: dict):
        self.config = config
        self.wake_keyword = config.get('keyword', 'envy').lower()
        self.sensitivity = config.get('sensitivity', 0.5)
        self.model_path = config.get('model_path', 'models/vosk-model-small-en-us-0.15')
        self.timeout = config.get('timeout_seconds', 30)
        
        self.model = None
        self.rec = None
        self.running = False
        self.audio_queue = queue.Queue()
        
    def initialize(self) -> bool:
        """Initialize VOSK model and audio stream."""
        try:
            if not Path(self.model_path).exists():
                logger.error(f"VOSK model not found at {self.model_path}")
                logger.info("Downloading VOSK model...")
                self._download_model()
            
            logger.info(f"Loading VOSK model from {self.model_path}")
            self.model = vosk.Model(self.model_path)
            self.rec = vosk.KaldiRecognizer(self.model, 16000)
            self.rec.SetWords(True)
            
            logger.info("Wake word listener initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize wake listener: {e}")
            return False
    
    def _download_model(self):
        """Download VOSK model if missing."""
        import urllib.request
        import zipfile
        
        model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        zip_path = Path(self.model_path).parent / "vosk-model.zip"
        
        logger.info(f"Downloading VOSK model from {model_url}")
        urllib.request.urlretrieve(model_url, zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(Path(self.model_path).parent)
        
        zip_path.unlink()
        logger.info("VOSK model downloaded successfully")
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def listen(self) -> Optional[str]:
        """Listen for wake word and return when detected."""
        if not self.model or not self.rec:
            logger.error("Listener not initialized")
            return None
        
        self.running = True
        logger.info(f"Listening for wake word: '{self.wake_keyword}'")
        
        try:
            with sd.RawInputStream(
                samplerate=16000,
                channels=1,
                dtype='int16',
                blocksize=8000,
                callback=self.audio_callback
            ):
                start_time = time.time()
                
                while self.running:
                    if time.time() - start_time > self.timeout:
                        logger.debug("Wake word timeout")
                        return None
                    
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    
                    if self.rec.AcceptWaveform(data):
                        result = json.loads(self.rec.Result())
                        text = result.get('text', '').lower()
                        
                        if self.wake_keyword in text:
                            logger.info(f"Wake word detected: '{self.wake_keyword}'")
                            return self.wake_keyword
                    else:
                        partial = json.loads(self.rec.PartialResult())
                        text = partial.get('partial', '').lower()
                        if self.wake_keyword in text:
                            logger.info(f"Wake word detected (partial): '{self.wake_keyword}'")
                            return self.wake_keyword
                            
        except KeyboardInterrupt:
            logger.info("Wake listener interrupted")
        except Exception as e:
            logger.error(f"Error in wake listener: {e}")
        finally:
            self.running = False
        
        return None
    
    def stop(self):
        """Stop the listener."""
        self.running = False
        logger.info("Wake listener stopped")


def main():
    """Main entry point for wake listener service."""
    import yaml
    
    config_path = Path(__file__).parent.parent / 'config' / 'envy.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    wake_config = config.get('wake', {})
    listener = WakeWordListener(wake_config)
    
    if not listener.initialize():
        sys.exit(1)
    
    try:
        detected = listener.listen()
        if detected:
            print(f"WAKE_DETECTED:{detected}")
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        listener.stop()
        sys.exit(0)


if __name__ == '__main__':
    main()
