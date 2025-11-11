"""Skill Manager for executing modular skills."""
import asyncio
import importlib
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from .logger import setup_logger
from .config_loader import get_config


class SkillManager:
    """Manage and execute skills."""
    
    def __init__(self):
        self.config = get_config()
        self.logger = setup_logger("SkillManager", self.config.get("logging.file"))
        
        self.skills = {}
        self.enabled_skills = self.config.get("skills.enabled_skills", [])
        self.timeout = self.config.get("skills.timeout", 60)
        self.require_confirmation = self.config.get("skills.require_confirmation", [])
        
        # Add skills directory to path
        base_dir = Path(__file__).parent.parent
        skills_dir = base_dir / "skills"
        if str(skills_dir) not in sys.path:
            sys.path.insert(0, str(skills_dir))
            
    def initialize(self):
        """Initialize and load skills."""
        self.logger.info("Loading skills...")
        
        base_dir = Path(__file__).parent.parent
        skills_dir = base_dir / "skills"
        
        for skill_name in self.enabled_skills:
            try:
                # Convert skill name to module name (e.g., CodeSkill -> code_skill)
                module_name = ''.join(['_' + c.lower() if c.isupper() else c for c in skill_name]).lstrip('_')
                
                # Import the skill module
                module = importlib.import_module(module_name)
                
                # Get the skill class
                skill_class = getattr(module, skill_name)
                
                # Instantiate the skill
                self.skills[skill_name] = skill_class()
                self.logger.info(f"Loaded skill: {skill_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to load skill {skill_name}: {e}")
                
        self.logger.info(f"Loaded {len(self.skills)} skills")
        return len(self.skills) > 0
        
    async def execute_skill(self, skill_name: str, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a skill with given parameters."""
        self.logger.info(f"Executing skill: {skill_name}.{action} with params: {params}")
        
        result = {
            "skill": skill_name,
            "action": action,
            "success": False,
            "response": "",
            "data": {}
        }
        
        # Check if skill exists
        if skill_name not in self.skills:
            result["response"] = f"Skill {skill_name} not found"
            self.logger.error(result["response"])
            return result
            
        # Check if confirmation required
        if skill_name in self.require_confirmation:
            self.logger.info(f"Skill {skill_name} requires confirmation")
            result["requires_confirmation"] = True
            result["response"] = f"This action requires confirmation. Please confirm to proceed."
            return result
            
        try:
            # Execute skill with timeout
            skill = self.skills[skill_name]
            
            # Call the action method
            if hasattr(skill, action):
                method = getattr(skill, action)
                skill_result = await asyncio.wait_for(
                    method(**params),
                    timeout=self.timeout
                )
                
                result["success"] = True
                result["response"] = skill_result.get("response", "Task completed")
                result["data"] = skill_result.get("data", {})
                
            else:
                result["response"] = f"Action {action} not found in skill {skill_name}"
                self.logger.error(result["response"])
                
        except asyncio.TimeoutError:
            result["response"] = f"Skill execution timed out after {self.timeout} seconds"
            self.logger.error(result["response"])
            
        except Exception as e:
            result["response"] = f"Skill execution error: {str(e)}"
            self.logger.error(result["response"])
            
        return result
        
    def list_skills(self) -> list:
        """List all loaded skills."""
        return list(self.skills.keys())


def main():
    """Test skill manager."""
    manager = SkillManager()
    manager.initialize()
    
    print(f"Loaded skills: {manager.list_skills()}")


if __name__ == "__main__":
    main()
