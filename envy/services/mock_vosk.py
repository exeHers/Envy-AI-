"""Mock VOSK implementation for testing without models."""
import json


class Model:
    """Mock VOSK Model."""
    def __init__(self, path):
        self.path = path


class KaldiRecognizer:
    """Mock VOSK Recognizer."""
    def __init__(self, model, sample_rate):
        self.model = model
        self.sample_rate = sample_rate
        self.partial_text = ""
        
    def SetWords(self, value):
        pass
        
    def AcceptWaveform(self, data):
        # Simulate detection every ~10 calls
        import random
        return random.random() > 0.9
        
    def Result(self):
        return json.dumps({"text": "envy detected"})
        
    def PartialResult(self):
        return json.dumps({"partial": "envy"})
