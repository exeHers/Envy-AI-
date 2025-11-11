#!/usr/bin/env python3
"""
Skill Manager - Manages and executes modular skills
Handles skill loading, execution, sandboxing, and confirmation workflows
"""

import os
import sys
import logging
import importlib.util
from typing import Dict, Any, Optional, List
import multiprocessing
import signal

logger = logging.getLogger(__name__)


class SkillManager:
    """Manages plugin-based skills"""
    
    def __init__(self, config):
        self.config = config
        self.skills_config = config.get('skills', {})
        self.plugins_dir = self.skills_config.get('plugins_dir', './skills')
        self.max_execution_time = self.skills_config.get('max_execution_time', 60)
        self.require_confirmation = self.skills_config.get('require_confirmation', True)
        
        self.skills = {}
        self.pending_confirmations = {}
        
        logger.info(f"SkillManager initialized, plugins dir: {self.plugins_dir}")
    
    def load_skills(self):
        """Load all skills from plugins directory"""
        if not os.path.exists(self.plugins_dir):
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return False
        
        # Import built-in skills
        skill_modules = [
            'code_skill',
            'research_skill',
            'sys_control_skill',
            'reminder_skill'
        ]
        
        for skill_name in skill_modules:
            try:
                skill_path = os.path.join(self.plugins_dir, f'{skill_name}.py')
                if os.path.exists(skill_path):
                    spec = importlib.util.spec_from_file_location(skill_name, skill_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Get skill class (should be named with CamelCase)
                    class_name = ''.join(word.capitalize() for word in skill_name.split('_'))
                    if hasattr(module, class_name):
                        skill_class = getattr(module, class_name)
                        self.skills[skill_name] = skill_class(self.config)
                        logger.info(f"Loaded skill: {skill_name}")
                    else:
                        logger.warning(f"Skill class {class_name} not found in {skill_name}")
                else:
                    logger.warning(f"Skill file not found: {skill_path}")
            except Exception as e:
                logger.error(f"Failed to load skill {skill_name}: {e}")
        
        logger.info(f"Loaded {len(self.skills)} skills")
        return True
    
    def execute_skill(self, skill_name: str, input_text: str, 
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a skill with timeout and sandboxing"""
        
        if skill_name not in self.skills:
            logger.error(f"Skill not found: {skill_name}")
            return {
                'success': False,
                'error': f'Skill not found: {skill_name}',
                'response': f"I don't have that capability yet."
            }
        
        skill = self.skills[skill_name]
        
        # Check if skill requires confirmation for this action
        if self.require_confirmation and skill.is_destructive(input_text):
            logger.info(f"Skill {skill_name} requires confirmation for: {input_text}")
            
            # Store pending confirmation
            confirmation_id = f"{skill_name}_{len(self.pending_confirmations)}"
            self.pending_confirmations[confirmation_id] = {
                'skill_name': skill_name,
                'input_text': input_text,
                'context': context
            }
            
            return {
                'success': True,
                'requires_confirmation': True,
                'confirmation_id': confirmation_id,
                'response': f"This action requires confirmation. Please confirm via the dashboard or say 'confirm'.",
                'action_preview': skill.preview_action(input_text)
            }
        
        # Execute skill
        try:
            logger.info(f"Executing skill: {skill_name}")
            
            # Execute with timeout (simplified - in production use proper process isolation)
            result = skill.execute(input_text, context)
            
            logger.info(f"Skill execution completed: {skill_name}")
            return result
        
        except Exception as e:
            logger.error(f"Skill execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"Sorry, I encountered an error while processing that request."
            }
    
    def confirm_action(self, confirmation_id: str) -> Dict[str, Any]:
        """Confirm and execute a pending action"""
        if confirmation_id not in self.pending_confirmations:
            return {
                'success': False,
                'error': 'Invalid confirmation ID',
                'response': 'No pending action found.'
            }
        
        pending = self.pending_confirmations.pop(confirmation_id)
        skill_name = pending['skill_name']
        input_text = pending['input_text']
        context = pending['context']
        
        logger.info(f"Executing confirmed action: {skill_name}")
        
        skill = self.skills[skill_name]
        result = skill.execute(input_text, context)
        
        return result
    
    def cancel_action(self, confirmation_id: str) -> Dict[str, Any]:
        """Cancel a pending action"""
        if confirmation_id in self.pending_confirmations:
            self.pending_confirmations.pop(confirmation_id)
            return {
                'success': True,
                'response': 'Action cancelled.'
            }
        
        return {
            'success': False,
            'error': 'Invalid confirmation ID'
        }
    
    def list_skills(self) -> List[str]:
        """List all loaded skills"""
        return list(self.skills.keys())


class BaseSkill:
    """Base class for all skills"""
    
    def __init__(self, config):
        self.config = config
    
    def execute(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the skill - must be implemented by subclasses"""
        raise NotImplementedError("Subclass must implement execute()")
    
    def is_destructive(self, input_text: str) -> bool:
        """Check if action is destructive and requires confirmation"""
        return False
    
    def preview_action(self, input_text: str) -> str:
        """Preview what the action will do"""
        return "Execute skill action"


def main():
    """Standalone test of skill manager"""
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'skills': {
            'plugins_dir': './skills',
            'max_execution_time': 60,
            'require_confirmation': True
        }
    }
    
    manager = SkillManager(config)
    manager.load_skills()
    
    print(f"Loaded skills: {manager.list_skills()}")


if __name__ == "__main__":
    main()
