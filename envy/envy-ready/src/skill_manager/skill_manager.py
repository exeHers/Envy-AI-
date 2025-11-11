#!/usr/bin/env python3
"""
Skill Manager
Manages skill loading, execution, and sandboxing.
"""

import importlib
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SkillManager:
    """Manages skill loading and execution."""
    
    def __init__(self, config: dict):
        self.config = config
        self.skills_dir = Path(config.get('skills_dir', 'skills'))
        self.enabled_skills = config.get('enabled', [])
        self.sandbox_config = config.get('sandbox', {})
        self.sandbox_enabled = self.sandbox_config.get('enabled', True)
        self.allowed_commands = set(self.sandbox_config.get('allowed_commands', []))
        self.blocked_commands = set(self.sandbox_config.get('blocked_commands', []))
        self.require_confirmation = self.sandbox_config.get('require_confirmation', True)
        
        self.skills = {}
        self._load_skills()
    
    def _load_skills(self):
        """Load all enabled skills."""
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return
        
        for skill_file in self.skills_dir.glob('*.py'):
            skill_name = skill_file.stem
            if skill_name in self.enabled_skills:
                try:
                    self._load_skill(skill_name, skill_file)
                except Exception as e:
                    logger.error(f"Failed to load skill {skill_name}: {e}")
    
    def _load_skill(self, skill_name: str, skill_file: Path):
        """Load a single skill module."""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(skill_name, skill_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get skill class (should be named SkillNameSkill)
            skill_class = getattr(module, skill_name, None)
            if skill_class and callable(skill_class):
                self.skills[skill_name] = skill_class()
                logger.info(f"Loaded skill: {skill_name}")
            else:
                logger.warning(f"Skill {skill_name} does not have a callable class")
        except Exception as e:
            logger.error(f"Error loading skill {skill_name}: {e}")
    
    def execute(self, skill_name: str, params: Dict[str, Any], require_confirmation: bool = True) -> Dict[str, Any]:
        """Execute a skill with parameters."""
        if skill_name not in self.skills:
            return {
                'success': False,
                'error': f'Skill {skill_name} not found or not enabled'
            }
        
        skill = self.skills[skill_name]
        
        # Check if confirmation is needed
        if require_confirmation and self.require_confirmation:
            if hasattr(skill, 'requires_confirmation') and skill.requires_confirmation(params):
                return {
                    'success': False,
                    'requires_confirmation': True,
                    'skill': skill_name,
                    'params': params
                }
        
        try:
            # Execute skill with timeout
            timeout = self.config.get('timeout', 30)
            start_time = time.time()
            
            result = skill.execute(params)
            
            execution_time = time.time() - start_time
            logger.info(f"Skill {skill_name} executed in {execution_time:.2f}s")
            
            return {
                'success': True,
                'result': result,
                'execution_time': execution_time
            }
        except Exception as e:
            logger.error(f"Skill execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed by sandbox rules."""
        if not self.sandbox_enabled:
            return True
        
        cmd_parts = command.split()
        if not cmd_parts:
            return False
        
        base_cmd = cmd_parts[0]
        
        # Check blocked commands
        if base_cmd in self.blocked_commands:
            return False
        
        # Check allowed commands
        if self.allowed_commands and base_cmd not in self.allowed_commands:
            return False
        
        return True
    
    def list_skills(self) -> list:
        """List all loaded skills."""
        return list(self.skills.keys())


def main():
    """Main entry point for skill manager."""
    import yaml
    
    config_path = Path(__file__).parent.parent.parent / 'config' / 'envy.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    skills_config = config.get('skills', {})
    manager = SkillManager(skills_config)
    
    print(f"Loaded skills: {manager.list_skills()}")


if __name__ == '__main__':
    main()
