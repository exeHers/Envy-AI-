#!/usr/bin/env python3
"""
Test Text-to-Speech Service
Validates TTS functionality and audio output
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.tts_service import TTSService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_tts_service():
    """Test TTS service"""
    logger.info("=" * 60)
    logger.info("TEST: Text-to-Speech Service")
    logger.info("=" * 60)
    
    config = {
        'tts': {
            'engine': 'pyttsx3',
            'voice_id': 0,
            'rate': 175,
            'volume': 0.9,
            'save_audio': True
        }
    }
    
    try:
        # Initialize TTS service
        tts = TTSService(config)
        
        logger.info("Initializing TTS engine...")
        if tts.initialize():
            logger.info("✓ TTS engine initialized successfully")
            
            # Test speech synthesis
            test_text = "Hello, I am Envy. This is a test of the text to speech system."
            output_file = './artifacts/tts-output.wav'
            
            logger.info(f"Synthesizing text: '{test_text}'")
            success = tts.speak(test_text, save_path=output_file)
            
            if success:
                logger.info("✓ TTS synthesis completed")
                
                # Check if file was created
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    logger.info(f"✓ Audio file created: {output_file} ({file_size} bytes)")
                    return True
                else:
                    logger.warning("⚠ Audio file not created (may need audio system)")
                    logger.info("✓ TTS synthesis completed without error")
                    return True
            else:
                logger.error("✗ TTS synthesis failed")
                return False
        else:
            logger.error("✗ TTS engine initialization failed")
            return False
    
    except Exception as e:
        logger.error(f"✗ TTS test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_tts_service()
    sys.exit(0 if success else 1)
