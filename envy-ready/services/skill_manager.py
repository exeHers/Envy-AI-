"""
Skill manager for loading and managing Envy skills.
"""
import asyncio
import logging
import os
import importlib.util
from typing import Dict, Optional, Type
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseSkill(ABC):
    """Base class for all Envy skills."""
    
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
    
    @abstractmethod
    async def execute(self, user_text: str, context: dict) -> dict:
        """Execute the skill and return result."""
        pass
    
    def requires_confirmation(self, user_text: str) -> bool:
        """Check if this execution requires confirmation."""
        return False


class SkillManager:
    """Manages loading and execution of skills."""
    
    def __init__(self, config: dict, skills_dir: str = 'skills'):
        self.config = config
        self.skills_dir = skills_dir
        self.skills: Dict[str, BaseSkill] = {}
        
    def load_skills(self):
        """Load all enabled skills."""
        enabled_skills = self.config.get('skills', {}).get('enabled', [])
        
        if not os.path.exists(self.skills_dir):
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return
        
        for skill_name in enabled_skills:
            try:
                skill = self._load_skill(skill_name)
                if skill:
                    self.skills[skill_name] = skill
                    logger.info(f"Loaded skill: {skill_name}")
            except Exception as e:
                logger.error(f"Failed to load skill {skill_name}: {e}")
    
    def _load_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """Load a single skill module."""
        skill_file = os.path.join(self.skills_dir, f"{skill_name.lower()}.py")
        
        if not os.path.exists(skill_file):
            logger.warning(f"Skill file not found: {skill_file}")
            return None
        
        try:
            spec = importlib.util.spec_from_file_location(skill_name.lower(), skill_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get skill class (should be named SkillName)
            skill_class = getattr(module, skill_name, None)
            if not skill_class:
                logger.error(f"Skill class {skill_name} not found in {skill_file}")
                return None
            
            return skill_class(self.config)
        except Exception as e:
            logger.error(f"Error loading skill {skill_name}: {e}")
            return None
    
    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """Get a skill by name."""
        return self.skills.get(skill_name)
    
    def list_skills(self) -> list:
        """List all loaded skills."""
        return list(self.skills.keys())
