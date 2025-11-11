"""LLM Adapter for local and remote LLM support."""
import logging
import requests
import json
from typing import Optional, Dict, Any
import time


class LLMAdapter:
    """Adapter for LLM inference (local llama.cpp or free remote endpoints)."""
    
    def __init__(self, config, logger: Optional[logging.Logger] = None):
        self.config = config.llm
        self.logger = logger or logging.getLogger("envy.llm")
        self.local_model = None
        self.initialized = False
        
    def initialize(self):
        """Initialize LLM (local or remote)."""
        try:
            if self.config.provider == "local":
                return self._initialize_local()
            elif self.config.provider == "remote_free":
                return self._initialize_remote()
            else:
                self.logger.error(f"Unknown LLM provider: {self.config.provider}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {e}")
            if self.config.fallback_enabled:
                self.logger.info("Attempting fallback to remote...")
                return self._initialize_remote()
            return False
    
    def _initialize_local(self) -> bool:
        """Initialize local LLM (llama.cpp)."""
        try:
            # Try to import llama-cpp-python
            try:
                from llama_cpp import Llama
                model_path = self.config.local.model_path
                self.logger.info(f"Loading local LLM from {model_path}")
                
                self.local_model = Llama(
                    model_path=model_path,
                    n_ctx=self.config.local.context_size,
                    n_gpu_layers=self.config.local.n_gpu_layers if self.config.local.use_mmap else 0,
                    use_mmap=self.config.local.use_mmap,
                    use_mlock=self.config.local.use_mlock,
                    verbose=False
                )
                self.initialized = True
                self.logger.info("Local LLM initialized")
                return True
            except ImportError:
                self.logger.warning("llama-cpp-python not installed, falling back to remote")
                if self.config.fallback_enabled:
                    return self._initialize_remote()
                return False
            except FileNotFoundError:
                self.logger.warning(f"Model file not found: {model_path}, falling back to remote")
                if self.config.fallback_enabled:
                    return self._initialize_remote()
                return False
        except Exception as e:
            self.logger.error(f"Failed to initialize local LLM: {e}")
            if self.config.fallback_enabled:
                return self._initialize_remote()
            return False
    
    def _initialize_remote(self) -> bool:
        """Initialize remote free LLM endpoint."""
        if not self.config.remote_free.enabled:
            self.logger.warning("Remote LLM not enabled in config")
            return False
        
        self.logger.info("Using remote free LLM endpoint")
        self.initialized = True
        return True
    
    def generate(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> str:
        """Generate response from LLM."""
        if not self.initialized:
            if not self.initialize():
                return "I'm sorry, I'm having trouble connecting to my language model."
        
        try:
            if self.config.provider == "local" and self.local_model:
                return self._generate_local(prompt, max_tokens, temperature)
            elif self.config.provider == "remote_free" or (self.config.fallback_enabled and not self.local_model):
                return self._generate_remote(prompt, max_tokens, temperature)
            else:
                return "I'm sorry, my language model is not available."
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "I encountered an error processing your request."
    
    def _generate_local(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using local LLM."""
        try:
            response = self.local_model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["\n\n", "Human:", "User:"],
                echo=False
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            self.logger.error(f"Local LLM generation error: {e}")
            raise
    
    def _generate_remote(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using remote free endpoint."""
        try:
            endpoint = self.config.remote_free.endpoint
            headers = {"Content-Type": "application/json"}
            if self.config.remote_free.api_key:
                headers["Authorization"] = f"Bearer {self.config.remote_free.api_key}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "return_full_text": False
                }
            }
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=self.config.remote_free.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    if 'generated_text' in result[0]:
                        return result[0]['generated_text'].strip()
                    elif 'text' in result[0]:
                        return result[0]['text'].strip()
                return str(result)
            else:
                self.logger.error(f"Remote LLM error: {response.status_code} - {response.text}")
                return "I'm sorry, the remote service is unavailable."
        except Exception as e:
            self.logger.error(f"Remote LLM generation error: {e}")
            return "I'm sorry, I couldn't reach the language service."
