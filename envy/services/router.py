"""Router service for intent classification and routing."""
import asyncio
from typing import Dict, Any, Optional
from .logger import setup_logger
from .config_loader import get_config
from .llm_adapter import LLMAdapter
from .tts_service import TTSService


class Router:
    """Route user requests to appropriate skills."""
    
    def __init__(self, skill_manager=None):
        self.config = get_config()
        self.logger = setup_logger("Router", self.config.get("logging.file"))
        
        self.llm_adapter = LLMAdapter()
        self.skill_manager = skill_manager
        self.tts = TTSService()
        
        self.confidence_threshold = self.config.get("router.confidence_threshold", 0.7)
        self.timeout = self.config.get("router.timeout", 30)
        
    def initialize(self):
        """Initialize router components."""
        self.logger.info("Initializing router...")
        
        llm_init = self.llm_adapter.initialize()
        tts_init = self.tts.initialize()
        
        self.logger.info(f"Router initialized (LLM: {llm_init}, TTS: {tts_init})")
        return True
        
    async def process_request(self, text: str) -> Dict[str, Any]:
        """Process user request and route to appropriate skill."""
        self.logger.info(f"Processing request: {text}")
        
        # Classify intent
        intent = self.llm_adapter.classify_intent(text)
        self.logger.info(f"Intent: {intent}")
        
        result = {
            "text": text,
            "intent": intent,
            "response": "",
            "success": False
        }
        
        # Route to skill if confidence is high enough
        if intent["confidence"] >= self.confidence_threshold and intent["skill"]:
            if self.skill_manager:
                skill_result = await self.skill_manager.execute_skill(
                    intent["skill"],
                    intent["action"],
                    intent["params"]
                )
                result["response"] = skill_result.get("response", "")
                result["success"] = skill_result.get("success", False)
            else:
                result["response"] = f"Skill manager not available for {intent['skill']}"
                
        else:
            # Use LLM for general conversation
            prompt = self._build_prompt(text, intent)
            response = self.llm_adapter.generate(prompt, max_tokens=256)
            result["response"] = response
            result["success"] = True
            
        # Speak the response
        if result["response"]:
            self.tts.speak(result["response"], blocking=False)
            
        self.logger.info(f"Response: {result['response']}")
        return result
        
    def _build_prompt(self, text: str, intent: Dict[str, Any]) -> str:
        """Build prompt for LLM."""
        persona = self.config.get("persona.style", "neutral")
        verbosity = self.config.get("persona.verbosity", "concise")
        
        system_prompt = "You are Envy, a personal assistant. "
        
        if persona == "neutral":
            system_prompt += "Be professional and helpful. "
        elif persona == "friendly":
            system_prompt += "Be warm and friendly. "
        elif persona == "sardonic":
            system_prompt += "Be slightly sardonic but helpful. "
            
        if verbosity == "concise":
            system_prompt += "Keep responses brief and to the point."
        elif verbosity == "detailed":
            system_prompt += "Provide detailed explanations."
        else:
            system_prompt += "Provide balanced responses."
            
        prompt = f"{system_prompt}\n\nUser: {text}\nEnvy:"
        return prompt
        
    def speak(self, text: str, blocking: bool = False):
        """Speak text using TTS."""
        self.tts.speak(text, blocking=blocking)


def main():
    """Test router."""
    router = Router()
    router.initialize()
    
    # Test requests
    test_requests = [
        "Hello Envy",
        "Create a file called test.py that prints hello",
        "Research quantum computing",
        "Remind me to call mom tomorrow"
    ]
    
    async def test():
        for request in test_requests:
            print(f"\n>>> {request}")
            result = await router.process_request(request)
            print(f"<<< {result['response']}")
            
    asyncio.run(test())


if __name__ == "__main__":
    main()
