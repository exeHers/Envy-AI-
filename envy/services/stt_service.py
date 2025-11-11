"""
Speech-to-Text service using Whisper with streaming support.
"""
import asyncio
import logging
import os
import tempfile
from typing import Optional, Callable, AsyncGenerator
import sounddevice as sd
import numpy as np
import whisper

from .base_service import BaseService

logger = logging.getLogger(__name__)


class STTService(BaseService):
    """Speech-to-Text service using Whisper."""
    
    def __init__(self, config: dict):
        super().__init__("STTService", config)
        self.model: Optional[whisper.Whisper] = None
        self.sample_rate = 16000
        self.recording = False
        self.audio_buffer = []
        
    async def start(self):
        """Initialize STT model."""
        logger.info("Initializing STT service")
        
        stt_config = self.config.get('stt', {})
        model_name = stt_config.get('model', 'small')
        device = stt_config.get('device', 'auto')
        
        try:
            # Load Whisper model
            logger.info(f"Loading Whisper model: {model_name}")
            self.model = whisper.load_model(model_name, device=device)
            logger.info("STT model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            # Fallback to base model
            try:
                self.model = whisper.load_model('base', device='cpu')
                logger.info("Loaded fallback base model")
            except Exception as e2:
                logger.error(f"Failed to load fallback model: {e2}")
                raise
        
        self.running = True
        logger.info("STT service ready")
    
    async def transcribe_audio_file(self, audio_path: str) -> str:
        """Transcribe an audio file."""
        if not self.model:
            raise RuntimeError("STT model not loaded")
        
        logger.info(f"Transcribing audio file: {audio_path}")
        try:
            result = self.model.transcribe(audio_path, language='en')
            text = result['text'].strip()
            logger.info(f"Transcription: {text}")
            return text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
    
    async def transcribe_stream(self, duration: float = 5.0) -> AsyncGenerator[str, None]:
        """Stream transcription from microphone."""
        if not self.model:
            raise RuntimeError("STT model not loaded")
        
        logger.info(f"Starting stream transcription for {duration}s")
        self.recording = True
        self.audio_buffer = []
        
        def audio_callback(indata, frames, time, status):
            if self.recording:
                self.audio_buffer.append(indata.copy())
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                callback=audio_callback
            ):
                # Record for specified duration
                await asyncio.sleep(duration)
                self.recording = False
                
                if not self.audio_buffer:
                    yield ""
                    return
                
                # Concatenate audio
                audio_data = np.concatenate(self.audio_buffer, axis=0)
                
                # Save to temp file for Whisper
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    import scipy.io.wavfile as wavfile
                    wavfile.write(tmp.name, self.sample_rate, (audio_data * 32767).astype(np.int16))
                    tmp_path = tmp.name
                
                try:
                    # Transcribe
                    result = self.model.transcribe(tmp_path, language='en')
                    text = result['text'].strip()
                    
                    # Stream words as they're recognized
                    if text:
                        words = text.split()
                        for word in words:
                            yield word
                            await asyncio.sleep(0.1)
                finally:
                    os.unlink(tmp_path)
                    
        except Exception as e:
            logger.error(f"Stream transcription error: {e}")
            yield ""
    
    async def record_and_transcribe(self, duration: float = 5.0) -> str:
        """Record audio and return full transcription."""
        text_parts = []
        async for word in self.transcribe_stream(duration):
            if word:
                text_parts.append(word)
        return " ".join(text_parts)
    
    async def stop(self):
        """Stop STT service."""
        logger.info("Stopping STT service")
        self.running = False
        self.recording = False
        logger.info("STT service stopped")
