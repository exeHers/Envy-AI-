"""Speech-to-Text service using Whisper."""
import logging
import whisper
import torch
import numpy as np
from typing import Optional, Callable
import io
import sounddevice as sd


logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service using OpenAI Whisper."""
    
    def __init__(self, config):
        self.config = config
        self.model_name = config.get("stt.model", "base")
        self.device = config.get("stt.device", "auto")
        self.language = config.get("stt.language", "en")
        self.streaming = config.get("stt.streaming", True)
        self.model: Optional[whisper.Whisper] = None
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model."""
        try:
            # Determine device
            if self.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self.device
            
            logger.info(f"Loading Whisper model '{self.model_name}' on {device}")
            self.model = whisper.load_model(self.model_name, device=device)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.model = None
    
    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe audio file."""
        if not self.model:
            logger.error("Whisper model not loaded")
            return ""
        
        try:
            result = self.model.transcribe(
                audio_path,
                language=self.language,
                task="transcribe"
            )
            text = result.get("text", "").strip()
            logger.info(f"Transcribed: {text}")
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
    
    def transcribe_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio data."""
        if not self.model:
            logger.error("Whisper model not loaded")
            return ""
        
        try:
            # Ensure audio is float32 and normalized
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            if audio_data.max() > 1.0:
                audio_data = audio_data / 32768.0
            
            result = self.model.transcribe(
                audio_data,
                language=self.language,
                task="transcribe"
            )
            text = result.get("text", "").strip()
            return text
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
    
    def record_and_transcribe(self, duration: float = 5.0, callback: Optional[Callable[[str], None]] = None) -> str:
        """Record audio and transcribe."""
        logger.info(f"Recording audio for {duration} seconds...")
        
        try:
            # Record audio
            sample_rate = 16000
            audio_data = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()
            
            # Transcribe
            text = self.transcribe_audio(audio_data.flatten(), sample_rate)
            
            if callback:
                callback(text)
            
            return text
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            return ""
