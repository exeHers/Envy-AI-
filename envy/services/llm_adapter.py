"""
LLM Adapter Service
Supports local llama.cpp models and remote free fallback
MIT License
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests

from .config_manager import get_config

logger = logging.getLogger(__name__)


class LLMAdapter:
    """Adapter for LLM inference with local and remote support"""
    
    def __init__(self):
        self.config = get_config()
        self.local_model = None
        
        # Configuration
        self.primary = self.config.get('llm.primary', 'local')
        self.local_enabled = self.config.get('llm.local.enabled', True)
        self.remote_enabled = self.config.get('llm.remote.enabled', False)
        
        logger.info(f"LLMAdapter initialized (primary: {self.primary})")
    
    def load_local_model(self):
        """Load local llama.cpp model"""
        try:
            from llama_cpp import Llama
            
            model_path = self.config.get('llm.local.model_path', 'models/llama-2-7b-chat.Q4_0.gguf')
            base_dir = Path(__file__).parent.parent
            full_path = base_dir / model_path
            
            if not full_path.exists():
                logger.warning(f"Local model not found at {full_path}")
                return False
            
            logger.info(f"Loading local LLM from {full_path}")
            
            # Get configuration
            context_size = self.config.get('llm.local.context_size', 2048)
            n_threads = self.config.get('llm.local.threads', 4)
            n_gpu_layers = self.config.get('llm.local.gpu_layers', 20)
            
            # Check if GPU is enabled
            if not self.config.is_gpu_enabled():
                n_gpu_layers = 0
                logger.info("GPU disabled, using CPU only")
            
            self.local_model = Llama(
                model_path=str(full_path),
                n_ctx=context_size,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            
            logger.info("Local LLM loaded successfully")
            return True
            
        except ImportError:
            logger.warning("llama-cpp-python not installed, local LLM unavailable")
            return False
        except Exception as e:
            logger.error(f"Failed to load local LLM: {e}")
            return False
    
    def generate_local(self, prompt: str, max_tokens: int = 256) -> Optional[str]:
        """Generate response using local model"""
        try:
            if self.local_model is None:
                if not self.load_local_model():
                    return None
            
            logger.info(f"Generating local response (max_tokens: {max_tokens})")
            
            temperature = self.config.get('llm.local.temperature', 0.7)
            
            # Format prompt for chat
            formatted_prompt = f"### Human: {prompt}\n### Assistant:"
            
            response = self.local_model(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["###", "\n\n"],
                echo=False
            )
            
            text = response['choices'][0]['text'].strip()
            logger.info(f"Local response: '{text[:100]}...'")
            
            return text
            
        except Exception as e:
            logger.error(f"Local generation failed: {e}")
            return None
    
    def generate_remote(self, prompt: str, max_tokens: int = 256) -> Optional[str]:
        """Generate response using remote free API"""
        try:
            if not self.remote_enabled:
                logger.warning("Remote API is disabled in config")
                return None
            
            provider = self.config.get('llm.remote.provider', 'huggingface')
            
            if provider == 'huggingface':
                return self._generate_huggingface(prompt, max_tokens)
            else:
                logger.warning(f"Unknown remote provider: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"Remote generation failed: {e}")
            return None
    
    def _generate_huggingface(self, prompt: str, max_tokens: int = 256) -> Optional[str]:
        """Generate using Hugging Face Inference API (free tier)"""
        try:
            model = self.config.get('llm.remote.model', 'mistralai/Mistral-7B-Instruct-v0.1')
            api_key = self.config.get('llm.remote.api_key', '')
            timeout = self.config.get('llm.remote.timeout', 30)
            
            url = f"https://api-inference.huggingface.co/models/{model}"
            
            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            logger.info(f"Calling Hugging Face API: {model}")
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get('generated_text', '').strip()
                    logger.info(f"Remote response: '{text[:100]}...'")
                    return text
            else:
                logger.warning(f"Remote API returned status {response.status_code}")
                
            return None
            
        except Exception as e:
            logger.error(f"Hugging Face API call failed: {e}")
            return None
    
    def generate(self, prompt: str, max_tokens: int = 256) -> Optional[str]:
        """
        Generate response using configured primary method with fallback
        Returns tuple: (response_text, source)
        """
        response = None
        source = None
        
        # Try primary method first
        if self.primary == 'local' and self.local_enabled:
            response = self.generate_local(prompt, max_tokens)
            source = 'local'
            
            # Fallback to remote if local fails
            if response is None and self.remote_enabled:
                logger.info("Local generation failed, trying remote fallback")
                response = self.generate_remote(prompt, max_tokens)
                source = 'remote'
        
        elif self.primary == 'remote' and self.remote_enabled:
            response = self.generate_remote(prompt, max_tokens)
            source = 'remote'
            
            # Fallback to local if remote fails
            if response is None and self.local_enabled:
                logger.info("Remote generation failed, trying local fallback")
                response = self.generate_local(prompt, max_tokens)
                source = 'local'
        
        # Return safe fallback if both fail
        if response is None:
            logger.warning("All LLM methods failed, using safe fallback")
            response = "I'm currently unable to process that request. Please try again."
            source = 'fallback'
        
        return response, source
    
    def classify_intent(self, text: str) -> str:
        """
        Classify user intent from text
        Returns: skill name or 'unknown'
        """
        text_lower = text.lower()
        
        # Simple keyword-based intent classification
        if any(word in text_lower for word in ['create', 'write', 'code', 'file', 'script']):
            return 'CodeSkill'
        
        if any(word in text_lower for word in ['research', 'search', 'find', 'look up', 'tell me about']):
            return 'ResearchSkill'
        
        if any(word in text_lower for word in ['remind', 'reminder', 'remember']):
            return 'ReminderSkill'
        
        if any(word in text_lower for word in ['system', 'run', 'execute', 'command']):
            return 'SysControlSkill'
        
        # Use LLM for ambiguous cases
        return 'unknown'
