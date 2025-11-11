"""Text-to-Speech service using pyttsx3."""
import logging
import pyttsx3
import threading
from typing import Optional
from pathlib import Path
import wave
import numpy as np


logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service using pyttsx3."""
    
    def __init__(self, config):
        self.config = config
        self.engine: Optional[pyttsx3.Engine] = None
        self.rate = config.get("tts.rate", 150)
        self.volume = config.get("tts.volume", 0.9)
        self.streaming = config.get("tts.streaming", True)
        self._init_engine()
    
    def _init_engine(self):
        """Initialize TTS engine."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            # Try to set a better voice if available
            voices = self.engine.getProperty('voices')
            if voices:
                # Prefer female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            
            logger.info("TTS engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None
    
    def speak(self, text: str, async_mode: bool = True):
        """Speak text."""
        if not self.engine:
            logger.error("TTS engine not initialized")
            return
        
        if not text:
            return
        
        logger.info(f"Speaking: {text[:50]}...")
        
        def _speak():
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS failed: {e}")
        
        if async_mode:
            thread = threading.Thread(target=_speak, daemon=True)
            thread.start()
        else:
            _speak()
    
    def save_to_file(self, text: str, output_path: str):
        """Save speech to WAV file."""
        if not self.engine:
            logger.error("TTS engine not initialized")
            return False
        
        try:
            # pyttsx3 doesn't directly support saving, so we'll use a workaround
            # Save to temporary file and read it back
            temp_path = "/tmp/envy_tts_temp.wav"
            self.engine.save_to_file(text, temp_path)
            self.engine.runAndWait()
            
            # Copy to output path
            from shutil import copy
            copy(temp_path, output_path)
            logger.info(f"Saved TTS output to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save TTS to file: {e}")
            return False
    
    def get_available_voices(self):
        """Get list of available voices."""
        if not self.engine:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            return [{"id": v.id, "name": v.name} for v in voices]
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return []
