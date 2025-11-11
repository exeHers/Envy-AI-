"""
Speech-to-Text Service
Uses Faster-Whisper for efficient transcription
MIT License
"""

import os
import logging
import sounddevice as sd
import soundfile as sf
import numpy as np
from pathlib import Path
from typing import Optional, Callable
import threading
import time
import tempfile

from .config_manager import get_config

logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service using Faster-Whisper"""
    
    def __init__(self):
        self.config = get_config()
        self.model = None
        self.is_recording = False
        self.audio_data = []
        
        # Configuration
        self.model_size = self.config.get('stt.model_size', 'base')
        self.language = self.config.get('stt.language', 'en')
        self.sample_rate = self.config.get('wake.sample_rate', 16000)
        self.device = self.config.get('stt.device', 'auto')
        self.compute_type = self.config.get('stt.compute_type', 'int8')
        
        logger.info(f"STTService initialized (model: {self.model_size}, device: {self.device})")
    
    def load_model(self):
        """Load Faster-Whisper model"""
        try:
            from faster_whisper import WhisperModel
            
            # Determine device
            if self.device == 'auto':
                try:
                    import torch
                    device = 'cuda' if torch.cuda.is_available() else 'cpu'
                except ImportError:
                    device = 'cpu'
            else:
                device = self.device
            
            # Adjust compute type based on device
            compute_type = self.compute_type
            if device == 'cpu':
                compute_type = 'int8'  # CPU only supports int8
            
            logger.info(f"Loading Whisper model '{self.model_size}' on {device} with {compute_type}")
            
            self.model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type,
                download_root=str(Path(__file__).parent.parent / "models")
            )
            
            logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    def record_audio(self, duration: float = 5.0, silence_timeout: float = 2.0) -> Optional[str]:
        """
        Record audio from microphone with silence detection
        Returns path to temporary WAV file
        """
        try:
            logger.info(f"Recording audio (max {duration}s, silence timeout {silence_timeout}s)")
            
            self.audio_data = []
            self.is_recording = True
            
            # Energy threshold for silence detection
            energy_threshold = self.config.get('wake.energy_threshold', 300)
            
            # Record audio
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32'
            )
            
            start_time = time.time()
            last_sound_time = start_time
            
            # Monitor for silence
            while self.is_recording and (time.time() - start_time) < duration:
                sd.wait(100)  # Check every 100ms
                
                # Calculate energy of recent audio
                if len(recording) > 0:
                    recent_audio = recording[-int(0.1 * self.sample_rate):]
                    energy = np.sqrt(np.mean(recent_audio ** 2)) * 1000
                    
                    if energy > energy_threshold:
                        last_sound_time = time.time()
                    
                    # Stop if silence exceeds timeout
                    if time.time() - last_sound_time > silence_timeout:
                        logger.info("Silence detected, stopping recording")
                        break
            
            sd.stop()
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            sf.write(temp_file.name, recording, self.sample_rate)
            
            logger.info(f"Audio recorded to {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to record audio: {e}")
            return None
    
    def transcribe(self, audio_path: str) -> Optional[str]:
        """Transcribe audio file to text"""
        try:
            if self.model is None:
                self.load_model()
            
            logger.info(f"Transcribing audio from {audio_path}")
            
            segments, info = self.model.transcribe(
                audio_path,
                language=self.language,
                beam_size=5,
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Combine segments
            text = " ".join([segment.text for segment in segments]).strip()
            
            logger.info(f"Transcription: '{text}'")
            return text
            
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            return None
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(audio_path):
                    os.unlink(audio_path)
            except:
                pass
    
    def listen_and_transcribe(self, duration: float = 5.0, silence_timeout: float = 2.0) -> Optional[str]:
        """Record audio and transcribe in one operation"""
        audio_path = self.record_audio(duration, silence_timeout)
        if audio_path:
            return self.transcribe(audio_path)
        return None
    
    def stop_recording(self):
        """Stop current recording"""
        self.is_recording = False
