"""Text-to-Speech service."""
import logging
import pyttsx3
import threading
from typing import Optional
from pathlib import Path


class TTSService:
    """Text-to-Speech service using pyttsx3."""
    
    def __init__(self, config, logger: Optional[logging.Logger] = None):
        self.config = config.tts
        self.logger = logger or logging.getLogger("envy.tts")
        self.engine = None
        self.is_speaking = False
        
    def initialize(self):
        """Initialize TTS engine."""
        try:
            if self.config.engine == "pyttsx3":
                self.engine = pyttsx3.init()
                
                # Set properties
                if self.config.voice_id:
                    voices = self.engine.getProperty('voices')
                    for voice in voices:
                        if self.config.voice_id in voice.id:
                            self.engine.setProperty('voice', voice.id)
                            break
                
                self.engine.setProperty('rate', self.config.rate)
                self.engine.setProperty('volume', self.config.volume)
                
                self.logger.info("TTS service initialized (pyttsx3)")
                return True
            else:
                self.logger.error(f"Unknown TTS engine: {self.config.engine}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS service: {e}")
            return False
    
    def speak(self, text: str, async_mode: bool = True) -> bool:
        """Speak text."""
        if self.engine is None:
            if not self.initialize():
                return False
        
        try:
            if async_mode:
                # Speak in background thread
                def _speak():
                    self.is_speaking = True
                    self.engine.say(text)
                    self.engine.runAndWait()
                    self.is_speaking = False
                
                threading.Thread(target=_speak, daemon=True).start()
            else:
                self.is_speaking = True
                self.engine.say(text)
                self.engine.runAndWait()
                self.is_speaking = False
            
            self.logger.info(f"TTS: {text[:50]}...")
            return True
        except Exception as e:
            self.logger.error(f"Failed to speak: {e}")
            self.is_speaking = False
            return False
    
    def save_to_file(self, text: str, output_path: str) -> bool:
        """Save speech to WAV file."""
        if self.engine is None:
            if not self.initialize():
                return False
        
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            self.engine.save_to_file(text, str(output_file))
            self.engine.runAndWait()
            
            self.logger.info(f"TTS saved to {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save TTS to file: {e}")
            return False
    
    def stop(self):
        """Stop speaking."""
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
        self.is_speaking = False
