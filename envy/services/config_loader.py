"""Configuration loader for Envy."""
import yaml
import os
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Load and manage Envy configuration."""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "envy.yaml"
        
        self.config_path = Path(config_path)
        self.config = self.load()
        
    def load(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        # Apply profile-specific settings
        profile = config.get('profile', 'balanced')
        if profile in config.get('resources', {}):
            profile_settings = config['resources'][profile]
            # Override with profile settings
            config['stt']['model_size'] = profile_settings.get('stt_model', config['stt']['model_size'])
            config['llm']['local']['n_threads'] = profile_settings.get('llm_threads', config['llm']['local']['n_threads'])
            config['llm']['local']['n_gpu_layers'] = profile_settings.get('llm_gpu_layers', config['llm']['local']['n_gpu_layers'])
            
        return config
        
    def get(self, key_path: str, default=None):
        """Get configuration value by dot-separated path."""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value
        
    def save(self):
        """Save current configuration back to file."""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)


# Global config instance
_config = None

def get_config(config_path: str = None) -> ConfigLoader:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = ConfigLoader(config_path)
    return _config
