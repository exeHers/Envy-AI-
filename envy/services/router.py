"""
Router Service
Routes user requests to appropriate skills or LLM
MIT License
"""

import logging
from typing import Optional, Dict, Any
import time

from .config_manager import get_config
from .llm_adapter import LLMAdapter
from .stt_service import STTService
from .tts_service import TTSService

logger = logging.getLogger(__name__)


class Router:
    """Routes user commands to appropriate handlers"""
    
    def __init__(self, skill_manager):
        self.config = get_config()
        self.skill_manager = skill_manager
        self.llm_adapter = LLMAdapter()
        self.stt_service = STTService()
        self.tts_service = TTSService()
        
        # Configuration
        self.intent_threshold = self.config.get('router.intent_confidence_threshold', 0.6)
        self.llm_fallback = self.config.get('router.llm_fallback', True)
        self.max_processing_time = self.config.get('router.max_processing_time', 30)
        
        logger.info("Router initialized")
    
    def process_wake_event(self):
        """Handle wake word detection event"""
        try:
            logger.info("Wake word detected, listening for command...")
            
            # Acknowledge wake
            self.tts_service.speak("Yes?", save_to_file=False)
            
            # Listen for command
            command_text = self.stt_service.listen_and_transcribe(
                duration=8.0,
                silence_timeout=2.0
            )
            
            if command_text:
                logger.info(f"Command received: '{command_text}'")
                response = self.route_command(command_text)
                
                if response:
                    self.tts_service.speak(response)
            else:
                logger.warning("No command received")
                self.tts_service.speak("I didn't catch that.", save_to_file=False)
                
        except Exception as e:
            logger.error(f"Error processing wake event: {e}")
            self.tts_service.speak("I encountered an error.", save_to_file=False)
    
    def route_command(self, command: str) -> Optional[str]:
        """
        Route command to appropriate skill or LLM
        Returns response text
        """
        try:
            start_time = time.time()
            
            # Classify intent
            intent = self.llm_adapter.classify_intent(command)
            logger.info(f"Classified intent: {intent}")
            
            response = None
            
            # Route to skill if recognized
            if intent != 'unknown' and self.skill_manager.has_skill(intent):
                logger.info(f"Routing to skill: {intent}")
                response = self.skill_manager.execute_skill(intent, command)
            
            # Fallback to LLM if skill fails or intent unknown
            if response is None and self.llm_fallback:
                logger.info("Using LLM fallback")
                response, source = self.llm_adapter.generate(
                    prompt=f"User request: {command}\nProvide a brief, helpful response.",
                    max_tokens=200
                )
                
                if source == 'remote':
                    logger.info("Response from remote LLM")
            
            # Final fallback
            if response is None:
                response = "I'm not sure how to help with that."
            
            elapsed = time.time() - start_time
            logger.info(f"Command processed in {elapsed:.2f}s")
            
            # Check timeout
            if elapsed > self.max_processing_time:
                logger.warning(f"Processing exceeded max time ({self.max_processing_time}s)")
            
            return response
            
        except Exception as e:
            logger.error(f"Error routing command: {e}")
            return "I encountered an error processing that request."
    
    def handle_manual_command(self, command: str) -> Dict[str, Any]:
        """
        Handle command from web dashboard (manual entry)
        Returns dict with response and metadata
        """
        try:
            response = self.route_command(command)
            
            return {
                'success': True,
                'command': command,
                'response': response,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error handling manual command: {e}")
            return {
                'success': False,
                'command': command,
                'error': str(e),
                'timestamp': time.time()
            }
