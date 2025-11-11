#!/usr/bin/env python3
"""
Envy AI Assistant - Main Orchestrator
Coordinates all services and manages the assistant's lifecycle
"""

import os
import sys
import yaml
import logging
import signal
import threading
from pathlib import Path

# Add services and skills to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'skills'))

from services.wake_listener import WakeListener
from services.stt_service import STTService
from services.tts_service import TTSService
from services.llm_adapter import LLMAdapter
from services.router import Router
from services.skill_manager import SkillManager

logger = logging.getLogger(__name__)


class EnvyAssistant:
    """Main orchestrator for Envy AI Assistant"""
    
    def __init__(self, config_path='./config/envy.yaml'):
        self.config_path = config_path
        self.config = self._load_config()
        self.running = False
        
        # Initialize logging
        self._setup_logging()
        
        # Initialize services
        self.wake_listener = None
        self.stt_service = None
        self.tts_service = None
        self.llm_adapter = None
        self.skill_manager = None
        self.router = None
        
        logger.info("Envy Assistant initialized")
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get('general', {}).get('log_level', 'INFO')
        log_file = self.config.get('monitoring', {}).get('log_file', './artifacts/logs/envy.log')
        
        # Create logs directory
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def initialize(self):
        """Initialize all services"""
        logger.info("Initializing Envy services...")
        
        try:
            # Initialize LLM Adapter
            logger.info("Loading LLM adapter...")
            self.llm_adapter = LLMAdapter(self.config)
            self.llm_adapter.load_model()
            
            # Initialize Skill Manager
            logger.info("Loading skill manager...")
            self.skill_manager = SkillManager(self.config)
            self.skill_manager.load_skills()
            
            # Initialize Router
            logger.info("Initializing router...")
            self.router = Router(self.config, self.llm_adapter, self.skill_manager)
            
            # Initialize TTS Service
            logger.info("Initializing TTS service...")
            self.tts_service = TTSService(self.config)
            self.tts_service.initialize()
            
            # Initialize STT Service
            logger.info("Initializing STT service...")
            self.stt_service = STTService(self.config)
            self.stt_service.load_model()
            
            # Initialize Wake Listener
            logger.info("Initializing wake listener...")
            self.wake_listener = WakeListener(self.config)
            
            logger.info("All services initialized successfully!")
            return True
        
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def start(self):
        """Start the assistant"""
        if not self.initialize():
            logger.error("Failed to initialize services")
            return False
        
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("=" * 60)
        logger.info("🎤 Envy AI Assistant is now active!")
        logger.info("=" * 60)
        logger.info("Say 'Envy' to activate the assistant")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        # Start wake word listener
        try:
            self.wake_listener.start(on_wake_callback=self._on_wake_word)
        except KeyboardInterrupt:
            self.stop()
        
        return True
    
    def _on_wake_word(self):
        """Callback when wake word is detected"""
        logger.info("🎤 Wake word detected! Listening for command...")
        
        # Acknowledge with beep or sound (optional)
        # self.tts_service.speak("Yes?")
        
        # Record user command
        try:
            command_text = self.stt_service.record_and_transcribe(duration=5)
            logger.info(f"User said: {command_text}")
            
            # Process command
            self._process_command(command_text)
        
        except Exception as e:
            logger.error(f"Error processing wake word: {e}")
    
    def _process_command(self, command_text: str):
        """Process user command"""
        try:
            # Route command to appropriate skill
            result = self.router.route(command_text)
            
            logger.info(f"Command result: {result}")
            
            # Get response text
            response = result.get('response', 'I completed that task.')
            
            # Speak response
            logger.info(f"Response: {response}")
            self.tts_service.speak(response)
        
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            self.tts_service.speak("Sorry, I encountered an error processing that request.")
    
    def process_text_command(self, text: str) -> dict:
        """Process a text command (for API/web interface)"""
        try:
            result = self.router.route(text)
            return result
        except Exception as e:
            logger.error(f"Error processing text command: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': 'Error processing command'
            }
    
    def stop(self):
        """Stop the assistant"""
        logger.info("Stopping Envy Assistant...")
        self.running = False
        
        if self.wake_listener:
            self.wake_listener.stop()
        
        logger.info("Envy Assistant stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Envy AI Personal Assistant')
    parser.add_argument('--config', default='./config/envy.yaml', help='Path to config file')
    parser.add_argument('--profile', choices=['low', 'balanced', 'power'], help='Resource profile')
    parser.add_argument('--no-gui', action='store_true', help='Run without GUI (headless)')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    
    args = parser.parse_args()
    
    # Change working directory to script location
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Load config
    if not os.path.exists(args.config):
        print(f"Config file not found: {args.config}")
        sys.exit(1)
    
    # Override profile if specified
    if args.profile:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
        config['resource_profile'] = args.profile
        with open(args.config, 'w') as f:
            yaml.dump(config, f)
    
    # Create and start assistant
    assistant = EnvyAssistant(config_path=args.config)
    
    if args.test:
        # Test mode - initialize and run a simple test
        print("Running in test mode...")
        if assistant.initialize():
            print("✓ All services initialized successfully")
            
            # Test a simple command
            result = assistant.process_text_command("Create test.py that prints hello")
            print(f"Test result: {result}")
            
            return 0
        else:
            print("✗ Initialization failed")
            return 1
    else:
        # Normal mode - start listening
        assistant.start()


if __name__ == "__main__":
    sys.exit(main() or 0)
