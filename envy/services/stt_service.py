"""
Speech-to-Text service using VOSK or Whisper
Streaming STT for low latency
"""
import json
import queue
import sounddevice as sd
import soundfile as sf
import vosk
import numpy as np
from pathlib import Path
from typing import Optional, Callable
import logging
import threading
import time

from services.config_loader import get_config


class STTService:
    """Speech-to-Text service with streaming support"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger("STTService")
        
        # Load STT config
        self.engine = self.config.get('stt.engine', 'vosk')
        model_path = self.config.get('stt.model_path', 'models/vosk-model-en-us-0.22')
        self.timeout = self.config.get('stt.timeout', 10)
        self.streaming = self.config.get('stt.streaming', True)
        
        # Resolve model path
        base_dir = Path(__file__).parent.parent
        self.model_path = base_dir / model_path
        
        # Audio settings
        self.sample_rate = 16000
        self.block_size = 4000
        
        # State
        self.model = None
        self.recognizer = None
        self.recording = False
        self.audio_queue = queue.Queue()
        
        self.logger.info(f"STTService initialized with engine: {self.engine}")
    
    def load_model(self):
        """Load STT model"""
        if self.engine == 'vosk':
            return self._load_vosk_model()
        else:
            self.logger.warning(f"Engine {self.engine} not implemented, using VOSK")
            return self._load_vosk_model()
    
    def _load_vosk_model(self):
        """Load VOSK model"""
        if not self.model_path.exists():
            self.logger.error(f"Model not found at {self.model_path}")
            return False
        
        try:
            self.model = vosk.Model(str(self.model_path))
            self.logger.info("VOSK STT model loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load VOSK model: {e}")
            return False
    
    def transcribe_audio_file(self, audio_path: str) -> str:
        """Transcribe audio from file"""
        self.logger.info(f"Transcribing audio file: {audio_path}")
        
        if self.model is None:
            self.load_model()
        
        if self.model is None:
            return "[STT model not available]"
        
        try:
            # Read audio file
            data, samplerate = sf.read(audio_path)
            
            # Ensure mono
            if len(data.shape) > 1:
                data = data[:, 0]
            
            # Resample if needed
            if samplerate != self.sample_rate:
                from scipy import signal
                num_samples = int(len(data) * self.sample_rate / samplerate)
                data = signal.resample(data, num_samples)
            
            # Convert to int16
            data = (data * 32767).astype('int16')
            
            # Create recognizer
            rec = vosk.KaldiRecognizer(self.model, self.sample_rate)
            rec.SetWords(True)
            
            # Process audio
            rec.AcceptWaveform(data.tobytes())
            result = json.loads(rec.FinalResult())
            
            text = result.get('text', '')
            self.logger.info(f"Transcription: {text}")
            return text
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            return f"[Error: {e}]"
    
    def record_and_transcribe(self, duration: float = None, 
                             on_partial: Callable[[str], None] = None) -> str:
        """Record audio and transcribe with optional streaming partial results"""
        self.logger.info("Starting recording and transcription...")
        
        if self.model is None:
            self.load_model()
        
        if self.model is None:
            return "[STT model not available]"
        
        # Create recognizer
        rec = vosk.KaldiRecognizer(self.model, self.sample_rate)
        rec.SetWords(True)
        
        final_text = ""
        audio_data = []
        silence_start = None
        silence_threshold = self.timeout
        
        def audio_callback(indata, frames, time_info, status):
            if status:
                self.logger.warning(f"Audio status: {status}")
            audio_data.append(indata.copy())
            self.audio_queue.put(bytes(indata))
        
        try:
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=self.block_size,
                                  dtype='int16', channels=1, callback=audio_callback):
                
                self.logger.info("Recording... (speak now)")
                start_time = time.time()
                last_speech_time = start_time
                
                while True:
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                        
                        # Check for speech activity
                        audio_level = np.abs(np.frombuffer(data, dtype=np.int16)).mean()
                        
                        if audio_level > 100:  # Speech detected
                            last_speech_time = time.time()
                        
                        # Process with recognizer
                        if rec.AcceptWaveform(data):
                            result = json.loads(rec.Result())
                            text = result.get('text', '')
                            if text:
                                final_text += text + " "
                                last_speech_time = time.time()
                                self.logger.debug(f"Recognized: {text}")
                        else:
                            # Partial result
                            if self.streaming and on_partial:
                                partial = json.loads(rec.PartialResult())
                                partial_text = partial.get('partial', '')
                                if partial_text:
                                    on_partial(partial_text)
                        
                        # Check for timeout
                        if time.time() - last_speech_time > silence_threshold:
                            self.logger.info("Silence timeout reached")
                            break
                        
                        # Check duration limit
                        if duration and time.time() - start_time > duration:
                            self.logger.info("Duration limit reached")
                            break
                            
                    except queue.Empty:
                        # Check timeout even without audio
                        if time.time() - last_speech_time > silence_threshold:
                            break
                
                # Get final result
                final_result = json.loads(rec.FinalResult())
                final_text += final_result.get('text', '')
                
                self.logger.info(f"Final transcription: {final_text}")
                return final_text.strip()
                
        except Exception as e:
            self.logger.error(f"Recording/transcription failed: {e}")
            return f"[Error: {e}]"
        finally:
            # Clear queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except:
                    break
    
    def test_transcription(self, test_audio_path: str = None) -> tuple[bool, str]:
        """Test STT service"""
        self.logger.info("Testing STT service...")
        
        if test_audio_path and Path(test_audio_path).exists():
            text = self.transcribe_audio_file(test_audio_path)
            success = len(text) > 0 and not text.startswith('[')
            return success, text
        else:
            self.logger.warning("No test audio provided")
            return False, "No test audio"


def main():
    """Test STT service standalone"""
    logging.basicConfig(level=logging.INFO)
    
    stt = STTService()
    
    def on_partial(text):
        print(f"Partial: {text}")
    
    print("Recording for 5 seconds...")
    text = stt.record_and_transcribe(duration=5, on_partial=on_partial)
    print(f"\nFinal transcription: {text}")


if __name__ == "__main__":
    main()
