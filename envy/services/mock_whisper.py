"""Mock Faster Whisper implementation for testing without models."""


class WhisperModel:
    """Mock Whisper Model."""
    def __init__(self, model_size, device="cpu", compute_type="int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        
    def transcribe(self, audio, language=None, beam_size=5, vad_filter=True, vad_parameters=None):
        """Mock transcription."""
        # Return mock transcription
        segments = [
            MockSegment("This is a test transcription"),
            MockSegment("from the mock Whisper model")
        ]
        info = MockInfo()
        return segments, info


class MockSegment:
    """Mock transcription segment."""
    def __init__(self, text):
        self.text = text


class MockInfo:
    """Mock transcription info."""
    pass
