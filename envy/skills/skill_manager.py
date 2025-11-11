"""
Skill manager for loading and executing modular skills
"""
import logging
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, Optional, List
import multiprocessing
import signal
import time

from services.config_loader import get_config


class SkillManager:
    """Manage and execute skills"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger("SkillManager")
        
        # Settings
        self.skills_enabled = self.config.get('skills.enabled', True)
        self.timeout = self.config.get('skills.timeout', 60)
        
        # Loaded skills
        self.skills: Dict[str, Any] = {}
        
        # Load all skills
        if self.skills_enabled:
            self.load_skills()
        
        self.logger.info(f"SkillManager initialized with {len(self.skills)} skills")
    
    def load_skills(self):
        """Load all available skills"""
        skills_dir = Path(__file__).parent
        
        # List of skill modules to load
        skill_modules = [
            'code_skill',
            'research_skill',
            'sys_control_skill',
            'reminder_skill'
        ]
        
        for module_name in skill_modules:
            try:
                # Import skill module
                module = importlib.import_module(f'skills.{module_name}')
                
                # Find skill class (should be named like CodeSkill, ResearchSkill, etc.)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if name.endswith('Skill') and obj.__module__ == module.__name__:
                        # Instantiate skill
                        skill_instance = obj()
                        skill_name = name
                        
                        # Check if enabled in config
                        config_key = f'skills.{module_name}.enabled'
                        if self.config.get(config_key, True):
                            self.skills[skill_name] = skill_instance
                            self.logger.info(f"Loaded skill: {skill_name}")
                        else:
                            self.logger.info(f"Skill {skill_name} is disabled in config")
                        
                        break
                        
            except Exception as e:
                self.logger.error(f"Failed to load skill {module_name}: {e}")
    
    def execute_skill(self, skill_name: str, action: str, 
                     command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a skill with timeout and error handling"""
        
        if skill_name not in self.skills:
            self.logger.error(f"Skill not found: {skill_name}")
            return {
                'success': False,
                'error': f'Skill {skill_name} not available'
            }
        
        skill = self.skills[skill_name]
        
        try:
            self.logger.info(f"Executing {skill_name}.{action}")
            
            # Execute skill method
            if hasattr(skill, 'execute'):
                result = skill.execute(action=action, command=command, parameters=parameters)
            else:
                result = {
                    'success': False,
                    'error': f'Skill {skill_name} has no execute method'
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Skill execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_skills(self) -> List[str]:
        """List available skills"""
        return list(self.skills.keys())
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a skill"""
        if skill_name not in self.skills:
            return None
        
        skill = self.skills[skill_name]
        
        return {
            'name': skill_name,
            'description': getattr(skill, 'description', 'No description'),
            'actions': getattr(skill, 'actions', [])
        }


def main():
    """Test skill manager standalone"""
    logging.basicConfig(level=logging.INFO)
    
    manager = SkillManager()
    
    print(f"Loaded skills: {manager.list_skills()}")
    
    # Test each skill
    for skill_name in manager.list_skills():
        print(f"\n--- Testing {skill_name} ---")
        info = manager.get_skill_info(skill_name)
        print(f"Description: {info['description']}")
        print(f"Actions: {info['actions']}")


if __name__ == "__main__":
    main()
