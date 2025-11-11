#!/usr/bin/env python3
"""
Text-to-Speech Service - Converts text to spoken audio
Supports pyttsx3 (cross-platform) and Coqui TTS (higher quality)
"""

import os
import sys
import logging
import tempfile
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service with multiple engine support"""
    
    def __init__(self, config):
        self.config = config
        self.tts_config = config.get('tts', {})
        self.engine_name = self.tts_config.get('engine', 'pyttsx3')
        self.voice_id = self.tts_config.get('voice_id', 0)
        self.rate = self.tts_config.get('rate', 175)
        self.volume = self.tts_config.get('volume', 0.9)
        self.save_audio = self.tts_config.get('save_audio', True)
        
        self.engine = None
        
        logger.info(f"TTSService initialized with engine: {self.engine_name}")
    
    def initialize(self):
        """Initialize TTS engine"""
        try:
            if self.engine_name == 'pyttsx3':
                self._init_pyttsx3()
            elif self.engine_name == 'coqui':
                self._init_coqui()
            else:
                logger.error(f"Unknown TTS engine: {self.engine_name}")
                return False
            
            logger.info(f"TTS engine initialized: {self.engine_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            return False
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine (cross-platform, reliable)"""
        import pyttsx3
        
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', self.rate)
        self.engine.setProperty('volume', self.volume)
        
        # Set voice if available
        voices = self.engine.getProperty('voices')
        if voices and len(voices) > self.voice_id:
            self.engine.setProperty('voice', voices[self.voice_id].id)
            logger.info(f"Using voice: {voices[self.voice_id].name}")
    
    def _init_coqui(self):
        """Initialize Coqui TTS (higher quality, more resource intensive)"""
        try:
            from TTS.api import TTS
            
            # Use a lightweight model
            model_name = "tts_models/en/ljspeech/tacotron2-DDC"
            self.engine = TTS(model_name=model_name, progress_bar=False, gpu=False)
            logger.info(f"Coqui TTS loaded with model: {model_name}")
        except ImportError:
            logger.warning("Coqui TTS not available, falling back to pyttsx3")
            self.engine_name = 'pyttsx3'
            self._init_pyttsx3()
    
    def speak(self, text: str, save_path: Optional[str] = None) -> bool:
        """Synthesize and speak text"""
        if not self.engine and not self.initialize():
            logger.error("TTS engine not initialized")
            return False
        
        try:
            logger.info(f"Speaking: {text[:50]}...")
            
            if self.engine_name == 'pyttsx3':
                # Save to file if requested
                if save_path or self.save_audio:
                    output_path = save_path or './artifacts/tts-output.wav'
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    self.engine.save_to_file(text, output_path)
                    self.engine.runAndWait()
                    logger.info(f"Audio saved to {output_path}")
                    
                    # Play the audio file
                    self._play_audio(output_path)
                else:
                    # Speak directly
                    self.engine.say(text)
                    self.engine.runAndWait()
            
            elif self.engine_name == 'coqui':
                # Coqui always saves to file first
                output_path = save_path or './artifacts/tts-output.wav'
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                self.engine.tts_to_file(text=text, file_path=output_path)
                logger.info(f"Audio saved to {output_path}")
                
                # Play the audio
                self._play_audio(output_path)
            
            return True
        
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return False
    
    def _play_audio(self, audio_path: str):
        """Play audio file using system player"""
        try:
            if sys.platform == 'linux':
                # Try multiple players
                players = ['aplay', 'paplay', 'ffplay']
                for player in players:
                    try:
                        subprocess.run([player, audio_path], 
                                     check=True, 
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                        logger.info(f"Played audio with {player}")
                        return
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                logger.warning("No audio player found on system")
            
            elif sys.platform == 'darwin':
                subprocess.run(['afplay', audio_path], check=True)
            
            elif sys.platform == 'win32':
                import winsound
                winsound.PlaySound(audio_path, winsound.SND_FILENAME)
        
        except Exception as e:
            logger.warning(f"Could not play audio: {e}")
    
    def speak_async(self, text: str):
        """Speak text asynchronously (non-blocking)"""
        import threading
        thread = threading.Thread(target=self.speak, args=(text,))
        thread.daemon = True
        thread.start()


def main():
    """Standalone test of TTS service"""
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'tts': {
            'engine': 'pyttsx3',
            'voice_id': 0,
            'rate': 175,
            'volume': 0.9,
            'save_audio': True
        }
    }
    
    tts = TTSService(config)
    
    print("Testing TTS Service...")
    test_text = "Hello, I am Envy, your personal AI assistant. How can I help you today?"
    
    tts.speak(test_text)
    print("TTS test complete!")


if __name__ == "__main__":
    main()
