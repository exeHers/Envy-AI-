"""
Generate test audio files for testing
"""
import numpy as np
import soundfile as sf
import logging

logger = logging.getLogger("generate_test_audio")


def generate_test_audio(output_path: str, text: str = "Envy test"):
    """Generate a simple test audio file (sine wave as placeholder)"""
    try:
        # Generate a simple tone (this is a placeholder - real audio would be better)
        sample_rate = 16000
        duration = 2.0  # seconds
        frequency = 440  # Hz (A note)
        
        # Generate time array
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Generate sine wave
        audio = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Add some variation to simulate speech-like envelope
        envelope = np.exp(-t / (duration * 0.5))
        audio = audio * (0.3 + 0.7 * envelope)
        
        # Save as WAV
        sf.write(output_path, audio, sample_rate)
        
        logger.info(f"Generated test audio: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate test audio: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_test_audio("test_audio.wav", "Envy test")
