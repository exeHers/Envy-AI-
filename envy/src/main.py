#!/usr/bin/env python3
"""
Envy Main Orchestrator
Coordinates all services: wake listener, STT, router, skills, TTS.
"""

import logging
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Optional

import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from wake_listener.wake_listener import WakeWordListener
from stt_service.stt_service import STTService
from router.router import Router
from skill_manager.skill_manager import SkillManager
from tts_service.tts_service import TTSService
from llm_adapter.llm_adapter import LLMAdapter

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
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        
        self.running = False
        self.services = {}
        
        # Initialize services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all services."""
        logger.info("Initializing Envy services...")
        
        try:
            # LLM Adapter
            llm_config = self.config.get('llm', {})
            self.services['llm'] = LLMAdapter(llm_config)
            if not self.services['llm'].initialize():
                logger.warning("LLM adapter initialization failed, continuing with fallback")
            
            # Router
            router_config = self.config.get('router', {})
            self.services['router'] = Router(router_config, self.services['llm'])
            
            # Skill Manager
            skills_config = self.config.get('skills', {})
            skills_config['skills_dir'] = Path(__file__).parent.parent / 'skills'
            self.services['skills'] = SkillManager(skills_config)
            
            # STT Service
            stt_config = self.config.get('stt', {})
            self.services['stt'] = STTService(stt_config)
            if not self.services['stt'].initialize():
                logger.error("STT service initialization failed")
                sys.exit(1)
            
            # TTS Service
            tts_config = self.config.get('tts', {})
            self.services['tts'] = TTSService(tts_config)
            if not self.services['tts'].initialize():
                logger.error("TTS service initialization failed")
                sys.exit(1)
            
            # Wake Listener
            wake_config = self.config.get('wake', {})
            self.services['wake'] = WakeWordListener(wake_config)
            if not self.services['wake'].initialize():
                logger.error("Wake listener initialization failed")
                sys.exit(1)
            
            logger.info("All services initialized successfully")
        except Exception as e:
            logger.error(f"Service initialization failed: {e}")
            sys.exit(1)
    
    def run(self):
        """Main run loop."""
        self.running = True
        logger.info("Envy assistant started")
        
        # Start web dashboard in background
        web_thread = threading.Thread(target=self._start_web_dashboard, daemon=True)
        web_thread.start()
        
        try:
            while self.running:
                # Listen for wake word
                logger.info("Listening for wake word...")
                detected = self.services['wake'].listen()
                
                if detected:
                    logger.info("Wake word detected, starting interaction...")
                    self._handle_interaction()
                
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.stop()
    
    def _handle_interaction(self):
        """Handle a single user interaction."""
        try:
            # Record and transcribe
            logger.info("Recording user input...")
            text = self.services['stt'].transcribe()
            
            if not text:
                logger.warning("No transcription received")
                return
            
            logger.info(f"User said: {text}")
            
            # Route to skill
            skill_name, params = self.services['router'].route(text)
            logger.info(f"Routed to: {skill_name}")
            
            # Execute skill
            result = self.services['skills'].execute(skill_name, params, require_confirmation=False)
            
            if result.get('requires_confirmation'):
                logger.info("Confirmation required")
                response_text = "I need your confirmation to proceed. Please confirm in the dashboard."
            elif result.get('success'):
                response_text = result.get('message', 'Done.')
            else:
                response_text = f"Sorry, I encountered an error: {result.get('error', 'Unknown error')}"
            
            # Generate LLM response if needed
            if not result.get('success') or result.get('requires_confirmation'):
                llm_response = self.services['llm'].generate(
                    f"User asked: {text}. My response: {response_text}. Generate a natural spoken response.",
                    max_tokens=50
                )
                if llm_response:
                    response_text = llm_response
            
            # Speak response
            logger.info(f"Responding: {response_text}")
            self.services['tts'].speak(response_text)
            
        except Exception as e:
            logger.error(f"Interaction handling failed: {e}")
            self.services['tts'].speak("Sorry, I encountered an error. Please try again.")
    
    def _start_web_dashboard(self):
        """Start web dashboard server."""
        try:
            from web_dashboard.web_dashboard import WebDashboard
            
            web_config = self.config.get('web', {})
            dashboard = WebDashboard(web_config, self.services)
            dashboard.run()
        except Exception as e:
            logger.error(f"Web dashboard failed: {e}")
    
    def stop(self):
        """Stop all services."""
        self.running = False
        if 'wake' in self.services:
            self.services['wake'].stop()
        logger.info("Envy assistant stopped")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Envy Personal Assistant')
    parser.add_argument('--config', type=Path, default=Path(__file__).parent / 'config' / 'envy.yaml')
    parser.add_argument('--profile', choices=['low', 'balanced', 'power'], default='balanced')
    parser.add_argument('--no-gui', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    # Load and adjust config based on profile
    config_path = args.config
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    assistant = EnvyAssistant(config_path)
    
    # Handle signals
    def signal_handler(sig, frame):
        logger.info("Received interrupt signal")
        assistant.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run
    assistant.run()


if __name__ == '__main__':
    main()
