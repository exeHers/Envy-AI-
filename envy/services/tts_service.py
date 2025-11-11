"""
Text-to-Speech service using pyttsx3 with streaming support.
"""
import asyncio
import logging
import os
import tempfile
from typing import Optional
import pyttsx3

from .base_service import BaseService

logger = logging.getLogger(__name__)


class TTSService(BaseService):
    """Text-to-Speech service using pyttsx3."""
    
    def __init__(self, config: dict):
        super().__init__("TTSService", config)
        self.engine: Optional[pyttsx3.Engine] = None
        
    async def start(self):
        """Initialize TTS engine."""
        logger.info("Initializing TTS service")
        
        tts_config = self.config.get('tts', {})
        
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice settings
            rate = tts_config.get('rate', 150)
            volume = tts_config.get('volume', 0.8)
            
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
            # Try to set voice
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
            raise
        
        self.running = True
        logger.info("TTS service ready")
    
    async def speak(self, text: str, save_to_file: Optional[str] = None) -> str:
        """Speak text and optionally save to file."""
        if not self.engine:
            raise RuntimeError("TTS engine not initialized")
        
        logger.info(f"Speaking: {text[:50]}...")
        
        try:
            if save_to_file:
                # Save to file
                self.engine.save_to_file(text, save_to_file)
                self.engine.runAndWait()
                logger.info(f"Saved speech to {save_to_file}")
                return save_to_file
            else:
                # Speak directly
                self.engine.say(text)
                self.engine.runAndWait()
                logger.info("Speech completed")
                return ""
        except Exception as e:
            logger.error(f"TTS error: {e}")
            raise
    
    async def speak_async(self, text: str) -> None:
        """Speak text asynchronously."""
        await asyncio.to_thread(self.speak, text)
    
    async def stop(self):
        """Stop TTS service."""
        logger.info("Stopping TTS service")
        self.running = False
        if self.engine:
            self.engine.stop()
        logger.info("TTS service stopped")
