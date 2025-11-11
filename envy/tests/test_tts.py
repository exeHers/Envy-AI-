"""
Test text-to-speech service
"""
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.tts_service import TTSService

logger = logging.getLogger("test_tts")


def test_tts():
    """Test TTS service"""
    logger.info("Testing TTS service...")
    
    try:
        tts = TTSService()
        
        # Test by saving to file
        success, output = tts.test_speech("Envy text to speech system is operational.")
        
        if success:
            logger.info(f"✓ TTS test PASSED - output saved to {output}")
            return True
        else:
            logger.error(f"✗ TTS test FAILED: {output}")
            return False
            
    except Exception as e:
        logger.error(f"✗ TTS test FAILED: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = test_tts()
    sys.exit(0 if success else 1)
