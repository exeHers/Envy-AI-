"""
Router service that routes user requests to appropriate skills.
"""
import asyncio
import logging
from typing import Dict, Any, Optional

from .base_service import BaseService
from .llm_adapter import LLMAdapter

logger = logging.getLogger(__name__)


class Router(BaseService):
    """Routes user requests to skills based on intent."""
    
    def __init__(self, config: dict, llm_adapter: LLMAdapter, skill_manager):
        super().__init__("Router", config)
        self.llm_adapter = llm_adapter
        self.skill_manager = skill_manager
        
    async def start(self):
        """Initialize router."""
        logger.info("Initializing router")
        self.running = True
        logger.info("Router ready")
    
    async def route(self, user_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route user request to appropriate skill."""
        logger.info(f"Routing request: {user_text}")
        
        # Classify intent
        intent_result = await self.llm_adapter.classify_intent(user_text)
        intent = intent_result.get('intent')
        skill_name = intent_result.get('skill')
        
        logger.info(f"Intent: {intent}, Skill: {skill_name}")
        
        if not skill_name:
            # No specific skill, generate general response
            response = await self.llm_adapter.generate(
                f"User said: {user_text}\nEnvy (assistant):",
                max_tokens=100
            )
            return {
                'success': True,
                'response': response,
                'skill': None,
                'outputs': []
            }
        
        # Get skill from manager
        skill = self.skill_manager.get_skill(skill_name)
        if not skill:
            logger.warning(f"Skill {skill_name} not found")
            response = await self.llm_adapter.generate(
                f"User requested: {user_text}\nEnvy (assistant):",
                max_tokens=100
            )
            return {
                'success': True,
                'response': response,
                'skill': None,
                'outputs': []
            }
        
        # Check if confirmation required
        requires_confirmation = self._requires_confirmation(skill_name, user_text)
        
        if requires_confirmation:
            return {
                'success': False,
                'requires_confirmation': True,
                'skill': skill_name,
                'user_text': user_text,
                'response': f"I need confirmation before executing: {user_text}"
            }
        
        # Execute skill
        try:
            result = await skill.execute(user_text, context or {})
            return {
                'success': True,
                'response': result.get('response', 'Done.'),
                'skill': skill_name,
                'outputs': result.get('outputs', [])
            }
        except Exception as e:
            logger.error(f"Skill execution error: {e}")
            return {
                'success': False,
                'response': f"Error executing {skill_name}: {str(e)}",
                'skill': skill_name,
                'outputs': []
            }
    
    def _requires_confirmation(self, skill_name: str, user_text: str) -> bool:
        """Check if action requires confirmation."""
        skills_config = self.config.get('skills', {})
        require_conf = skills_config.get('require_confirmation', [])
        
        user_lower = user_text.lower()
        
        # Check for destructive keywords
        destructive_keywords = ['delete', 'remove', 'kill', 'shutdown', 'format', 'rm -rf']
        if any(keyword in user_lower for keyword in destructive_keywords):
            return True
        
        # Check skill-specific requirements
        for req in require_conf:
            if skill_name in req:
                return True
        
        return False
    
    async def stop(self):
        """Stop router."""
        logger.info("Stopping router")
        self.running = False
        logger.info("Router stopped")
