"""
LLM Adapter supporting local llama.cpp models and optional remote fallback
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests
import json

from services.config_loader import get_config


class LLMAdapter:
    """Adapter for local and remote LLM inference"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger("LLMAdapter")
        
        # Load LLM config
        self.local_enabled = self.config.get('llm.local_enabled', True)
        self.remote_enabled = self.config.get('llm.remote_enabled', False)
        
        # Local model settings
        model_path = self.config.get('llm.local_model_path', 'models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf')
        base_dir = Path(__file__).parent.parent
        self.local_model_path = base_dir / model_path
        
        self.context_length = self.config.get('llm.local_context_length', 2048)
        self.threads = self.config.get('llm.local_threads', 4)
        self.gpu_layers = self.config.get('llm.local_gpu_layers', 0)
        
        # Remote settings
        self.remote_endpoint = self.config.get('llm.remote_endpoint', '')
        self.remote_api_key = self.config.get('llm.remote_api_key', '')
        
        # Generation settings
        self.max_tokens = self.config.get('llm.max_tokens', 256)
        self.temperature = self.config.get('llm.temperature', 0.7)
        self.timeout = self.config.get('llm.timeout', 30)
        
        # State
        self.local_model = None
        self.model_loaded = False
        
        self.logger.info(f"LLMAdapter initialized (local={self.local_enabled}, remote={self.remote_enabled})")
    
    def load_local_model(self):
        """Load local llama.cpp model"""
        if self.model_loaded:
            return True
        
        if not self.local_enabled:
            self.logger.info("Local LLM disabled in config")
            return False
        
        if not self.local_model_path.exists():
            self.logger.warning(f"Local model not found at {self.local_model_path}")
            return False
        
        try:
            from llama_cpp import Llama
            
            self.logger.info(f"Loading local model: {self.local_model_path.name}")
            self.local_model = Llama(
                model_path=str(self.local_model_path),
                n_ctx=self.context_length,
                n_threads=self.threads,
                n_gpu_layers=self.gpu_layers,
                verbose=False
            )
            
            self.model_loaded = True
            self.logger.info("Local LLM model loaded successfully")
            return True
            
        except ImportError:
            self.logger.error("llama-cpp-python not installed")
            return False
        except Exception as e:
            self.logger.error(f"Failed to load local model: {e}")
            return False
    
    def generate_local(self, prompt: str, system: str = None) -> Optional[str]:
        """Generate response using local model"""
        if not self.model_loaded:
            if not self.load_local_model():
                return None
        
        try:
            # Format prompt (chat template)
            if system:
                full_prompt = f"<|system|>\n{system}</s>\n<|user|>\n{prompt}</s>\n<|assistant|>"
            else:
                full_prompt = f"<|user|>\n{prompt}</s>\n<|assistant|>"
            
            # Generate
            self.logger.debug(f"Generating response for prompt: {prompt[:50]}...")
            
            output = self.local_model(
                full_prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stop=["</s>", "<|user|>"],
                echo=False
            )
            
            response = output['choices'][0]['text'].strip()
            self.logger.debug(f"Generated response: {response[:50]}...")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Local generation failed: {e}")
            return None
    
    def generate_remote(self, prompt: str, system: str = None) -> Optional[str]:
        """Generate response using remote API"""
        if not self.remote_enabled:
            self.logger.debug("Remote LLM not enabled")
            return None
        
        if not self.remote_endpoint:
            self.logger.error("Remote endpoint not configured")
            return None
        
        try:
            # Format request based on endpoint type
            if "huggingface" in self.remote_endpoint.lower():
                return self._generate_hf(prompt, system)
            else:
                # Generic OpenAI-compatible format
                return self._generate_openai_compatible(prompt, system)
                
        except Exception as e:
            self.logger.error(f"Remote generation failed: {e}")
            return None
    
    def _generate_hf(self, prompt: str, system: str = None) -> Optional[str]:
        """Generate using HuggingFace Inference API"""
        headers = {}
        if self.remote_api_key:
            headers["Authorization"] = f"Bearer {self.remote_api_key}"
        
        # Format payload
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": self.max_tokens,
                "temperature": self.temperature,
                "return_full_text": False
            }
        }
        
        response = requests.post(
            self.remote_endpoint,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '').strip()
            return result.get('generated_text', '').strip()
        else:
            self.logger.error(f"Remote API error: {response.status_code} - {response.text}")
            return None
    
    def _generate_openai_compatible(self, prompt: str, system: str = None) -> Optional[str]:
        """Generate using OpenAI-compatible API"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.remote_api_key:
            headers["Authorization"] = f"Bearer {self.remote_api_key}"
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        response = requests.post(
            self.remote_endpoint,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            self.logger.error(f"Remote API error: {response.status_code}")
            return None
    
    def generate(self, prompt: str, system: str = None, use_remote: bool = False) -> str:
        """Generate response with fallback logic"""
        self.logger.info(f"Generating response (use_remote={use_remote})")
        
        # Try local first if not explicitly requesting remote
        if not use_remote and self.local_enabled:
            response = self.generate_local(prompt, system)
            if response:
                self.logger.info("Response generated using local model")
                return response
            else:
                self.logger.warning("Local generation failed, trying fallback...")
        
        # Try remote as fallback
        if self.remote_enabled:
            response = self.generate_remote(prompt, system)
            if response:
                self.logger.info("Response generated using remote API")
                return response
        
        # Final fallback: simple rule-based response
        self.logger.warning("All LLM methods failed, using fallback response")
        return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Simple rule-based fallback when LLM unavailable"""
        prompt_lower = prompt.lower()
        
        if "hello" in prompt_lower or "hi" in prompt_lower:
            return "Hello! I'm Envy, but my language model is not available right now."
        elif "how are you" in prompt_lower:
            return "I'm operational, though running in fallback mode."
        elif "help" in prompt_lower:
            return "I can help with file operations, system commands, and reminders. My advanced AI is currently unavailable."
        else:
            return "I understand your request, but I'm running in limited mode. Please check my configuration."
    
    def classify_intent(self, text: str) -> Dict[str, Any]:
        """Classify user intent (simple rule-based for now)"""
        text_lower = text.lower()
        
        # Code/file operations
        if any(word in text_lower for word in ['create', 'write', 'make', 'generate']) and \
           any(word in text_lower for word in ['file', 'script', '.py', '.js', '.txt']):
            return {
                'skill': 'CodeSkill',
                'confidence': 0.9,
                'action': 'create_file'
            }
        
        # Research
        if any(word in text_lower for word in ['research', 'search', 'find', 'look up', 'information about']):
            return {
                'skill': 'ResearchSkill',
                'confidence': 0.8,
                'action': 'research'
            }
        
        # System control
        if any(word in text_lower for word in ['system', 'run', 'execute', 'command']):
            return {
                'skill': 'SysControlSkill',
                'confidence': 0.7,
                'action': 'execute'
            }
        
        # Reminder
        if any(word in text_lower for word in ['remind', 'reminder', 'remember']):
            return {
                'skill': 'ReminderSkill',
                'confidence': 0.9,
                'action': 'create_reminder'
            }
        
        # General chat
        return {
            'skill': 'ChatSkill',
            'confidence': 0.5,
            'action': 'chat'
        }
    
    def test_generation(self) -> tuple[bool, str]:
        """Test LLM generation"""
        self.logger.info("Testing LLM generation...")
        
        test_prompt = "Say 'Hello, I am Envy' in one short sentence."
        
        response = self.generate(test_prompt)
        
        if response and len(response) > 0:
            self.logger.info(f"✓ LLM test successful: {response}")
            return True, response
        else:
            self.logger.error("✗ LLM test failed")
            return False, "No response generated"


def main():
    """Test LLM adapter standalone"""
    logging.basicConfig(level=logging.INFO)
    
    adapter = LLMAdapter()
    
    # Test generation
    print("Testing LLM generation...")
    response = adapter.generate("What is 2+2? Answer briefly.")
    print(f"Response: {response}")
    
    # Test intent classification
    print("\nTesting intent classification...")
    intents = [
        "Create a Python file called test.py",
        "Research quantum computing",
        "Run the date command",
        "Remind me to call mom tomorrow"
    ]
    
    for text in intents:
        intent = adapter.classify_intent(text)
        print(f"  '{text}' -> {intent['skill']}")


if __name__ == "__main__":
    main()
