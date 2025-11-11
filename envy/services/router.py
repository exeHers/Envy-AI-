"""Router service for intent classification and skill dispatch."""
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
import importlib
import importlib.util
import sys
from pathlib import Path


logger = logging.getLogger(__name__)


class Router:
    """Routes user intents to appropriate skills."""
    
    def __init__(self, config, llm_adapter):
        self.config = config
        self.llm_adapter = llm_adapter
        self.intent_classifier = config.get("router.intent_classifier", "rule_based")
        self.confidence_threshold = config.get("router.confidence_threshold", 0.6)
        self.fallback_to_llm = config.get("router.fallback_to_llm", True)
        self.skills: Dict[str, Any] = {}
        self._load_skills()
    
    def _load_skills(self):
        """Load available skills."""
        skills_dir = Path(__file__).parent.parent / "skills"
        enabled_skills = self.config.get("skills.enabled", [])
        
        for skill_name in enabled_skills:
            try:
                # Import skill module
                module_path = skills_dir / f"{skill_name.lower()}.py"
                if not module_path.exists():
                    logger.warning(f"Skill file not found: {module_path}")
                    continue
                
                spec = importlib.util.spec_from_file_location(
                    skill_name.lower(),
                    module_path
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules[skill_name.lower()] = module
                spec.loader.exec_module(module)
                
                # Get skill class
                skill_class = getattr(module, skill_name, None)
                if skill_class:
                    skill_instance = skill_class(self.config)
                    self.skills[skill_name] = skill_instance
                    logger.info(f"Loaded skill: {skill_name}")
            except Exception as e:
                logger.error(f"Failed to load skill {skill_name}: {e}")
    
    def _classify_intent_rule_based(self, text: str) -> Tuple[Optional[str], float]:
        """Rule-based intent classification."""
        text_lower = text.lower()
        
        # Code-related intents
        code_patterns = [
            r"create.*\.(py|js|html|css|txt|md|json)",
            r"write.*file",
            r"make.*file",
            r"edit.*file",
            r"code",
            r"program"
        ]
        for pattern in code_patterns:
            if re.search(pattern, text_lower):
                return "CodeSkill", 0.9
        
        # Research intents
        research_patterns = [
            r"research",
            r"search.*for",
            r"find.*about",
            r"look.*up",
            r"what.*is",
            r"tell.*me.*about"
        ]
        for pattern in research_patterns:
            if re.search(pattern, text_lower):
                return "ResearchSkill", 0.85
        
        # System control intents
        sys_patterns = [
            r"shutdown",
            r"restart",
            r"open.*application",
            r"run.*command",
            r"execute",
            r"system"
        ]
        for pattern in sys_patterns:
            if re.search(pattern, text_lower):
                return "SysControlSkill", 0.8
        
        # Reminder intents
        reminder_patterns = [
            r"remind.*me",
            r"set.*reminder",
            r"alarm",
            r"schedule",
            r"at.*pm",
            r"at.*am"
        ]
        for pattern in reminder_patterns:
            if re.search(pattern, text_lower):
                return "ReminderSkill", 0.85
        
        return None, 0.0
    
    def _classify_intent_llm(self, text: str) -> Tuple[Optional[str], float]:
        """LLM-based intent classification."""
        prompt = f"""Classify the user's intent into one of these skills:
- CodeSkill: Creating, editing, or managing code files
- ResearchSkill: Searching for information, researching topics
- SysControlSkill: System commands, opening apps, controlling the computer
- ReminderSkill: Setting reminders, alarms, schedules

User request: "{text}"

Respond with only the skill name, or "unknown" if none match."""
        
        response = self.llm_adapter.generate(prompt, max_tokens=50)
        response = response.strip().split()[0] if response else "unknown"
        
        if response in self.skills:
            return response, 0.7
        return None, 0.0
    
    def classify_intent(self, text: str) -> Tuple[Optional[str], float]:
        """Classify user intent."""
        if self.intent_classifier == "rule_based":
            skill_name, confidence = self._classify_intent_rule_based(text)
        else:
            skill_name, confidence = self._classify_intent_llm(text)
        
        # Fallback to LLM if rule-based fails and fallback enabled
        if not skill_name and self.fallback_to_llm:
            skill_name, confidence = self._classify_intent_llm(text)
        
        return skill_name, confidence
    
    def route(self, text: str) -> Dict[str, any]:
        """Route user request to appropriate skill."""
        logger.info(f"Routing request: {text}")
        
        skill_name, confidence = self.classify_intent(text)
        
        if not skill_name or confidence < self.confidence_threshold:
            logger.warning(f"Could not classify intent with sufficient confidence: {confidence}")
            return {
                "success": False,
                "skill": None,
                "response": "I'm not sure how to help with that. Could you rephrase?",
                "confidence": confidence
            }
        
        if skill_name not in self.skills:
            logger.error(f"Skill {skill_name} not loaded")
            return {
                "success": False,
                "skill": skill_name,
                "response": f"Skill {skill_name} is not available.",
                "confidence": confidence
            }
        
        skill = self.skills[skill_name]
        
        # Check if confirmation required
        require_confirmation = skill_name in self.config.get("skills.require_confirmation", [])
        
        try:
            result = skill.execute(text)
            return {
                "success": True,
                "skill": skill_name,
                "response": result.get("response", "Done."),
                "data": result.get("data", {}),
                "requires_confirmation": require_confirmation,
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"Skill execution failed: {e}")
            return {
                "success": False,
                "skill": skill_name,
                "response": f"I encountered an error: {str(e)}",
                "confidence": confidence
            }
