"""Configuration loader for Envy."""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for Envy."""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "config", "envy.yaml"
            )
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "profile": "balanced",
            "wake": {
                "keyword": "envy",
                "sensitivity": 0.5,
                "model_path": "models/vosk-model-small-en-us-0.22",
                "continuous_listening": True
            },
            "stt": {
                "engine": "whisper",
                "model": "base",
                "device": "auto",
                "language": "en",
                "streaming": True
            },
            "tts": {
                "engine": "pyttsx3",
                "rate": 150,
                "volume": 0.9,
                "streaming": True
            },
            "llm": {
                "provider": "local",
                "local": {
                    "engine": "llama.cpp",
                    "model_path": "models/llama-2-7b-chat-q4_0.gguf",
                    "context_size": 2048,
                    "n_gpu_layers": 20,
                    "n_threads": 4,
                    "temperature": 0.7,
                    "max_tokens": 512
                },
                "remote_free": {
                    "enabled": False,
                    "endpoint": "",
                    "timeout": 10
                }
            },
            "resources": {
                "max_cpu_percent": 50,
                "max_memory_mb": 4096,
                "max_gpu_memory_mb": 6144,
                "skill_timeout_seconds": 30
            },
            "router": {
                "intent_classifier": "rule_based",
                "confidence_threshold": 0.6,
                "fallback_to_llm": True
            },
            "skills": {
                "enabled": ["CodeSkill", "ResearchSkill", "SysControlSkill", "ReminderSkill"],
                "require_confirmation": ["SysControlSkill"],
                "sandbox": {
                    "enabled": True,
                    "allowed_commands": [],
                    "allowed_paths": []
                }
            },
            "web": {
                "host": "127.0.0.1",
                "port": 8080,
                "enable_cors": True,
                "log_level": "INFO"
            },
            "logging": {
                "level": "INFO",
                "file": "artifacts/envy.log",
                "console": True
            },
            "security": {
                "require_voice_confirmation": True,
                "require_dashboard_confirmation": True,
                "sandbox_execution": True,
                "max_file_size_mb": 10
            },
            "persona": {
                "name": "Envy",
                "tone": "neutral",
                "verbosity": "concise",
                "responses": {
                    "wake": "Yes?",
                    "thinking": "Let me think...",
                    "error": "I encountered an error.",
                    "confirmation": "Are you sure?"
                }
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot-separated key."""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def apply_profile(self, profile: str):
        """Apply resource profile (low, balanced, power)."""
        profiles = {
            "low": {
                "resources.max_cpu_percent": 25,
                "resources.max_memory_mb": 2048,
                "stt.model": "tiny",
                "llm.local.n_gpu_layers": 0,
                "llm.local.n_threads": 2,
                "llm.local.context_size": 1024
            },
            "balanced": {
                "resources.max_cpu_percent": 50,
                "resources.max_memory_mb": 4096,
                "stt.model": "base",
                "llm.local.n_gpu_layers": 20,
                "llm.local.n_threads": 4,
                "llm.local.context_size": 2048
            },
            "power": {
                "resources.max_cpu_percent": 80,
                "resources.max_memory_mb": 8192,
                "stt.model": "small",
                "llm.local.n_gpu_layers": 35,
                "llm.local.n_threads": 8,
                "llm.local.context_size": 4096
            }
        }
        
        if profile in profiles:
            for key, value in profiles[profile].items():
                self.set(key, value)
            self.set("profile", profile)
