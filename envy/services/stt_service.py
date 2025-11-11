#!/usr/bin/env python3
"""
Speech-to-Text Service - Converts audio to text
Supports VOSK and Faster-Whisper with streaming
"""

import os
import sys
import wave
import logging
import tempfile
import numpy as np
import sounddevice as sd
from typing import Optional, Generator

logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text service with multiple engine support"""
    
    def __init__(self, config):
        self.config = config
        self.stt_config = config.get('stt', {})
        self.engine = self.stt_config.get('engine', 'faster-whisper')
        self.model_name = self.stt_config.get('model_name', 'base')
        self.language = self.stt_config.get('language', 'en')
        self.sample_rate = self.stt_config.get('sample_rate', 16000)
        self.streaming = self.stt_config.get('streaming', True)
        
        self.model = None
        self.recording = False
        
        logger.info(f"STTService initialized with engine: {self.engine}")
    
    def load_model(self):
        """Load STT model based on configured engine"""
        try:
            if self.engine == 'faster-whisper':
                self._load_faster_whisper()
            elif self.engine == 'vosk':
                self._load_vosk()
            elif self.engine == 'whisper':
                self._load_whisper()
            else:
                logger.error(f"Unknown STT engine: {self.engine}")
                return False
            
            logger.info(f"STT model loaded: {self.engine}/{self.model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to load STT model: {e}")
            return False
    
    def _load_faster_whisper(self):
        """Load Faster Whisper model (quantized, efficient)"""
        try:
            from faster_whisper import WhisperModel
            
            # Determine device
            device = "cuda" if self.config.get('profiles', {}).get(
                self.config.get('resource_profile', 'balanced'), {}
            ).get('use_gpu', False) else "cpu"
            
            # Use int8 quantization for better performance
            compute_type = "int8" if device == "cpu" else "float16"
            
            self.model = WhisperModel(
                self.model_name,
                device=device,
                compute_type=compute_type,
                download_root=os.path.join(self.config['general']['models_dir'], 'whisper')
            )
            logger.info(f"Faster-Whisper loaded on {device} with {compute_type}")
        except ImportError:
            logger.warning("faster-whisper not available, falling back to VOSK")
            self.engine = 'vosk'
            self._load_vosk()
    
    def _load_vosk(self):
        """Load VOSK model as fallback"""
        from vosk import Model
        
        models_dir = self.config['general']['models_dir']
        model_path = os.path.join(models_dir, 'vosk-model-small-en-us-0.15')
        
        if not os.path.exists(model_path):
            logger.error(f"VOSK model not found at {model_path}")
            raise FileNotFoundError("VOSK model not available")
        
        self.model = Model(model_path)
    
    def _load_whisper(self):
        """Load OpenAI Whisper model"""
        import whisper
        self.model = whisper.load_model(self.model_name)
    
    def transcribe_audio_file(self, audio_path: str) -> str:
        """Transcribe audio file to text"""
        if not self.model:
            if not self.load_model():
                return "[STT Error: Model not loaded]"
        
        try:
            if self.engine == 'faster-whisper':
                segments, info = self.model.transcribe(
                    audio_path,
                    language=self.language,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                text = " ".join([segment.text for segment in segments])
                return text.strip()
            
            elif self.engine == 'vosk':
                import json
                from vosk import KaldiRecognizer
                
                wf = wave.open(audio_path, "rb")
                rec = KaldiRecognizer(self.model, wf.getframerate())
                
                result_text = []
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        result_text.append(result.get('text', ''))
                
                final_result = json.loads(rec.FinalResult())
                result_text.append(final_result.get('text', ''))
                
                return " ".join(result_text).strip()
            
            elif self.engine == 'whisper':
                result = self.model.transcribe(audio_path, language=self.language)
                return result['text'].strip()
        
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return f"[STT Error: {str(e)}]"
    
    def record_and_transcribe(self, duration: int = 5) -> str:
        """Record audio from microphone and transcribe"""
        logger.info(f"Recording for {duration} seconds...")
        
        try:
            # Record audio
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16'
            )
            sd.wait()
            
            # Save to temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
                
                with wave.open(tmp_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(audio_data.tobytes())
            
            # Transcribe
            text = self.transcribe_audio_file(tmp_path)
            
            # Cleanup
            os.unlink(tmp_path)
            
            logger.info(f"Transcribed: {text}")
            return text
        
        except Exception as e:
            logger.error(f"Record and transcribe error: {e}")
            return f"[Recording Error: {str(e)}]"
    
    def stream_transcribe(self, audio_stream) -> Generator[str, None, None]:
        """Stream partial transcriptions (for real-time feedback)"""
        # Simplified streaming implementation
        # In production, implement proper streaming with VAD
        for chunk in audio_stream:
            # Process audio chunk and yield partial results
            yield "[Streaming transcription not fully implemented]"


def main():
    """Standalone test of STT service"""
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'general': {'models_dir': './models'},
        'stt': {
            'engine': 'faster-whisper',
            'model_name': 'tiny',  # Smallest for testing
            'language': 'en',
            'sample_rate': 16000,
            'streaming': True
        },
        'resource_profile': 'balanced',
        'profiles': {
            'balanced': {'use_gpu': False}
        }
    }
    
    stt = STTService(config)
    
    print("Testing STT Service...")
    print("Recording in 3 seconds... Say something!")
    
    import time
    time.sleep(3)
    
    text = stt.record_and_transcribe(duration=5)
    print(f"\nTranscription: {text}")


if __name__ == "__main__":
    main()
