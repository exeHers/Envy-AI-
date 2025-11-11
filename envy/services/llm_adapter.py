#!/usr/bin/env python3
"""
LLM Adapter - Unified interface for local and remote language models
Supports llama.cpp (local) and optional free remote fallbacks
"""

import os
import sys
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LLMAdapter:
    """Adapter for local and remote LLM inference"""
    
    def __init__(self, config):
        self.config = config
        self.llm_config = config.get('llm', {})
        self.primary_backend = self.llm_config.get('primary_backend', 'local')
        
        self.local_model = None
        self.local_enabled = self.llm_config.get('local', {}).get('enabled', True)
        self.remote_enabled = self.llm_config.get('remote', {}).get('enabled', False)
        
        logger.info(f"LLMAdapter initialized with backend: {self.primary_backend}")
    
    def load_model(self):
        """Load LLM model based on configuration"""
        if self.local_enabled and self.primary_backend in ['local', 'hybrid']:
            return self._load_local_model()
        return True
    
    def _load_local_model(self):
        """Load local LLM using llama-cpp-python"""
        try:
            from llama_cpp import Llama
            
            local_config = self.llm_config.get('local', {})
            model_path = local_config.get('model_path', './models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf')
            
            # Check if model exists
            if not os.path.exists(model_path):
                logger.warning(f"Local model not found at {model_path}")
                logger.info("Attempting to download model...")
                self._download_local_model(model_path)
            
            # Load model with appropriate settings
            n_gpu_layers = local_config.get('gpu_layers', 10)
            n_ctx = local_config.get('context_length', 2048)
            
            # Detect if GPU is available
            profile = self.config.get('resource_profile', 'balanced')
            use_gpu = self.config.get('profiles', {}).get(profile, {}).get('use_gpu', False)
            
            if not use_gpu:
                n_gpu_layers = 0
            
            logger.info(f"Loading local model from {model_path}")
            self.local_model = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            
            logger.info(f"Local LLM loaded successfully (GPU layers: {n_gpu_layers})")
            return True
        
        except ImportError:
            logger.error("llama-cpp-python not installed")
            return False
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            return False
    
    def _download_local_model(self, model_path: str):
        """Download a small quantized model from HuggingFace"""
        import urllib.request
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # TinyLlama 1.1B Q4_K_M (small, fast, free)
        model_url = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        
        logger.info(f"Downloading model from {model_url}...")
        logger.info("This may take a few minutes (file size: ~670MB)...")
        
        try:
            urllib.request.urlretrieve(model_url, model_path)
            logger.info(f"Model downloaded successfully to {model_path}")
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            raise
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text response from prompt"""
        
        # Try local model first
        if self.local_enabled and self.local_model:
            return self._generate_local(prompt, system_prompt)
        
        # Fallback to remote if enabled
        if self.remote_enabled:
            return self._generate_remote(prompt, system_prompt)
        
        # No backend available
        return self._generate_fallback(prompt)
    
    def _generate_local(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using local llama.cpp model"""
        try:
            local_config = self.llm_config.get('local', {})
            max_tokens = local_config.get('max_tokens', 256)
            temperature = local_config.get('temperature', 0.7)
            
            # Format prompt for chat models
            if system_prompt:
                full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>\n"
            else:
                full_prompt = f"<|user|>\n{prompt}\n<|assistant|>\n"
            
            logger.debug(f"Generating with local model: {prompt[:50]}...")
            
            output = self.local_model(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["<|user|>", "<|system|>"],
                echo=False
            )
            
            response = output['choices'][0]['text'].strip()
            logger.info(f"Local LLM response: {response[:100]}...")
            return response
        
        except Exception as e:
            logger.error(f"Local generation error: {e}")
            if self.remote_enabled:
                logger.info("Falling back to remote model")
                return self._generate_remote(prompt, system_prompt)
            return self._generate_fallback(prompt)
    
    def _generate_remote(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using free remote API (HuggingFace Inference API)"""
        try:
            remote_config = self.llm_config.get('remote', {})
            api_url = remote_config.get('api_url')
            api_key = remote_config.get('api_key', '')
            timeout = remote_config.get('timeout', 10)
            
            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            # Format payload
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            payload = {
                "inputs": full_prompt,
                "parameters": {
                    "max_new_tokens": 256,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            logger.info(f"[REMOTE] Calling free HuggingFace API...")
            response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('generated_text', '')
                logger.info(f"[REMOTE] Response received: {text[:100]}...")
                return text
            
            return self._generate_fallback(prompt)
        
        except Exception as e:
            logger.error(f"Remote generation error: {e}")
            return self._generate_fallback(prompt)
    
    def _generate_fallback(self, prompt: str) -> str:
        """Simple rule-based fallback when no LLM is available"""
        logger.warning("Using rule-based fallback (no LLM available)")
        
        prompt_lower = prompt.lower()
        
        # Simple intent detection
        if any(word in prompt_lower for word in ['create', 'write', 'make', 'generate']):
            if 'file' in prompt_lower or 'script' in prompt_lower or '.py' in prompt_lower:
                return "I'll create that file for you."
        
        if any(word in prompt_lower for word in ['research', 'find', 'search', 'look up']):
            return "I'll research that topic and prepare a summary for you."
        
        if any(word in prompt_lower for word in ['remind', 'reminder', 'schedule']):
            return "I'll set up that reminder for you."
        
        if any(word in prompt_lower for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm Envy, your personal assistant. How can I help you?"
        
        # Generic response
        return "I understand. Let me process that request for you."
    
    def classify_intent(self, text: str) -> Dict[str, Any]:
        """Classify user intent from text"""
        text_lower = text.lower()
        
        intents = {
            'code': ['create', 'write', 'make', 'file', 'script', '.py', '.js', 'function'],
            'research': ['research', 'find', 'search', 'look up', 'information', 'about'],
            'system': ['open', 'close', 'run', 'execute', 'command', 'system'],
            'reminder': ['remind', 'reminder', 'schedule', 'later', 'time'],
            'query': ['what', 'how', 'why', 'when', 'where', 'who', 'explain']
        }
        
        for intent, keywords in intents.items():
            if any(keyword in text_lower for keyword in keywords):
                return {'intent': intent, 'confidence': 0.7, 'text': text}
        
        return {'intent': 'general', 'confidence': 0.5, 'text': text}


def main():
    """Standalone test of LLM adapter"""
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'llm': {
            'primary_backend': 'local',
            'local': {
                'enabled': True,
                'engine': 'llama-cpp',
                'model_path': './models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf',
                'context_length': 2048,
                'max_tokens': 256,
                'temperature': 0.7,
                'gpu_layers': 0
            },
            'remote': {
                'enabled': False
            }
        },
        'resource_profile': 'balanced',
        'profiles': {
            'balanced': {'use_gpu': False}
        },
        'general': {'models_dir': './models'}
    }
    
    llm = LLMAdapter(config)
    
    print("Loading LLM model...")
    if llm.load_model():
        print("Model loaded successfully!")
        
        # Test generation
        prompt = "What is the capital of France?"
        print(f"\nPrompt: {prompt}")
        response = llm.generate(prompt)
        print(f"Response: {response}")
    else:
        print("Failed to load model, testing fallback...")
        response = llm.generate("Create a Python file")
        print(f"Fallback response: {response}")


if __name__ == "__main__":
    main()
