"""
Main orchestrator for Envy personal assistant.
Coordinates all services and handles the main event loop.
"""
import asyncio
import logging
import yaml
import os
import sys
from pathlib import Path

from services.wake_listener import WakeListener
from services.stt_service import STTService
from services.tts_service import TTSService
from services.llm_adapter import LLMAdapter
from services.router import Router
from services.skill_manager import SkillManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('artifacts/envy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EnvyAssistant:
    """Main Envy assistant orchestrator."""
    
    def __init__(self, config_path: str = 'config/envy.yaml'):
        self.config_path = config_path
        self.config = self._load_config()
        self.wake_listener: WakeListener = None
        self.stt_service: STTService = None
        self.tts_service: TTSService = None
        self.llm_adapter: LLMAdapter = None
        self.router: Router = None
        self.skill_manager: SkillManager = None
        self.running = False
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return {}
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded config from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    async def initialize(self):
        """Initialize all services."""
        logger.info("Initializing Envy assistant...")
        
        # Initialize LLM adapter first (needed by router)
        self.llm_adapter = LLMAdapter(self.config)
        await self.llm_adapter.start()
        
        # Initialize skill manager
        skills_dir = os.path.join(os.path.dirname(__file__), 'skills')
        self.skill_manager = SkillManager(self.config, skills_dir)
        self.skill_manager.load_skills()
        
        # Initialize router
        self.router = Router(self.config, self.llm_adapter, self.skill_manager)
        await self.router.start()
        
        # Initialize TTS service
        self.tts_service = TTSService(self.config)
        await self.tts_service.start()
        
        # Initialize STT service
        self.stt_service = STTService(self.config)
        await self.stt_service.start()
        
        # Initialize wake listener with callback
        self.wake_listener = WakeListener(self.config, self._on_wake_detected)
        
        logger.info("All services initialized")
    
    async def _on_wake_detected(self):
        """Handle wake word detection."""
        logger.info("Wake word detected!")
        
        # Speak acknowledgment
        await self.tts_service.speak_async("Yes?")
        
        # Record and transcribe user input
        logger.info("Listening for user input...")
        user_text = await self.stt_service.record_and_transcribe(duration=5.0)
        
        if not user_text or len(user_text.strip()) < 2:
            logger.warning("No valid user input detected")
            await self.tts_service.speak_async("I didn't catch that. Please try again.")
            return
        
        logger.info(f"User said: {user_text}")
        
        # Route request
        result = await self.router.route(user_text)
        
        # Handle result
        if result.get('requires_confirmation'):
            # Request confirmation
            confirmation_text = f"{result['response']} Please confirm in the dashboard."
            await self.tts_service.speak_async(confirmation_text)
        else:
            # Execute and respond
            response = result.get('response', 'Done.')
            await self.tts_service.speak_async(response)
            
            # Log outputs
            for output in result.get('outputs', []):
                if output.get('type') == 'file':
                    logger.info(f"Created file: {output['path']}")
    
    async def start(self):
        """Start the assistant."""
        logger.info("Starting Envy assistant...")
        await self.initialize()
        
        self.running = True
        
        # Start wake listener (runs continuously)
        try:
            await self.wake_listener.start()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop all services."""
        logger.info("Stopping Envy assistant...")
        self.running = False
        
        if self.wake_listener:
            await self.wake_listener.stop()
        if self.stt_service:
            await self.stt_service.stop()
        if self.tts_service:
            await self.tts_service.stop()
        if self.router:
            await self.router.stop()
        if self.llm_adapter:
            await self.llm_adapter.stop()
        
        logger.info("Envy assistant stopped")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Envy Personal Assistant')
    parser.add_argument('--config', default='config/envy.yaml', help='Config file path')
    parser.add_argument('--profile', choices=['low', 'balanced', 'power'], help='Resource profile')
    parser.add_argument('--no-gui', action='store_true', help='Run without GUI')
    args = parser.parse_args()
    
    # Update config if profile specified
    assistant = EnvyAssistant(args.config)
    if args.profile:
        assistant.config['profile'] = args.profile
    
    try:
        await assistant.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
