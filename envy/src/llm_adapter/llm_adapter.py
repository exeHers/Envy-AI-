#!/usr/bin/env python3
"""
LLM Adapter Service
Supports local llama.cpp models and optional free remote endpoints.
"""

import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMAdapter:
    """LLM adapter supporting local and remote models."""
    
    def __init__(self, config: dict):
        self.config = config
        self.primary = config.get('primary', 'local')
        self.local_config = config.get('local', {})
        self.remote_config = config.get('remote_free', {})
        
        self.local_model = None
        self.llama_cpp_path = None
        
    def initialize(self) -> bool:
        """Initialize the LLM adapter."""
        try:
            if self.primary == 'local':
                return self._init_local()
            elif self.primary == 'remote_free':
                return self._init_remote()
            elif self.primary == 'disabled':
                logger.warning("LLM adapter disabled")
                return True
            else:
                logger.error(f"Unknown LLM primary: {self.primary}")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize LLM adapter: {e}")
            return False
    
    def _init_local(self) -> bool:
        """Initialize local LLM (llama.cpp)."""
        try:
            model_path = self.local_config.get('model_path', 'models/llama-2-7b-chat-q4_0.gguf')
            
            # Check if llama.cpp is available
            self.llama_cpp_path = self._find_llama_cpp()
            if not self.llama_cpp_path:
                logger.warning("llama.cpp not found, will use Python bindings")
                return self._init_local_python()
            
            if not Path(model_path).exists():
                logger.warning(f"Model not found at {model_path}, will use fallback")
                return self._init_remote()
            
            logger.info(f"Local LLM initialized: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Local LLM initialization failed: {e}")
            return self._init_remote()
    
    def _init_local_python(self) -> bool:
        """Initialize local LLM using Python bindings."""
        try:
            import llama_cpp
            
            model_path = self.local_config.get('model_path', 'models/llama-2-7b-chat-q4_0.gguf')
            
            if not Path(model_path).exists():
                logger.warning(f"Model not found, using fallback")
                return self._init_remote()
            
            n_gpu_layers = self.local_config.get('n_gpu_layers', 20)
            n_threads = self.local_config.get('n_threads', 4)
            context_size = self.local_config.get('context_size', 2048)
            
            self.local_model = llama_cpp.Llama(
                model_path=model_path,
                n_ctx=context_size,
                n_gpu_layers=n_gpu_layers,
                n_threads=n_threads,
                verbose=False
            )
            
            logger.info("Local LLM (Python) initialized")
            return True
        except ImportError:
            logger.warning("llama-cpp-python not available, using fallback")
            return self._init_remote()
        except Exception as e:
            logger.error(f"Python LLM initialization failed: {e}")
            return self._init_remote()
    
    def _find_llama_cpp(self) -> Optional[Path]:
        """Find llama.cpp binary."""
        possible_paths = [
            Path('llama.cpp') / 'main',
            Path('llama.cpp') / 'build' / 'bin' / 'main',
            Path('/usr/local/bin/llama-cli'),
        ]
        
        for path in possible_paths:
            if path.exists() and path.is_file():
                return path
        
        return None
    
    def _init_remote(self) -> bool:
        """Initialize remote free LLM endpoint."""
        if not self.remote_config.get('enabled', False):
            logger.warning("Remote LLM disabled, LLM adapter will use fallback responses")
            return True
        
        endpoint = self.remote_config.get('endpoint', '')
        if not endpoint:
            logger.warning("No remote endpoint configured")
            return True
        
        logger.info(f"Remote LLM configured: {endpoint}")
        return True
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        """Generate response from LLM."""
        if self.primary == 'disabled':
            return self._fallback_response(prompt)
        
        try:
            if self.primary == 'local':
                return self._generate_local(prompt, system_prompt, max_tokens)
            elif self.primary == 'remote_free':
                return self._generate_remote(prompt, system_prompt, max_tokens)
            else:
                return self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._fallback_response(prompt)
    
    def _generate_local(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        """Generate using local LLM."""
        if self.local_model:
            # Python bindings
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            max_tokens = max_tokens or self.local_config.get('max_tokens', 512)
            temperature = self.local_config.get('temperature', 0.7)
            
            response = self.local_model(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["Human:", "User:", "\n\n"]
            )
            
            return response['choices'][0]['text'].strip()
        
        elif self.llama_cpp_path:
            # llama.cpp binary
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            max_tokens = max_tokens or self.local_config.get('max_tokens', 512)
            temperature = self.local_config.get('temperature', 0.7)
            n_gpu_layers = self.local_config.get('n_gpu_layers', 20)
            n_threads = self.local_config.get('n_threads', 4)
            model_path = self.local_config.get('model_path', 'models/llama-2-7b-chat-q4_0.gguf')
            
            cmd = [
                str(self.llama_cpp_path),
                '-m', model_path,
                '-p', full_prompt,
                '-n', str(max_tokens),
                '-t', str(n_threads),
                '--temp', str(temperature),
                '--top-p', '0.9',
            ]
            
            if n_gpu_layers > 0:
                cmd.extend(['-ngl', str(n_gpu_layers)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"llama.cpp error: {result.stderr}")
                return self._fallback_response(prompt)
        else:
            return self._fallback_response(prompt)
    
    def _generate_remote(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: Optional[int] = None) -> str:
        """Generate using remote free endpoint."""
        import requests
        
        endpoint = self.remote_config.get('endpoint', '')
        api_key = self.remote_config.get('api_key', '')
        timeout = self.remote_config.get('timeout', 10)
        
        if not endpoint:
            return self._fallback_response(prompt)
        
        try:
            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            payload = {
                'inputs': prompt,
                'parameters': {
                    'max_new_tokens': max_tokens or 512,
                    'temperature': 0.7,
                }
            }
            
            response = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', self._fallback_response(prompt))
            elif isinstance(result, dict):
                return result.get('generated_text', self._fallback_response(prompt))
            else:
                return self._fallback_response(prompt)
                
        except Exception as e:
            logger.error(f"Remote LLM error: {e}")
            if self.remote_config.get('fallback_on_error', True):
                return self._fallback_response(prompt)
            raise
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback response when LLM is unavailable."""
        prompt_lower = prompt.lower()
        
        # Simple rule-based responses
        if 'create' in prompt_lower and 'file' in prompt_lower:
            return "I'll create that file for you."
        elif 'research' in prompt_lower:
            return "I'll research that topic and provide a summary."
        elif 'remind' in prompt_lower:
            return "I'll set a reminder for you."
        elif 'hello' in prompt_lower or 'hi' in prompt_lower:
            return "Hello! I'm Envy, your personal assistant. How can I help you?"
        else:
            return "I understand. Let me help you with that."


def main():
    """Main entry point for LLM adapter."""
    import yaml
    
    config_path = Path(__file__).parent.parent.parent / 'config' / 'envy.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    llm_config = config.get('llm', {})
    adapter = LLMAdapter(llm_config)
    
    if not adapter.initialize():
        sys.exit(1)
    
    try:
        test_prompt = "Hello, what can you do?"
        response = adapter.generate(test_prompt)
        print(f"LLM_RESPONSE:{response}")
    except KeyboardInterrupt:
        logger.info("LLM adapter interrupted")
        sys.exit(0)


if __name__ == '__main__':
    main()
