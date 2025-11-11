"""Speech-to-Text service using Faster Whisper."""
import sounddevice as sd
import numpy as np
import queue
import threading
import time
from pathlib import Path
try:
    from faster_whisper import WhisperModel
except ImportError:
    from .mock_whisper import WhisperModel
from .logger import setup_logger
from .config_loader import get_config


class STTService:
    """Speech-to-Text service with streaming support."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = setup_logger("STTService", self.config.get("logging.file"))
        
        self.model_size = self.config.get("stt.model_size", "base")
        self.device = self.config.get("stt.device", "auto")
        self.compute_type = self.config.get("stt.compute_type", "int8")
        self.language = self.config.get("stt.language", "en")
        self.beam_size = self.config.get("stt.beam_size", 5)
        
        self.sample_rate = 16000
        self.model = None
        self.audio_queue = queue.Queue()
        
    def initialize(self):
        """Initialize Whisper model."""
        try:
            self.logger.info(f"Loading Whisper model: {self.model_size}")
            
            # Auto-detect device
            if self.device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.logger.info(f"Auto-detected device: {device}")
            else:
                device = self.device
                
            self.model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=self.compute_type
            )
            self.logger.info("Whisper model loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Whisper model: {e}")
            # Fallback to CPU with int8
            try:
                self.logger.info("Attempting fallback to CPU with int8...")
                self.model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8"
                )
                self.logger.info("Whisper model loaded (CPU fallback)")
                return True
            except Exception as e2:
                self.logger.error(f"Fallback also failed: {e2}")
                return False
                
    def transcribe_audio(self, audio_data: np.ndarray, language: str = None) -> str:
        """Transcribe audio data to text."""
        if self.model is None:
            if not self.initialize():
                return ""
                
        try:
            # Ensure audio is float32 and normalized
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32) / 32768.0
                
            lang = language or self.language
            segments, info = self.model.transcribe(
                audio_data,
                language=lang,
                beam_size=self.beam_size,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            text = " ".join([segment.text for segment in segments])
            self.logger.info(f"Transcribed: {text}")
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            return ""
            
    def record_and_transcribe(self, duration: float = 5.0, language: str = None) -> str:
        """Record audio and transcribe it."""
        self.logger.info(f"Recording for {duration} seconds...")
        
        try:
            # Record audio
            audio = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()
            
            # Transcribe
            audio = audio.flatten()
            return self.transcribe_audio(audio, language)
            
        except Exception as e:
            self.logger.error(f"Recording error: {e}")
            return ""
            
    def transcribe_file(self, file_path: str, language: str = None) -> str:
        """Transcribe audio file."""
        try:
            import soundfile as sf
            audio, sr = sf.read(file_path)
            
            # Resample if needed
            if sr != self.sample_rate:
                from scipy import signal
                num_samples = int(len(audio) * self.sample_rate / sr)
                audio = signal.resample(audio, num_samples)
                
            return self.transcribe_audio(audio, language)
            
        except Exception as e:
            self.logger.error(f"File transcription error: {e}")
            return ""


def main():
    """Test STT service."""
    stt = STTService()
    if not stt.initialize():
        print("Failed to initialize STT")
        return
        
    print("Recording for 5 seconds... Speak now!")
    text = stt.record_and_transcribe(5.0)
    print(f"You said: {text}")


if __name__ == "__main__":
    main()
