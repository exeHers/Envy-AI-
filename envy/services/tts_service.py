"""
Text-to-Speech Service
Uses pyttsx3 for cross-platform TTS
MIT License
"""

import os
import logging
import pyttsx3
import threading
from pathlib import Path
from typing import Optional
import subprocess
import platform

from .config_manager import get_config

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service using pyttsx3"""
    
    def __init__(self):
        self.config = get_config()
        self.engine = None
        self.lock = threading.Lock()
        
        # Configuration
        self.rate = self.config.get('tts.rate', 175)
        self.volume = self.config.get('tts.volume', 0.9)
        self.output_path = self.config.get('tts.output_path', 'artifacts/tts-output.wav')
        
        logger.info("TTSService initialized")
    
    def initialize(self):
        """Initialize TTS engine"""
        try:
            if self.engine is None:
                logger.info("Initializing pyttsx3 engine")
                self.engine = pyttsx3.init()
                
                # Set properties
                self.engine.setProperty('rate', self.rate)
                self.engine.setProperty('volume', self.volume)
                
                # Log available voices
                voices = self.engine.getProperty('voices')
                logger.info(f"Available voices: {len(voices)}")
                for i, voice in enumerate(voices[:3]):  # Log first 3
                    logger.debug(f"Voice {i}: {voice.name}")
                
                logger.info("pyttsx3 engine initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            raise
    
    def speak(self, text: str, save_to_file: bool = True) -> bool:
        """
        Speak text aloud and optionally save to file
        Returns True if successful
        """
        try:
            if not text:
                logger.warning("Empty text provided to TTS")
                return False
            
            with self.lock:
                if self.engine is None:
                    self.initialize()
                
                logger.info(f"Speaking: '{text}'")
                
                # Save to file if requested
                if save_to_file:
                    output_path = Path(__file__).parent.parent / self.output_path
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        self.engine.save_to_file(text, str(output_path))
                        self.engine.runAndWait()
                        logger.info(f"Audio saved to {output_path}")
                    except Exception as e:
                        logger.warning(f"Could not save to file: {e}")
                
                # Speak the text
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    logger.warning(f"Could not play audio: {e}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to speak text: {e}")
            return False
    
    def speak_async(self, text: str, save_to_file: bool = True):
        """Speak text asynchronously in a separate thread"""
        thread = threading.Thread(target=self.speak, args=(text, save_to_file), daemon=True)
        thread.start()
    
    def stop(self):
        """Stop current speech"""
        try:
            if self.engine:
                self.engine.stop()
        except Exception as e:
            logger.error(f"Failed to stop TTS: {e}")
    
    def shutdown(self):
        """Shutdown TTS engine"""
        try:
            if self.engine:
                self.engine.stop()
                self.engine = None
                logger.info("TTS engine shutdown")
        except Exception as e:
            logger.error(f"Failed to shutdown TTS: {e}")
