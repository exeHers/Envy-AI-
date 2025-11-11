#!/usr/bin/env python3
"""
Router Service - Routes user requests to appropriate skills
Handles intent classification and skill dispatch
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Router:
    """Routes user requests to skills based on intent"""
    
    def __init__(self, config, llm_adapter, skill_manager):
        self.config = config
        self.router_config = config.get('router', {})
        self.llm = llm_adapter
        self.skill_manager = skill_manager
        
        self.intent_threshold = self.router_config.get('intent_threshold', 0.7)
        self.max_retries = self.router_config.get('max_retries', 2)
        
        logger.info("Router initialized")
    
    def route(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route user input to appropriate skill"""
        logger.info(f"Routing request: {text[:100]}...")
        
        # Step 1: Classify intent
        intent_result = self.llm.classify_intent(text)
        intent = intent_result['intent']
        confidence = intent_result['confidence']
        
        logger.info(f"Intent classified: {intent} (confidence: {confidence:.2f})")
        
        # Step 2: If confidence is low, use LLM for better understanding
        if confidence < self.intent_threshold:
            logger.info("Low confidence, consulting LLM for clarification")
            llm_response = self.llm.generate(
                prompt=text,
                system_prompt="You are Envy, a helpful AI assistant. Classify the user's intent and provide a concise response."
            )
            
            # Re-classify based on LLM response
            intent_result = self._interpret_llm_response(text, llm_response)
            intent = intent_result['intent']
        
        # Step 3: Route to appropriate skill
        return self._dispatch_to_skill(intent, text, context)
    
    def _interpret_llm_response(self, original_text: str, llm_response: str) -> Dict[str, Any]:
        """Interpret LLM response to extract intent"""
        # Simple keyword-based interpretation
        response_lower = llm_response.lower()
        
        if any(word in response_lower for word in ['create', 'file', 'code', 'script']):
            return {'intent': 'code', 'confidence': 0.8, 'llm_response': llm_response}
        elif any(word in response_lower for word in ['research', 'find', 'search']):
            return {'intent': 'research', 'confidence': 0.8, 'llm_response': llm_response}
        elif any(word in response_lower for word in ['remind', 'schedule']):
            return {'intent': 'reminder', 'confidence': 0.8, 'llm_response': llm_response}
        elif any(word in response_lower for word in ['system', 'command', 'execute']):
            return {'intent': 'system', 'confidence': 0.8, 'llm_response': llm_response}
        else:
            return {'intent': 'general', 'confidence': 0.6, 'llm_response': llm_response}
    
    def _dispatch_to_skill(self, intent: str, text: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Dispatch request to appropriate skill"""
        
        # Map intents to skills
        skill_map = {
            'code': 'code_skill',
            'research': 'research_skill',
            'system': 'sys_control_skill',
            'reminder': 'reminder_skill'
        }
        
        skill_name = skill_map.get(intent)
        
        if skill_name:
            logger.info(f"Dispatching to skill: {skill_name}")
            result = self.skill_manager.execute_skill(skill_name, text, context)
            return result
        else:
            # General query - use LLM directly
            logger.info("General query, using LLM response")
            response = self.llm.generate(
                prompt=text,
                system_prompt="You are Envy, a helpful and slightly sardonic AI assistant. Be concise and direct."
            )
            
            return {
                'success': True,
                'intent': 'general',
                'response': response,
                'action': None
            }


def main():
    """Standalone test of router"""
    logging.basicConfig(level=logging.INFO)
    
    # Mock dependencies
    class MockLLM:
        def classify_intent(self, text):
            if 'create' in text.lower():
                return {'intent': 'code', 'confidence': 0.9, 'text': text}
            return {'intent': 'general', 'confidence': 0.5, 'text': text}
        
        def generate(self, prompt, system_prompt=None):
            return "This is a mock LLM response."
    
    class MockSkillManager:
        def execute_skill(self, skill_name, text, context):
            return {
                'success': True,
                'intent': 'code',
                'response': f"Executed {skill_name}",
                'action': 'file_created'
            }
    
    config = {
        'router': {
            'intent_threshold': 0.7,
            'max_retries': 2
        }
    }
    
    router = Router(config, MockLLM(), MockSkillManager())
    
    # Test routing
    result = router.route("Create a Python file that prints hello")
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
