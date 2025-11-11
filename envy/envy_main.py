#!/usr/bin/env python3
"""
Envy Personal Assistant - Main Entry Point
"""
import logging
import argparse
import sys
import signal
import time
from pathlib import Path

from services.config_loader import get_config
from services.wake_listener import WakeListener
from services.router import Router


class EnvyAssistant:
    """Main Envy Assistant class"""
    
    def __init__(self, profile: str = None, no_gui: bool = False):
        self.profile = profile
        self.no_gui = no_gui
        self.config = get_config()
        
        # Override profile if specified
        if profile:
            self.config.set('profile', profile)
        
        # Setup logging
        self._setup_logging()
        
        self.logger = logging.getLogger("EnvyAssistant")
        self.logger.info(f"Initializing Envy Assistant (profile: {self.config.get_profile()})")
        
        # Components
        self.router = None
        self.wake_listener = None
        self.running = False
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get('logging.level', 'INFO')
        log_dir = Path(__file__).parent / self.config.get('logging.dir', 'logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / 'envy.log'
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Start Envy assistant"""
        self.logger.info("Starting Envy Assistant...")
        
        try:
            # Initialize router
            self.router = Router()
            
            # Greet user
            greeting = self.config.get('persona.voice_greeting', 'Envy online.')
            self.router.tts.speak(greeting)
            
            # Initialize wake listener
            self.wake_listener = WakeListener(on_wake=self._on_wake)
            
            # Start listening
            self.wake_listener.start()
            
            self.running = True
            self.logger.info("Envy Assistant started successfully")
            
            # Keep running
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            self.stop()
        except Exception as e:
            self.logger.error(f"Failed to start: {e}", exc_info=True)
            self.stop()
            raise
    
    def stop(self):
        """Stop Envy assistant"""
        if not self.running:
            return
        
        self.logger.info("Stopping Envy Assistant...")
        self.running = False
        
        # Stop wake listener
        if self.wake_listener:
            self.wake_listener.stop()
        
        # Stop TTS
        if self.router and self.router.tts:
            self.router.tts.stop()
        
        self.logger.info("Envy Assistant stopped")
    
    def _on_wake(self):
        """Callback when wake word detected"""
        if self.router:
            self.router.handle_wake()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Envy Personal Assistant')
    parser.add_argument('--profile', choices=['low', 'balanced', 'power'],
                       help='Resource profile to use')
    parser.add_argument('--no-gui', action='store_true',
                       help='Run without GUI (headless mode)')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode')
    
    args = parser.parse_args()
    
    if args.test:
        # Test mode: run quick tests
        print("Running Envy in test mode...")
        from tests.run_tests import run_all_tests
        success = run_all_tests()
        sys.exit(0 if success else 1)
    
    # Normal mode: start assistant
    assistant = EnvyAssistant(profile=args.profile, no_gui=args.no_gui)
    assistant.start()


if __name__ == "__main__":
    main()
