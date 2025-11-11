"""Skill manager and base skill class."""
import logging
import importlib
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import subprocess
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class BaseSkill(ABC):
    """Base class for all skills."""
    
    def __init__(self, config, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(f"envy.skill.{self.__class__.__name__}")
        self.name = self.__class__.__name__
    
    @abstractmethod
    def execute(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill and return result."""
        pass
    
    @abstractmethod
    def requires_confirmation(self, intent_data: Dict[str, Any]) -> bool:
        """Check if this action requires confirmation."""
        pass


class SkillManager:
    """Manages skill loading and execution."""
    
    def __init__(self, config, logger: Optional[logging.Logger] = None):
        self.config = config.skills
        self.logger = logger or logging.getLogger("envy.skill_manager")
        self.skills: Dict[str, BaseSkill] = {}
        self.parent_config = config  # Store full config for skills
        self.load_skills()
    
    def load_skills(self):
        """Load all enabled skills."""
        skills_dir = Path(project_root / "skills")
        skills_dir.mkdir(exist_ok=True)
        
        for skill_name in self.config.enabled:
            try:
                # Map skill names to module names
                skill_module_map = {
                    'CodeSkill': 'codeskill',
                    'ResearchSkill': 'researchskill',
                    'SysControlSkill': 'syscontrolskill',
                    'ReminderSkill': 'reminderskill',
                    'GeneralSkill': 'generalskill'
                }
                module_name = skill_module_map.get(skill_name, skill_name.lower())
                skill_module = importlib.import_module(f"skills.{module_name}")
                skill_class = getattr(skill_module, skill_name)
                # Pass parent config (not just skills config) to skills
                skill_instance = skill_class(self.parent_config, self.logger)
                self.skills[skill_name] = skill_instance
                self.logger.info(f"Loaded skill: {skill_name}")
            except Exception as e:
                self.logger.error(f"Failed to load skill {skill_name}: {e}")
    
    def execute_skill(self, skill_name: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a skill."""
        if skill_name not in self.skills:
            return {
                'success': False,
                'error': f"Skill {skill_name} not found"
            }
        
        skill = self.skills[skill_name]
        
        # Check if confirmation is required
        if skill.requires_confirmation(intent_data) and self.config.require_confirmation:
            return {
                'success': False,
                'requires_confirmation': True,
                'skill': skill_name,
                'intent_data': intent_data
            }
        
        # Execute with timeout
        try:
            start_time = time.time()
            result = skill.execute(intent_data)
            elapsed = time.time() - start_time
            
            if elapsed > self.config.timeout:
                self.logger.warning(f"Skill {skill_name} exceeded timeout")
            
            result['execution_time'] = elapsed
            return result
        except Exception as e:
            self.logger.error(f"Error executing skill {skill_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def confirm_and_execute(self, skill_name: str, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Confirm and execute a skill."""
        return self.execute_skill(skill_name, intent_data)
