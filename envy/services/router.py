"""Router service for intent classification and skill dispatch."""
import logging
import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.llm_adapter import LLMAdapter


class Router:
    """Routes user intents to appropriate skills."""
    
    def __init__(self, config, llm_adapter: LLMAdapter, logger: Optional[logging.Logger] = None):
        self.config = config.router
        self.llm_adapter = llm_adapter
        self.logger = logger or logging.getLogger("envy.router")
        
        # Intent patterns for rule-based classification
        self.intent_patterns = {
            'code': [
                r'\b(create|write|make|generate|code|program|script|file)\b.*\.(py|js|html|cpp|java|txt)',
                r'\b(create|write|make)\b.*\b(file|script|program|code)\b',
            ],
            'research': [
                r'\b(research|search|find|lookup|information about|tell me about)\b',
            ],
            'system': [
                r'\b(open|launch|start|run|execute|shutdown|restart)\b',
                r'\b(control|system|computer)\b',
            ],
            'reminder': [
                r'\b(remind|reminder|remember|alert|notify)\b',
            ],
        }
    
    def classify_intent(self, text: str) -> Tuple[str, float]:
        """Classify user intent from text."""
        text_lower = text.lower()
        
        if self.config.intent_classifier == "rule_based":
            return self._classify_rule_based(text_lower)
        else:
            # Use LLM for classification
            return self._classify_llm(text_lower)
    
    def _classify_rule_based(self, text: str) -> Tuple[str, float]:
        """Rule-based intent classification."""
        best_intent = "general"
        best_score = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, text))
                score += matches * 0.5
            
            if score > best_score:
                best_score = score
                best_intent = intent
        
        confidence = min(best_score, 1.0)
        if confidence < self.config.confidence_threshold:
            best_intent = "general"
        
        return best_intent, confidence
    
    def _classify_llm(self, text: str) -> Tuple[str, float]:
        """LLM-based intent classification."""
        prompt = f"""Classify the following user request into one of these categories: code, research, system, reminder, general.

User request: "{text}"

Respond with only the category name:"""
        
        try:
            response = self.llm_adapter.generate(prompt, max_tokens=10, temperature=0.1)
            intent = response.strip().lower()
            
            if intent in ['code', 'research', 'system', 'reminder', 'general']:
                return intent, 0.8
            else:
                return "general", 0.5
        except Exception as e:
            self.logger.error(f"LLM classification error: {e}")
            return self._classify_rule_based(text)
    
    def route(self, text: str) -> Dict[str, Any]:
        """Route user request to appropriate skill."""
        intent, confidence = self.classify_intent(text)
        
        self.logger.info(f"Intent: {intent} (confidence: {confidence:.2f})")
        
        return {
            'intent': intent,
            'confidence': confidence,
            'text': text,
            'skill_name': self._intent_to_skill(intent)
        }
    
    def _intent_to_skill(self, intent: str) -> str:
        """Map intent to skill name."""
        mapping = {
            'code': 'CodeSkill',
            'research': 'ResearchSkill',
            'system': 'SysControlSkill',
            'reminder': 'ReminderSkill',
            'general': 'GeneralSkill'
        }
        return mapping.get(intent, 'GeneralSkill')
