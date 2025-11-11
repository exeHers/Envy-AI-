"""
Configuration Manager for Envy
Loads and validates configuration from YAML file
MIT License
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading and access"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Default to config/envy.yaml relative to project root
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "envy.yaml"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"Configuration loaded from {self.config_path}")
            self._validate()
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _validate(self):
        """Validate configuration has required fields"""
        required_sections = ['system', 'wake', 'stt', 'tts', 'llm', 'skills']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: {section}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation path
        Example: config.get('llm.local.model_path')
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """Set configuration value by dot-notation path"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self):
        """Save configuration back to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def get_profile(self) -> str:
        """Get current performance profile"""
        return self.get('system.profile', 'balanced')
    
    def is_gpu_enabled(self) -> bool:
        """Check if GPU is enabled"""
        return self.get('resources.gpu_enabled', False)
    
    def get_max_cpu_percent(self) -> int:
        """Get maximum CPU usage percentage"""
        return self.get('resources.max_cpu_percent', 50)
    
    def get_max_memory_mb(self) -> int:
        """Get maximum memory in MB"""
        return self.get('resources.max_memory_mb', 4096)


# Global config instance
_config_instance: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """Get or create global configuration instance"""
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    
    return _config_instance
