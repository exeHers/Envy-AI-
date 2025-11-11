"""LLM Adapter supporting local and remote models."""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from .logger import setup_logger
from .config_loader import get_config


class LLMAdapter:
    """Adapter for LLM inference (local and remote fallback)."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = setup_logger("LLMAdapter", self.config.get("logging.file"))
        
        self.local_enabled = self.config.get("llm.local.enabled", True)
        self.remote_enabled = self.config.get("llm.remote.enabled", False)
        
        self.local_model = None
        self.local_model_path = None
        
    def initialize(self):
        """Initialize LLM model."""
        if self.local_enabled:
            return self._init_local_model()
        elif self.remote_enabled:
            return self._init_remote_client()
        else:
            self.logger.warning("No LLM backend enabled")
            return False
            
    def _init_local_model(self):
        """Initialize local LLM using llama-cpp-python."""
        try:
            try:
                from llama_cpp import Llama
            except ImportError:
                self.logger.warning("llama-cpp-python not installed, using fallback")
                return False
            
            model_path = self.config.get("llm.local.model_path")
            if not model_path:
                self.logger.warning("No local model path configured")
                return False
                
            base_dir = Path(__file__).parent.parent
            full_path = base_dir / model_path
            
            if not full_path.exists():
                self.logger.warning(f"Local model not found at {full_path}")
                # Try to find any GGUF model
                models_dir = base_dir / "models"
                if models_dir.exists():
                    gguf_models = list(models_dir.glob("*.gguf")) + list(models_dir.glob("*.ggml"))
                    if gguf_models:
                        full_path = gguf_models[0]
                        self.logger.info(f"Using model: {full_path}")
                    else:
                        self.logger.error("No GGUF/GGML models found")
                        return False
                else:
                    self.logger.error("Models directory not found")
                    return False
                    
            self.local_model_path = full_path
            
            n_ctx = self.config.get("llm.local.n_ctx", 2048)
            n_threads = self.config.get("llm.local.n_threads", 4)
            n_gpu_layers = self.config.get("llm.local.n_gpu_layers", 0)
            
            self.logger.info(f"Loading local LLM: {full_path}")
            self.logger.info(f"Context: {n_ctx}, Threads: {n_threads}, GPU layers: {n_gpu_layers}")
            
            self.local_model = Llama(
                model_path=str(full_path),
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            
            self.logger.info("Local LLM loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load local LLM: {e}")
            self.logger.info("Will attempt remote fallback if enabled")
            self.local_enabled = False
            return False
            
    def _init_remote_client(self):
        """Initialize remote LLM client."""
        if not self.remote_enabled:
            return False
            
        provider = self.config.get("llm.remote.provider", "none")
        if provider == "none":
            self.logger.warning("Remote LLM enabled but no provider configured")
            return False
            
        self.logger.info(f"Remote LLM provider: {provider}")
        return True
        
    def generate(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Generate response from LLM."""
        if self.local_model:
            return self._generate_local(prompt, max_tokens, temperature)
        elif self.remote_enabled:
            return self._generate_remote(prompt, max_tokens, temperature)
        else:
            return self._generate_fallback(prompt)
            
    def _generate_local(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Generate using local model."""
        try:
            if max_tokens is None:
                max_tokens = self.config.get("llm.local.max_tokens", 512)
            if temperature is None:
                temperature = self.config.get("llm.local.temperature", 0.7)
                
            self.logger.debug(f"Generating with local LLM: {prompt[:100]}...")
            
            output = self.local_model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["Human:", "User:", "\n\n"],
                echo=False
            )
            
            response = output['choices'][0]['text'].strip()
            self.logger.debug(f"Generated: {response[:100]}...")
            return response
            
        except Exception as e:
            self.logger.error(f"Local generation error: {e}")
            return self._generate_fallback(prompt)
            
    def _generate_remote(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Generate using remote API (free tier)."""
        try:
            import requests
            
            api_url = self.config.get("llm.remote.api_url")
            model = self.config.get("llm.remote.model")
            
            if not api_url:
                return self._generate_fallback(prompt)
                
            # Example for Hugging Face Inference API (free tier)
            headers = {
                "Content-Type": "application/json"
            }
            
            api_key = self.config.get("llm.remote.api_key")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
                
            data = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens or 512,
                    "temperature": temperature or 0.7,
                    "return_full_text": False
                }
            }
            
            response = requests.post(api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "").strip()
            
            return self._generate_fallback(prompt)
            
        except Exception as e:
            self.logger.error(f"Remote generation error: {e}")
            return self._generate_fallback(prompt)
            
    def _generate_fallback(self, prompt: str) -> str:
        """Fallback response when LLM is unavailable."""
        self.logger.warning("Using fallback responses (no LLM available)")
        
        # Simple rule-based responses
        prompt_lower = prompt.lower()
        
        if "create" in prompt_lower and "file" in prompt_lower:
            return "I'll create that file for you."
        elif "research" in prompt_lower or "search" in prompt_lower:
            return "I'll research that topic for you."
        elif "remind" in prompt_lower:
            return "I'll set that reminder for you."
        elif "system" in prompt_lower or "command" in prompt_lower:
            return "I'll execute that system command."
        elif any(word in prompt_lower for word in ["hello", "hi", "hey"]):
            return "Hello! How can I assist you today?"
        elif "help" in prompt_lower:
            return "I can help you with code creation, research, system control, and reminders."
        else:
            return "I understand. Let me help you with that."
            
    def classify_intent(self, text: str) -> Dict[str, Any]:
        """Classify user intent from text."""
        text_lower = text.lower()
        
        # Simple keyword-based classification
        intent = {
            "skill": None,
            "confidence": 0.0,
            "action": None,
            "params": {}
        }
        
        if any(word in text_lower for word in ["create", "write", "code", "file", "script"]):
            intent["skill"] = "CodeSkill"
            intent["confidence"] = 0.9
            intent["action"] = "create_file"
            # Extract filename
            words = text.split()
            for i, word in enumerate(words):
                if word.lower() in ["file", "create"] and i + 1 < len(words):
                    intent["params"]["filename"] = words[i + 1]
                    
        elif any(word in text_lower for word in ["research", "search", "find", "lookup"]):
            intent["skill"] = "ResearchSkill"
            intent["confidence"] = 0.9
            intent["action"] = "research"
            intent["params"]["query"] = text
            
        elif any(word in text_lower for word in ["remind", "reminder", "remember"]):
            intent["skill"] = "ReminderSkill"
            intent["confidence"] = 0.8
            intent["action"] = "set_reminder"
            intent["params"]["message"] = text
            
        elif any(word in text_lower for word in ["run", "execute", "command", "open", "close"]):
            intent["skill"] = "SysControlSkill"
            intent["confidence"] = 0.7
            intent["action"] = "execute_command"
            intent["params"]["command"] = text
            
        else:
            # Use LLM for ambiguous cases
            intent["confidence"] = 0.3
            
        return intent


def main():
    """Test LLM adapter."""
    adapter = LLMAdapter()
    if adapter.initialize():
        response = adapter.generate("Hello, how are you?")
        print(f"Response: {response}")
    else:
        print("Failed to initialize LLM")


if __name__ == "__main__":
    main()
