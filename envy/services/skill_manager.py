"""
Skill Manager Service
Manages and executes skills (plugins)
MIT License
"""

import os
import sys
import logging
import importlib
import importlib.util
from pathlib import Path
from typing import Optional, Dict, Any, List
import multiprocessing
import signal
import time

from .config_manager import get_config

logger = logging.getLogger(__name__)


class SkillManager:
    """Manages skill plugins and execution"""
    
    def __init__(self):
        self.config = get_config()
        self.skills: Dict[str, Any] = {}
        
        # Configuration
        self.enabled_skills = self.config.get('skills.enabled', [])
        self.timeout = self.config.get('skills.timeout', 60)
        self.sandboxed = self.config.get('skills.sandboxed', True)
        
        logger.info(f"SkillManager initialized (sandboxed: {self.sandboxed})")
    
    def load_skills(self):
        """Load all enabled skills from skills directory"""
        try:
            base_dir = Path(__file__).parent.parent
            skills_dir = base_dir / "skills"
            
            if not skills_dir.exists():
                logger.warning(f"Skills directory not found: {skills_dir}")
                return
            
            logger.info(f"Loading skills from {skills_dir}")
            
            # Add skills directory to path
            if str(skills_dir) not in sys.path:
                sys.path.insert(0, str(skills_dir))
            
            # Load each enabled skill
            for skill_name in self.enabled_skills:
                self.load_skill(skill_name, skills_dir)
            
            logger.info(f"Loaded {len(self.skills)} skills")
            
        except Exception as e:
            logger.error(f"Failed to load skills: {e}")
    
    def load_skill(self, skill_name: str, skills_dir: Path):
        """Load a single skill module"""
        try:
            # Convert CamelCase to snake_case for filename
            filename = ''.join(['_' + c.lower() if c.isupper() else c for c in skill_name]).lstrip('_')
            skill_file = skills_dir / f"{filename}.py"
            
            if not skill_file.exists():
                logger.warning(f"Skill file not found: {skill_file}")
                return
            
            logger.info(f"Loading skill: {skill_name} from {skill_file}")
            
            # Load module
            spec = importlib.util.spec_from_file_location(skill_name, skill_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get skill class (should match skill name)
            if hasattr(module, skill_name):
                skill_class = getattr(module, skill_name)
                self.skills[skill_name] = skill_class()
                logger.info(f"Skill loaded: {skill_name}")
            else:
                logger.warning(f"Skill class '{skill_name}' not found in module")
                
        except Exception as e:
            logger.error(f"Failed to load skill {skill_name}: {e}")
    
    def has_skill(self, skill_name: str) -> bool:
        """Check if skill is loaded"""
        return skill_name in self.skills
    
    def list_skills(self) -> List[str]:
        """Get list of loaded skill names"""
        return list(self.skills.keys())
    
    def execute_skill(self, skill_name: str, command: str) -> Optional[str]:
        """
        Execute a skill with the given command
        Returns response text or None on failure
        """
        try:
            if skill_name not in self.skills:
                logger.warning(f"Skill not found: {skill_name}")
                return None
            
            skill = self.skills[skill_name]
            logger.info(f"Executing skill: {skill_name}")
            
            # Check if skill requires confirmation
            if hasattr(skill, 'requires_confirmation') and skill.requires_confirmation():
                if not self._get_confirmation(skill_name, command):
                    return "Action cancelled - confirmation not received."
            
            # Execute skill with timeout
            if self.sandboxed:
                result = self._execute_sandboxed(skill, command)
            else:
                result = skill.execute(command)
            
            logger.info(f"Skill {skill_name} completed")
            return result
            
        except Exception as e:
            logger.error(f"Error executing skill {skill_name}: {e}")
            return f"Failed to execute {skill_name}: {str(e)}"
    
    def _execute_sandboxed(self, skill, command: str) -> Optional[str]:
        """Execute skill in sandboxed environment with timeout"""
        try:
            # Use multiprocessing for isolation and timeout
            queue = multiprocessing.Queue()
            
            def worker():
                try:
                    result = skill.execute(command)
                    queue.put(('success', result))
                except Exception as e:
                    queue.put(('error', str(e)))
            
            process = multiprocessing.Process(target=worker)
            process.start()
            process.join(timeout=self.timeout)
            
            if process.is_alive():
                # Timeout - terminate process
                logger.warning(f"Skill execution timeout ({self.timeout}s)")
                process.terminate()
                process.join(timeout=2)
                if process.is_alive():
                    process.kill()
                return "Skill execution timed out."
            
            # Get result from queue
            if not queue.empty():
                status, result = queue.get()
                if status == 'success':
                    return result
                else:
                    return f"Skill error: {result}"
            
            return "Skill execution failed."
            
        except Exception as e:
            logger.error(f"Sandboxed execution failed: {e}")
            return f"Execution error: {str(e)}"
    
    def _get_confirmation(self, skill_name: str, command: str) -> bool:
        """
        Get user confirmation for sensitive actions
        TODO: Implement dashboard confirmation check
        """
        logger.info(f"Confirmation required for {skill_name}: {command}")
        
        # For now, auto-confirm non-destructive actions
        destructive_keywords = self.config.get('security.destructive_actions', [])
        
        command_lower = command.lower()
        for keyword in destructive_keywords:
            if keyword in command_lower:
                logger.warning(f"Destructive action detected: {keyword}")
                return False  # Require explicit confirmation
        
        return True  # Auto-confirm safe actions
    
    def reload_skill(self, skill_name: str):
        """Reload a specific skill"""
        try:
            if skill_name in self.skills:
                del self.skills[skill_name]
            
            base_dir = Path(__file__).parent.parent
            skills_dir = base_dir / "skills"
            self.load_skill(skill_name, skills_dir)
            
            logger.info(f"Skill reloaded: {skill_name}")
            
        except Exception as e:
            logger.error(f"Failed to reload skill {skill_name}: {e}")
