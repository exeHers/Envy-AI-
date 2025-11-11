"""
Configuration loader for Envy
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Load and manage Envy configuration"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to config/envy.yaml relative to project root
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "envy.yaml"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Apply profile-specific resource limits
        profile = self.config.get('profile', 'balanced')
        if profile in self.config.get('resources', {}).get('profiles', {}):
            profile_settings = self.config['resources']['profiles'][profile]
            self.config['active_resources'] = profile_settings
    
    def get(self, key: str, default=None):
        """Get configuration value by dot-notation key"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot-notation key"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def save(self):
        """Save configuration back to YAML file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def get_profile(self) -> str:
        """Get current resource profile"""
        return self.config.get('profile', 'balanced')
    
    def get_resource_limits(self) -> Dict[str, Any]:
        """Get active resource limits based on profile"""
        return self.config.get('active_resources', {})


# Global config instance
_config_instance = None

def get_config() -> ConfigLoader:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance
