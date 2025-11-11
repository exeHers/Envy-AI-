"""
Text-to-Speech service using pyttsx3
Streaming TTS for responsive voice output
"""
import pyttsx3
import logging
import threading
import queue
from pathlib import Path
from typing import Optional
import tempfile
import os

from services.config_loader import get_config


class TTSService:
    """Text-to-Speech service"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger("TTSService")
        
        # Load TTS config
        self.engine_name = self.config.get('tts.engine', 'pyttsx3')
        self.rate = self.config.get('tts.rate', 150)
        self.volume = self.config.get('tts.volume', 0.9)
        self.voice_id = self.config.get('tts.voice_id', None)
        
        # Initialize engine
        self.engine = None
        self.speech_queue = queue.Queue()
        self.speaking = False
        self._thread = None
        
        self.logger.info(f"TTSService initialized with engine: {self.engine_name}")
    
    def initialize_engine(self):
        """Initialize TTS engine"""
        try:
            self.engine = pyttsx3.init()
            
            # Set properties
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Set voice if specified
            if self.voice_id:
                self.engine.setProperty('voice', self.voice_id)
            
            self.logger.info("TTS engine initialized successfully")
            
            # Log available voices
            voices = self.engine.getProperty('voices')
            self.logger.debug(f"Available voices: {len(voices)}")
            for i, voice in enumerate(voices[:3]):  # Log first 3
                self.logger.debug(f"  Voice {i}: {voice.name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            return False
    
    def speak(self, text: str, blocking: bool = False):
        """Speak text (async by default)"""
        if not text:
            return
        
        self.logger.info(f"Speaking: {text[:50]}...")
        
        if self.engine is None:
            self.initialize_engine()
        
        if self.engine is None:
            self.logger.error("TTS engine not available")
            return
        
        if blocking:
            # Synchronous speech
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                self.logger.error(f"Speech failed: {e}")
        else:
            # Asynchronous speech via queue
            self.speech_queue.put(text)
            if not self.speaking:
                self._start_speech_worker()
    
    def _start_speech_worker(self):
        """Start background speech worker thread"""
        if self._thread and self._thread.is_alive():
            return
        
        self.speaking = True
        self._thread = threading.Thread(target=self._speech_worker, daemon=True)
        self._thread.start()
    
    def _speech_worker(self):
        """Background worker to process speech queue"""
        while self.speaking or not self.speech_queue.empty():
            try:
                text = self.speech_queue.get(timeout=1.0)
                
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    self.logger.error(f"Speech failed: {e}")
                
                self.speech_queue.task_done()
                
            except queue.Empty:
                continue
        
        self.speaking = False
    
    def stop(self):
        """Stop current speech"""
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
        
        self.speaking = False
        
        # Clear queue
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except:
                break
    
    def save_to_file(self, text: str, output_path: str):
        """Save speech to audio file"""
        self.logger.info(f"Saving speech to file: {output_path}")
        
        if self.engine is None:
            self.initialize_engine()
        
        if self.engine is None:
            self.logger.error("TTS engine not available")
            return False
        
        try:
            self.engine.save_to_file(text, output_path)
            self.engine.runAndWait()
            self.logger.info(f"Speech saved to {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save speech: {e}")
            return False
    
    def test_speech(self, test_text: str = None) -> tuple[bool, str]:
        """Test TTS service"""
        if test_text is None:
            test_text = "Envy text to speech system is operational."
        
        self.logger.info("Testing TTS service...")
        
        # Test by saving to file
        try:
            base_dir = Path(__file__).parent.parent
            output_dir = base_dir / "artifacts" / "tests"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / "tts-test-output.wav"
            success = self.save_to_file(test_text, str(output_path))
            
            if success and output_path.exists():
                self.logger.info(f"✓ TTS test successful: {output_path}")
                return True, str(output_path)
            else:
                self.logger.error("✗ TTS test failed")
                return False, "Failed to generate audio"
                
        except Exception as e:
            self.logger.error(f"TTS test failed: {e}")
            return False, str(e)
    
    def list_voices(self):
        """List available voices"""
        if self.engine is None:
            self.initialize_engine()
        
        if self.engine is None:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            return [{'id': v.id, 'name': v.name, 'languages': v.languages} 
                   for v in voices]
        except Exception as e:
            self.logger.error(f"Failed to list voices: {e}")
            return []


def main():
    """Test TTS service standalone"""
    logging.basicConfig(level=logging.INFO)
    
    tts = TTSService()
    
    # Test speech
    print("Testing TTS...")
    tts.speak("Hello, I am Envy, your personal assistant.", blocking=True)
    
    # List voices
    voices = tts.list_voices()
    print(f"\nAvailable voices: {len(voices)}")
    for v in voices[:5]:
        print(f"  - {v['name']}")


if __name__ == "__main__":
    main()
