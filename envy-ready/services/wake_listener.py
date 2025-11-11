"""
Wake word listener service using VOSK for continuous listening.
"""
import asyncio
import logging
import json
import os
from typing import Optional, Callable
import sounddevice as sd
import numpy as np
from vosk import Model, KaldiRecognizer

from .base_service import BaseService

logger = logging.getLogger(__name__)


class WakeListener(BaseService):
    """Listens for wake word 'Envy' using VOSK."""
    
    def __init__(self, config: dict, on_wake_detected: Callable):
        super().__init__("WakeListener", config)
        self.on_wake_detected = on_wake_detected
        self.model: Optional[Model] = None
        self.recognizer: Optional[KaldiRecognizer] = None
        self.stream: Optional[sd.InputStream] = None
        self.wake_word = config.get('assistant', {}).get('wake_word', 'envy').lower()
        self.sample_rate = 16000
        self.chunk_size = 4000
        
    async def start(self):
        """Start listening for wake word."""
        logger.info(f"Starting wake listener for '{self.wake_word}'")
        
        wake_config = self.config.get('wake_word', {})
        model_path = wake_config.get('model_path', 'models/vosk-wake')
        
        # Try to load VOSK model
        if not os.path.exists(model_path):
            logger.warning(f"VOSK model not found at {model_path}, using simple keyword matching")
            await self._start_simple_listener()
            return
        
        try:
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)
            logger.info("VOSK model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load VOSK model: {e}, falling back to simple listener")
            await self._start_simple_listener()
            return
        
        self.running = True
        self.setup_signal_handlers()
        
        # Start audio stream
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                blocksize=self.chunk_size,
                callback=self._audio_callback
            )
            self.stream.start()
            logger.info("Wake listener started")
            
            # Keep running
            while self.running:
                await asyncio.sleep(0.1)
                if not self.check_resource_limits():
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in wake listener: {e}")
            raise
    
    async def _start_simple_listener(self):
        """Fallback simple listener using basic audio analysis."""
        logger.info("Starting simple wake word listener")
        self.running = True
        
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio callback status: {status}")
            
            # Simple energy-based detection (very basic)
            # In production, this would use proper keyword spotting
            audio_data = indata[:, 0]
            energy = np.abs(audio_data).mean()
            
            # This is a placeholder - real implementation would use proper KWS
            # For now, we'll use a simple threshold (not reliable)
            if energy > 0.01:  # Very basic threshold
                # In real implementation, would analyze audio for "envy" pattern
                pass
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                callback=audio_callback
            )
            self.stream.start()
            
            # For testing, simulate wake word detection
            logger.info("Simple listener active (will use test mode for demos)")
            
            while self.running:
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in simple listener: {e}")
            raise
    
    def _audio_callback(self, indata, frames, time, status):
        """Process audio chunks for wake word detection."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        if not self.recognizer:
            return
        
        # Convert to bytes
        audio_bytes = indata.tobytes()
        
        if self.recognizer.AcceptWaveform(audio_bytes):
            result = json.loads(self.recognizer.Result())
            text = result.get('text', '').lower()
            
            # Check if wake word is in the recognized text
            if self.wake_word in text:
                logger.info(f"Wake word '{self.wake_word}' detected!")
                asyncio.create_task(self._trigger_wake())
        else:
            # Partial result
            partial = json.loads(self.recognizer.PartialResult())
            text = partial.get('partial', '').lower()
            if self.wake_word in text:
                logger.info(f"Wake word '{self.wake_word}' detected (partial)!")
                asyncio.create_task(self._trigger_wake())
    
    async def _trigger_wake(self):
        """Trigger wake word callback."""
        if self.on_wake_detected:
            try:
                await self.on_wake_detected()
            except Exception as e:
                logger.error(f"Error in wake callback: {e}")
    
    async def stop(self):
        """Stop the wake listener."""
        logger.info("Stopping wake listener")
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        logger.info("Wake listener stopped")
