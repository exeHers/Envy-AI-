"""Speech-to-Text service."""
import json
import queue
import logging
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from typing import Optional, Callable, Generator
import threading


class STTService:
    """Speech-to-Text service using VOSK (with optional Whisper fallback)."""
    
    def __init__(self, config, logger: Optional[logging.Logger] = None):
        self.config = config.stt
        self.logger = logger or logging.getLogger("envy.stt")
        self.model = None
        self.recognizer = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.stream = None
        self.transcript_callback: Optional[Callable] = None
        
    def initialize(self):
        """Initialize STT model."""
        try:
            if self.config.engine == "vosk":
                model_path = self.config.vosk_model_path
                self.logger.info(f"Loading VOSK STT model from {model_path}")
                self.model = Model(model_path)
                self.recognizer = KaldiRecognizer(self.model, 16000)
                self.recognizer.SetWords(True)
                self.logger.info("STT service initialized (VOSK)")
                return True
            elif self.config.engine == "whisper":
                # Whisper would be initialized here if available
                self.logger.warning("Whisper not yet implemented, falling back to VOSK")
                return self.initialize()  # Fallback to VOSK
            else:
                self.logger.error(f"Unknown STT engine: {self.config.engine}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to initialize STT service: {e}")
            return False
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio input."""
        if status:
            self.logger.warning(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))
    
    def start_recording(self, callback: Optional[Callable] = None, duration: Optional[float] = None):
        """Start recording audio for transcription."""
        if self.model is None:
            if not self.initialize():
                return False
        
        self.transcript_callback = callback
        self.is_recording = True
        
        try:
            self.stream = sd.InputStream(
                samplerate=16000,
                channels=1,
                dtype='int16',
                callback=self.audio_callback,
                blocksize=8000
            )
            self.stream.start()
            
            # Process audio in a thread
            if duration:
                threading.Timer(duration, self.stop_recording).start()
            
            threading.Thread(target=self._process_recording, daemon=True).start()
            
            self.logger.info("STT recording started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start STT recording: {e}")
            self.is_recording = False
            return False
    
    def _process_recording(self):
        """Process recorded audio."""
        full_text = ""
        
        while self.is_recording:
            try:
                data = self.audio_queue.get(timeout=0.1)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '')
                    if text:
                        full_text += text + " "
                        if self.transcript_callback:
                            self.transcript_callback(text, final=True)
                else:
                    partial = json.loads(self.recognizer.PartialResult())
                    text = partial.get('partial', '')
                    if text and self.transcript_callback:
                        self.transcript_callback(text, final=False)
                        
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing audio: {e}")
        
        # Finalize
        if self.recognizer:
            final_result = json.loads(self.recognizer.FinalResult())
            final_text = final_result.get('text', '')
            if final_text:
                full_text += final_text
                if self.transcript_callback:
                    self.transcript_callback(final_text, final=True)
        
        self.logger.info(f"STT transcription complete: {full_text.strip()}")
        return full_text.strip()
    
    def stop_recording(self) -> str:
        """Stop recording and return final transcript."""
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        # Get final result
        if self.recognizer:
            final_result = json.loads(self.recognizer.FinalResult())
            return final_result.get('text', '').strip()
        return ""
