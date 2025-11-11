#!/usr/bin/env python3
"""
Speech-to-Text Service
Supports VOSK, Whisper, and WhisperX with streaming capabilities.
"""

import json
import logging
import sys
import tempfile
from pathlib import Path
from typing import Optional, Iterator

try:
    import sounddevice as sd
    import numpy as np
except ImportError:
    print("ERROR: Missing dependencies. Run: pip install sounddevice numpy")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service with multiple engine support."""
    
    def __init__(self, config: dict):
        self.config = config
        self.engine = config.get('engine', 'whisper')
        self.model_size = config.get('model_size', 'small')
        self.model_path = config.get('model_path', 'models/whisper-small')
        self.use_gpu = config.get('use_gpu', True)
        self.device = config.get('device', 'cuda')
        self.language = config.get('language', 'en')
        self.streaming = config.get('streaming', True)
        
        self.model = None
        self.processor = None
        
    def initialize(self) -> bool:
        """Initialize the STT engine."""
        try:
            if self.engine == 'whisper':
                return self._init_whisper()
            elif self.engine == 'whisperx':
                return self._init_whisperx()
            elif self.engine == 'vosk':
                return self._init_vosk()
            else:
                logger.error(f"Unknown STT engine: {self.engine}")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize STT: {e}")
            return False
    
    def _init_whisper(self) -> bool:
        """Initialize Whisper model."""
        try:
            import whisper
            
            logger.info(f"Loading Whisper model: {self.model_size}")
            
            # Check if model exists locally
            if Path(self.model_path).exists():
                self.model = whisper.load_model(self.model_path, device=self.device if self.use_gpu else 'cpu')
            else:
                self.model = whisper.load_model(self.model_size, device=self.device if self.use_gpu else 'cpu')
            
            logger.info("Whisper model loaded")
            return True
        except ImportError:
            logger.warning("Whisper not available, falling back to VOSK")
            self.engine = 'vosk'
            return self._init_vosk()
        except Exception as e:
            logger.error(f"Whisper initialization failed: {e}")
            return False
    
    def _init_whisperx(self) -> bool:
        """Initialize WhisperX model."""
        try:
            import whisperx
            
            logger.info(f"Loading WhisperX model: {self.model_size}")
            device = self.device if self.use_gpu else 'cpu'
            compute_type = "float16" if self.use_gpu else "int8"
            
            self.model = whisperx.load_model(
                self.model_size,
                device=device,
                compute_type=compute_type,
                language=self.language
            )
            
            logger.info("WhisperX model loaded")
            return True
        except ImportError:
            logger.warning("WhisperX not available, falling back to Whisper")
            self.engine = 'whisper'
            return self._init_whisper()
        except Exception as e:
            logger.error(f"WhisperX initialization failed: {e}")
            return False
    
    def _init_vosk(self) -> bool:
        """Initialize VOSK model."""
        try:
            import vosk
            
            model_path = Path(self.model_path).parent / 'vosk-model-small-en-us-0.15'
            if not model_path.exists():
                logger.error(f"VOSK model not found at {model_path}")
                return False
            
            self.model = vosk.Model(str(model_path))
            self.processor = vosk.KaldiRecognizer(self.model, 16000)
            self.processor.SetWords(True)
            
            logger.info("VOSK model loaded")
            return True
        except ImportError:
            logger.error("VOSK not available")
            return False
        except Exception as e:
            logger.error(f"VOSK initialization failed: {e}")
            return False
    
    def record_audio(self, duration: float = 5.0, sample_rate: int = 16000) -> np.ndarray:
        """Record audio from microphone."""
        logger.info(f"Recording audio for {duration} seconds...")
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        return audio.flatten()
    
    def transcribe(self, audio: Optional[np.ndarray] = None) -> str:
        """Transcribe audio to text."""
        if audio is None:
            audio = self.record_audio()
        
        try:
            if self.engine == 'whisper':
                result = self.model.transcribe(audio, language=self.language)
                text = result.get('text', '').strip()
                logger.info(f"Transcribed: {text}")
                return text
                
            elif self.engine == 'whisperx':
                result = self.model.transcribe(audio, batch_size=16)
                text = result['segments'][0]['text'] if result.get('segments') else ''
                logger.info(f"Transcribed: {text}")
                return text.strip()
                
            elif self.engine == 'vosk':
                if not self.processor:
                    return ""
                
                text_parts = []
                audio_bytes = (audio * 32767).astype(np.int16).tobytes()
                
                chunk_size = 4000
                for i in range(0, len(audio_bytes), chunk_size):
                    chunk = audio_bytes[i:i+chunk_size]
                    if self.processor.AcceptWaveform(chunk):
                        result = json.loads(self.processor.Result())
                        if result.get('text'):
                            text_parts.append(result['text'])
                
                final_result = json.loads(self.processor.FinalResult())
                if final_result.get('text'):
                    text_parts.append(final_result['text'])
                
                text = ' '.join(text_parts).strip()
                logger.info(f"Transcribed: {text}")
                return text
                
            else:
                logger.error(f"Unknown engine: {self.engine}")
                return ""
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
    
    def transcribe_stream(self) -> Iterator[str]:
        """Stream transcription results."""
        if not self.streaming:
            text = self.transcribe()
            yield text
            return
        
        logger.info("Starting streaming transcription...")
        # Simplified streaming - record in chunks
        chunk_duration = 2.0
        sample_rate = 16000
        
        while True:
            try:
                audio = self.record_audio(chunk_duration, sample_rate)
                text = self.transcribe(audio)
                if text:
                    yield text
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                break


def main():
    """Main entry point for STT service."""
    import yaml
    
    config_path = Path(__file__).parent.parent.parent / 'config' / 'envy.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    stt_config = config.get('stt', {})
    service = STTService(stt_config)
    
    if not service.initialize():
        sys.exit(1)
    
    try:
        text = service.transcribe()
        print(f"TRANSCRIPT:{text}")
    except KeyboardInterrupt:
        logger.info("STT service interrupted")
        sys.exit(0)


if __name__ == '__main__':
    main()
