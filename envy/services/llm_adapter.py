"""
LLM Adapter supporting local llama.cpp and optional free remote endpoints.
"""
import asyncio
import logging
import os
import subprocess
import json
from typing import Optional, Dict, Any
import requests

from .base_service import BaseService

logger = logging.getLogger(__name__)


class LLMAdapter(BaseService):
    """Adapter for LLM inference (local llama.cpp or remote fallback)."""
    
    def __init__(self, config: dict):
        super().__init__("LLMAdapter", config)
        self.local_model = None
        self.local_process: Optional[subprocess.Popen] = None
        self.use_local = True
        
    async def start(self):
        """Initialize LLM adapter."""
        logger.info("Initializing LLM adapter")
        
        llm_config = self.config.get('llm', {})
        primary = llm_config.get('primary', 'local')
        
        if primary == 'local':
            await self._init_local()
        else:
            await self._init_remote()
        
        self.running = True
        logger.info("LLM adapter ready")
    
    async def _init_local(self):
        """Initialize local LLM (llama.cpp)."""
        llm_config = self.config.get('llm', {}).get('local', {})
        model_path = llm_config.get('model_path', 'models/llama-7b-q4_0.gguf')
        
        if not os.path.exists(model_path):
            logger.warning(f"Local model not found at {model_path}, will use remote fallback")
            self.use_local = False
            await self._init_remote()
            return
        
        try:
            # Try to use llama-cpp-python
            from llama_cpp import Llama
            
            context_size = llm_config.get('context_size', 2048)
            threads = llm_config.get('threads', 4)
            gpu_layers = llm_config.get('gpu_layers', 20)
            
            logger.info(f"Loading local LLM from {model_path}")
            self.local_model = Llama(
                model_path=model_path,
                n_ctx=context_size,
                n_threads=threads,
                n_gpu_layers=gpu_layers,
                verbose=False
            )
            logger.info("Local LLM loaded successfully")
            self.use_local = True
        except ImportError:
            logger.warning("llama-cpp-python not available, using remote fallback")
            self.use_local = False
            await self._init_remote()
        except Exception as e:
            logger.error(f"Failed to load local LLM: {e}, using remote fallback")
            self.use_local = False
            await self._init_remote()
    
    async def _init_remote(self):
        """Initialize remote LLM fallback."""
        logger.info("Using remote LLM fallback")
        self.use_local = False
    
    async def generate(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> str:
        """Generate text response."""
        if self.use_local and self.local_model:
            return await self._generate_local(prompt, max_tokens, temperature)
        else:
            return await self._generate_remote(prompt, max_tokens, temperature)
    
    async def _generate_local(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using local LLM."""
        try:
            response = self.local_model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["\n\n", "User:", "Envy:"],
                echo=False
            )
            text = response['choices'][0]['text'].strip()
            logger.info(f"Local LLM response: {text[:100]}...")
            return text
        except Exception as e:
            logger.error(f"Local LLM error: {e}, falling back to remote")
            return await self._generate_remote(prompt, max_tokens, temperature)
    
    async def _generate_remote(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using remote free endpoint (fallback)."""
        llm_config = self.config.get('llm', {}).get('remote', {})
        
        if not llm_config.get('enabled', False):
            # Return a simple rule-based response
            logger.warning("Remote LLM disabled, using rule-based fallback")
            return self._rule_based_response(prompt)
        
        endpoint = llm_config.get('endpoint', '')
        timeout = llm_config.get('timeout', 10)
        
        try:
            # Try Hugging Face Inference API (free tier)
            headers = {}
            api_key = llm_config.get('api_key', '')
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            payload = {
                'inputs': prompt,
                'parameters': {
                    'max_new_tokens': max_tokens,
                    'temperature': temperature,
                    'return_full_text': False
                }
            }
            
            response = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                text = result[0].get('generated_text', '').strip()
            elif isinstance(result, dict):
                text = result.get('generated_text', '').strip()
            else:
                text = str(result).strip()
            
            logger.info(f"Remote LLM response: {text[:100]}...")
            return text
        except Exception as e:
            logger.error(f"Remote LLM error: {e}, using rule-based fallback")
            return self._rule_based_response(prompt)
    
    def _rule_based_response(self, prompt: str) -> str:
        """Simple rule-based response when LLM unavailable."""
        prompt_lower = prompt.lower()
        
        if 'create' in prompt_lower and 'file' in prompt_lower:
            return "I'll create that file for you."
        elif 'research' in prompt_lower:
            return "I'll research that topic for you."
        elif 'remind' in prompt_lower:
            return "I'll set a reminder for you."
        elif 'hello' in prompt_lower or 'hi' in prompt_lower:
            return "Hello! How can I help you?"
        else:
            return "I understand. Let me help you with that."
    
    async def classify_intent(self, text: str) -> Dict[str, Any]:
        """Classify user intent from text."""
        text_lower = text.lower()
        
        # Simple rule-based intent classification
        intents = {
            'code': ['create', 'write', 'file', 'code', 'script', 'program'],
            'research': ['research', 'search', 'find', 'look up', 'information'],
            'system': ['system', 'command', 'run', 'execute', 'open', 'close'],
            'reminder': ['remind', 'reminder', 'remember', 'alert', 'notify']
        }
        
        for intent, keywords in intents.items():
            if any(keyword in text_lower for keyword in keywords):
                return {
                    'intent': intent,
                    'confidence': 0.8,
                    'skill': f"{intent.capitalize()}Skill"
                }
        
        # Use LLM for ambiguous cases
        if self.use_local or self.config.get('llm', {}).get('remote', {}).get('enabled', False):
            prompt = f"Classify this user request into one category: code, research, system, reminder, or other.\nUser: {text}\nCategory:"
            response = await self.generate(prompt, max_tokens=10, temperature=0.3)
            response_lower = response.lower()
            
            for intent in intents.keys():
                if intent in response_lower:
                    return {
                        'intent': intent,
                        'confidence': 0.6,
                        'skill': f"{intent.capitalize()}Skill"
                    }
        
        return {
            'intent': 'other',
            'confidence': 0.5,
            'skill': None
        }
    
    async def stop(self):
        """Stop LLM adapter."""
        logger.info("Stopping LLM adapter")
        self.running = False
        if self.local_process:
            self.local_process.terminate()
        logger.info("LLM adapter stopped")
