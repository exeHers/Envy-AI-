"""
Router service for intent classification and skill dispatch
Coordinates between STT, LLM, skills, and TTS
"""
import logging
from typing import Dict, Any, Optional
import time

from services.config_loader import get_config
from services.llm_adapter import LLMAdapter
from services.stt_service import STTService
from services.tts_service import TTSService
from skills.skill_manager import SkillManager


class Router:
    """Main router for Envy assistant"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger("Router")
        
        # Initialize services
        self.llm = LLMAdapter()
        self.stt = STTService()
        self.tts = TTSService()
        self.skill_manager = SkillManager()
        
        # Load persona
        self.persona_name = self.config.get('persona.name', 'Envy')
        self.persona_style = self.config.get('persona.style', 'neutral')
        self.greeting = self.config.get('persona.voice_greeting', 'Envy online. How can I assist?')
        
        self.logger.info("Router initialized")
    
    def handle_wake(self):
        """Handle wake word detection"""
        self.logger.info("Wake word detected, starting interaction...")
        
        # Acknowledge
        self.tts.speak("Yes?")
        
        # Record command
        self.logger.info("Listening for command...")
        command = self.stt.record_and_transcribe(
            on_partial=lambda text: self.logger.debug(f"Partial: {text}")
        )
        
        if not command or len(command.strip()) < 3:
            self.tts.speak("I didn't catch that.")
            return
        
        self.logger.info(f"Command received: {command}")
        
        # Process command
        response = self.process_command(command)
        
        # Speak response
        if response:
            self.tts.speak(response)
    
    def process_command(self, command: str) -> str:
        """Process user command and return response"""
        self.logger.info(f"Processing command: {command}")
        
        # Classify intent
        intent = self.llm.classify_intent(command)
        self.logger.info(f"Classified intent: {intent}")
        
        skill_name = intent.get('skill')
        action = intent.get('action')
        
        # Dispatch to skill
        if skill_name and skill_name != 'ChatSkill':
            result = self.skill_manager.execute_skill(
                skill_name=skill_name,
                action=action,
                command=command,
                parameters={}
            )
            
            if result['success']:
                response = result.get('response', 'Done.')
            else:
                response = f"I encountered an error: {result.get('error', 'Unknown error')}"
        else:
            # General chat using LLM
            system_prompt = self._get_system_prompt()
            response = self.llm.generate(command, system=system_prompt)
        
        return response
    
    def _get_system_prompt(self) -> str:
        """Get system prompt based on persona"""
        if self.persona_style == 'friendly':
            return f"You are {self.persona_name}, a friendly and helpful personal assistant. Be warm and encouraging."
        elif self.persona_style == 'sardonic':
            return f"You are {self.persona_name}, a capable but slightly sardonic personal assistant. Be helpful but with a touch of dry wit."
        else:
            return f"You are {self.persona_name}, a neutral and efficient personal assistant. Be concise and professional."
    
    def test_pipeline(self, test_command: str = "Hello Envy") -> tuple[bool, str]:
        """Test the full pipeline"""
        self.logger.info(f"Testing pipeline with command: {test_command}")
        
        try:
            response = self.process_command(test_command)
            
            if response and len(response) > 0:
                self.logger.info(f"✓ Pipeline test successful: {response}")
                return True, response
            else:
                self.logger.error("✗ Pipeline test failed: no response")
                return False, "No response"
                
        except Exception as e:
            self.logger.error(f"✗ Pipeline test failed: {e}")
            return False, str(e)


def main():
    """Test router standalone"""
    logging.basicConfig(level=logging.INFO)
    
    router = Router()
    
    # Test commands
    commands = [
        "Create a file called test.py that prints hello world",
        "What is the weather like?",
        "Remind me to buy milk"
    ]
    
    for cmd in commands:
        print(f"\n--- Command: {cmd} ---")
        response = router.process_command(cmd)
        print(f"Response: {response}\n")


if __name__ == "__main__":
    main()
