#!/usr/bin/env python3
"""
Text-to-Speech Service
Supports pyttsx3 and Coqui TTS with streaming capabilities.
"""

import logging
import sys
import tempfile
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service with multiple engine support."""
    
    def __init__(self, config: dict):
        self.config = config
        self.engine = config.get('engine', 'pyttsx3')
        self.voice_id = config.get('voice_id')
        self.rate = config.get('rate', 150)
        self.volume = config.get('volume', 0.9)
        self.streaming = config.get('streaming', True)
        
        self.tts_engine = None
        
    def initialize(self) -> bool:
        """Initialize the TTS engine."""
        try:
            if self.engine == 'pyttsx3':
                return self._init_pyttsx3()
            elif self.engine == 'coqui':
                return self._init_coqui()
            else:
                logger.error(f"Unknown TTS engine: {self.engine}")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            return False
    
    def _init_pyttsx3(self) -> bool:
        """Initialize pyttsx3 engine."""
        try:
            import pyttsx3
            
            self.tts_engine = pyttsx3.init()
            
            # Configure voice
            voices = self.tts_engine.getProperty('voices')
            if voices and self.voice_id:
                for voice in voices:
                    if self.voice_id in voice.id.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            self.tts_engine.setProperty('rate', self.rate)
            self.tts_engine.setProperty('volume', self.volume)
            
            logger.info("pyttsx3 initialized")
            return True
        except ImportError:
            logger.error("pyttsx3 not available")
            return False
        except Exception as e:
            logger.error(f"pyttsx3 initialization failed: {e}")
            return False
    
    def _init_coqui(self) -> bool:
        """Initialize Coqui TTS engine."""
        try:
            from TTS.api import TTS
            
            logger.info("Loading Coqui TTS model...")
            self.tts_engine = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
            logger.info("Coqui TTS initialized")
            return True
        except ImportError:
            logger.warning("Coqui TTS not available, falling back to pyttsx3")
            self.engine = 'pyttsx3'
            return self._init_pyttsx3()
        except Exception as e:
            logger.error(f"Coqui TTS initialization failed: {e}")
            return False
    
    def speak(self, text: str, save_path: Optional[Path] = None) -> Optional[Path]:
        """Convert text to speech and play/save."""
        if not self.tts_engine:
            logger.error("TTS engine not initialized")
            return None
        
        try:
            if self.engine == 'pyttsx3':
                if save_path:
                    # Save to file
                    self.tts_engine.save_to_file(text, str(save_path))
                    self.tts_engine.runAndWait()
                    logger.info(f"Speech saved to {save_path}")
                    return save_path
                else:
                    # Speak directly
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                    logger.info(f"Spoke: {text[:50]}...")
                    return None
                    
            elif self.engine == 'coqui':
                if save_path:
                    output_path = save_path
                else:
                    output_path = Path(tempfile.gettempdir()) / f"envy_tts_{hash(text)}.wav"
                
                self.tts_engine.tts_to_file(text=text, file_path=str(output_path))
                logger.info(f"Speech saved to {output_path}")
                
                # Play audio file
                if not save_path:
                    self._play_audio(output_path)
                
                return output_path
                
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return None
    
    def _play_audio(self, audio_path: Path):
        """Play audio file using system player."""
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Linux':
                subprocess.run(['aplay', str(audio_path)], check=False)
            elif platform.system() == 'Darwin':
                subprocess.run(['afplay', str(audio_path)], check=False)
            elif platform.system() == 'Windows':
                subprocess.run(['powershell', '-c', f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync()'], check=False)
        except Exception as e:
            logger.warning(f"Could not play audio: {e}")


def main():
    """Main entry point for TTS service."""
    import yaml
    
    config_path = Path(__file__).parent.parent.parent / 'config' / 'envy.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    tts_config = config.get('tts', {})
    service = TTSService(tts_config)
    
    if not service.initialize():
        sys.exit(1)
    
    try:
        test_text = "Hello, I am Envy, your personal assistant."
        output_path = service.speak(test_text)
        if output_path:
            print(f"TTS_OUTPUT:{output_path}")
    except KeyboardInterrupt:
        logger.info("TTS service interrupted")
        sys.exit(0)


if __name__ == '__main__':
    main()
