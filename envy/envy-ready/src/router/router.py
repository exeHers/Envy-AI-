#!/usr/bin/env python3
"""
Router Service
Routes user intents to appropriate skills using rule-based or LLM-based classification.
"""

import logging
import re
from typing import Dict, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Router:
    """Routes user intents to skills."""
    
    def __init__(self, config: dict, llm_adapter):
        self.config = config
        self.llm_adapter = llm_adapter
        self.classifier_type = config.get('intent_classifier', 'rule_based')
        self.confidence_threshold = config.get('confidence_threshold', 0.6)
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout_seconds', 30)
        
        # Intent patterns
        self.intent_patterns = {
            'code': [
                r'create.*file',
                r'write.*code',
                r'make.*\.py',
                r'create.*\.(py|js|html|txt)',
                r'write.*script',
            ],
            'research': [
                r'research.*',
                r'find.*about',
                r'look.*up',
                r'what.*is',
                r'tell.*me.*about',
            ],
            'system': [
                r'open.*',
                r'launch.*',
                r'run.*command',
                r'execute.*',
                r'system.*',
            ],
            'reminder': [
                r'remind.*',
                r'set.*reminder',
                r'remember.*',
                r'alert.*',
            ],
        }
    
    def route(self, text: str) -> Tuple[str, Dict]:
        """Route text to appropriate skill and extract parameters."""
        text_lower = text.lower()
        
        # Remove wake word if present
        text_lower = re.sub(r'\benvy\b', '', text_lower).strip()
        
        if self.classifier_type == 'rule_based':
            return self._route_rule_based(text_lower)
        else:
            return self._route_llm_based(text_lower)
    
    def _route_rule_based(self, text: str) -> Tuple[str, Dict]:
        """Route using rule-based patterns."""
        scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    score += 1
            
            if score > 0:
                scores[intent] = score / len(patterns)
        
        if scores:
            best_intent = max(scores.items(), key=lambda x: x[1])
            if best_intent[1] >= self.confidence_threshold:
                skill_name = self._intent_to_skill(best_intent[0])
                params = self._extract_params(text, best_intent[0])
                logger.info(f"Routed to {skill_name} with confidence {best_intent[1]:.2f}")
                return skill_name, params
        
        # Default fallback
        logger.warning(f"No intent matched, using default")
        return 'CodeSkill', {'text': text}
    
    def _route_llm_based(self, text: str) -> Tuple[str, Dict]:
        """Route using LLM-based classification."""
        prompt = f"""Classify this user request into one of these categories:
- code: Creating files, writing code, scripts
- research: Researching topics, finding information
- system: System control, opening apps, running commands
- reminder: Setting reminders, alerts

User request: "{text}"

Respond with only the category name and a JSON object with parameters."""
        
        try:
            response = self.llm_adapter.generate(prompt, max_tokens=100)
            
            # Parse response
            intent = None
            for cat in ['code', 'research', 'system', 'reminder']:
                if cat in response.lower():
                    intent = cat
                    break
            
            if intent:
                skill_name = self._intent_to_skill(intent)
                params = self._extract_params(text, intent)
                return skill_name, params
            else:
                return self._route_rule_based(text)
                
        except Exception as e:
            logger.error(f"LLM routing failed: {e}")
            return self._route_rule_based(text)
    
    def _intent_to_skill(self, intent: str) -> str:
        """Map intent to skill name."""
        mapping = {
            'code': 'CodeSkill',
            'research': 'ResearchSkill',
            'system': 'SysControlSkill',
            'reminder': 'ReminderSkill',
        }
        return mapping.get(intent, 'CodeSkill')
    
    def _extract_params(self, text: str, intent: str) -> Dict:
        """Extract parameters from text based on intent."""
        params = {'text': text, 'original': text}
        
        if intent == 'code':
            # Extract filename
            file_match = re.search(r'create\s+(\S+\.\w+)|make\s+(\S+\.\w+)|write\s+(\S+\.\w+)', text)
            if file_match:
                params['filename'] = file_match.group(1) or file_match.group(2) or file_match.group(3)
            
            # Extract content
            content_match = re.search(r'that\s+(prints|says|contains|writes)\s+(.+)', text)
            if content_match:
                params['content'] = content_match.group(2)
        
        elif intent == 'research':
            # Extract topic
            topic_match = re.search(r'research\s+(.+)|find.*about\s+(.+)|what.*is\s+(.+)', text)
            if topic_match:
                params['topic'] = topic_match.group(1) or topic_match.group(2) or topic_match.group(3)
        
        elif intent == 'reminder':
            # Extract reminder details
            time_match = re.search(r'in\s+(\d+)\s*(minute|hour|day)', text)
            if time_match:
                params['delay'] = int(time_match.group(1))
                params['unit'] = time_match.group(2)
            
            reminder_match = re.search(r'remind.*to\s+(.+)|remember\s+(.+)', text)
            if reminder_match:
                params['message'] = reminder_match.group(1) or reminder_match.group(2)
        
        elif intent == 'system':
            # Extract command
            cmd_match = re.search(r'(open|launch|run)\s+(.+)', text)
            if cmd_match:
                params['command'] = cmd_match.group(2)
        
        return params


if __name__ == '__main__':
    import yaml
    import json
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from llm_adapter.llm_adapter import LLMAdapter
    
    config_path = Path(__file__).parent.parent.parent / 'config' / 'envy.yaml'
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    router_config = config.get('router', {})
    llm_config = config.get('llm', {})
    
    llm_adapter = LLMAdapter(llm_config)
    if not llm_adapter.initialize():
        logger.warning("LLM adapter not initialized, using rule-based only")
    
    router = Router(router_config, llm_adapter)
    
    test_text = "Envy, create test.py that prints hello"
    skill, params = router.route(test_text)
    print(f"SKILL:{skill}")
    print(f"PARAMS:{json.dumps(params)}")
