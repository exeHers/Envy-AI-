"""GeneralSkill - fallback skill for general queries."""
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.skill_manager import BaseSkill


class GeneralSkill(BaseSkill):
    """General fallback skill for queries that don't match specific intents."""
    
    def __init__(self, config, llm_adapter=None, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        # If llm_adapter not provided, create one
        if llm_adapter is None:
            from services.llm_adapter import LLMAdapter
            self.llm_adapter = LLMAdapter(config, logger)
            self.llm_adapter.initialize()
        else:
            self.llm_adapter = llm_adapter
    
    def execute(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general query."""
        text = intent_data.get('text', '')
        
        try:
            # Use LLM to generate response
            prompt = f"User: {text}\nAssistant:"
            response = self.llm_adapter.generate(prompt, max_tokens=200)
            
            return {
                'success': True,
                'response': response,
                'message': response
            }
        except Exception as e:
            self.logger.error(f"Error in general skill: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "I'm sorry, I didn't understand that."
            }
    
    def requires_confirmation(self, intent_data: Dict[str, Any]) -> bool:
        """General queries don't require confirmation."""
        return False
