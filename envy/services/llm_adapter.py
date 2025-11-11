"""LLM Adapter supporting local llama.cpp and free remote endpoints."""
import logging
import requests
from typing import Optional, Dict, Any
from pathlib import Path
import json


logger = logging.getLogger(__name__)


class LLMAdapter:
    """Adapter for LLM inference - supports local and remote."""
    
    def __init__(self, config):
        self.config = config
        self.provider = config.get("llm.provider", "local")
        self.local_config = config.get("llm.local", {})
        self.remote_config = config.get("llm.remote_free", {})
        self.local_model = None
        self._init_local_model()
    
    def _init_local_model(self):
        """Initialize local LLM model (llama.cpp)."""
        if self.provider != "local":
            return
        
        try:
            from llama_cpp import Llama
            
            model_path = self.local_config.get("model_path", "models/llama-2-7b-chat-q4_0.gguf")
            model_path = Path(model_path)
            
            if not model_path.exists():
                logger.warning(f"Local LLM model not found at {model_path}")
                logger.info("Falling back to remote free endpoint")
                self.provider = "remote_free"
                return
            
            logger.info(f"Loading local LLM from {model_path}")
            self.local_model = Llama(
                model_path=str(model_path),
                n_ctx=self.local_config.get("context_size", 2048),
                n_gpu_layers=self.local_config.get("n_gpu_layers", 20),
                n_threads=self.local_config.get("n_threads", 4),
                verbose=False
            )
            logger.info("Local LLM loaded successfully")
        except ImportError:
            logger.warning("llama-cpp-python not available, using remote fallback")
            self.provider = "remote_free"
        except Exception as e:
            logger.error(f"Failed to load local LLM: {e}")
            logger.info("Falling back to remote free endpoint")
            self.provider = "remote_free"
    
    def _generate_local(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate response using local model."""
        if not self.local_model:
            return ""
        
        try:
            max_tokens = max_tokens or self.local_config.get("max_tokens", 512)
            temperature = self.local_config.get("temperature", 0.7)
            
            # Format prompt for chat
            formatted_prompt = f"User: {prompt}\nAssistant:"
            
            response = self.local_model(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["User:", "\n\n"],
                echo=False
            )
            
            text = response.get("choices", [{}])[0].get("text", "").strip()
            return text
        except Exception as e:
            logger.error(f"Local LLM generation failed: {e}")
            return ""
    
    def _generate_remote_free(self, prompt: str) -> str:
        """Generate response using free remote endpoint."""
        if not self.remote_config.get("enabled", False):
            logger.warning("Remote free endpoint not enabled")
            return ""
        
        endpoint = self.remote_config.get("endpoint", "")
        if not endpoint:
            logger.warning("No remote endpoint configured")
            return ""
        
        try:
            # Use Hugging Face Inference API (free tier)
            headers = {}
            api_key = self.remote_config.get("api_key", "")
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 200,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            timeout = self.remote_config.get("timeout", 10)
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    if "generated_text" in result[0]:
                        return result[0]["generated_text"].strip()
                    elif isinstance(result[0], str):
                        return result[0].strip()
                elif isinstance(result, dict) and "generated_text" in result:
                    return result["generated_text"].strip()
                else:
                    return str(result).strip()
            else:
                logger.error(f"Remote API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            logger.error(f"Remote LLM generation failed: {e}")
            return ""
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate response using configured provider."""
        logger.info(f"Generating LLM response for prompt: {prompt[:50]}...")
        
        if self.provider == "local" and self.local_model:
            response = self._generate_local(prompt, max_tokens)
            if response:
                return response
        
        # Fallback to remote if local fails or not available
        if self.remote_config.get("enabled", False):
            logger.info("Using remote free endpoint as fallback")
            response = self._generate_remote_free(prompt)
            if response:
                return response
        
        logger.warning("No LLM response generated")
        return "I'm having trouble processing that right now. Please try again."
