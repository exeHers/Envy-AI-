#!/usr/bin/env python3
"""Main orchestrator for Envy Personal Assistant."""
import asyncio
import signal
import sys
import argparse
from pathlib import Path
import threading

# Add services to path
sys.path.insert(0, str(Path(__file__).parent))

from services.config_loader import get_config
from services.logger import setup_logger
from services.wake_listener import WakeListener
from services.stt_service import STTService
from services.tts_service import TTSService
from services.router import Router
from services.skill_manager import SkillManager


class EnvyOrchestrator:
    """Main orchestrator for Envy."""
    
    def __init__(self, profile: str = None, no_gui: bool = False):
        # Load config
        self.config = get_config()
        if profile:
            self.config.config['profile'] = profile
            
        self.logger = setup_logger("Envy", self.config.get("logging.file"))
        self.no_gui = no_gui
        
        # Services
        self.wake_listener = None
        self.stt = None
        self.tts = None
        self.skill_manager = None
        self.router = None
        self.dashboard_thread = None
        
        self.running = False
        self.processing = False
        
    def initialize(self):
        """Initialize all services."""
        self.logger.info("=" * 60)
        self.logger.info("Initializing Envy Personal Assistant")
        self.logger.info("=" * 60)
        
        try:
            # Initialize skill manager
            self.logger.info("Initializing skill manager...")
            self.skill_manager = SkillManager()
            self.skill_manager.initialize()
            
            # Initialize router
            self.logger.info("Initializing router...")
            self.router = Router(skill_manager=self.skill_manager)
            self.router.initialize()
            
            # Initialize STT
            self.logger.info("Initializing speech-to-text...")
            self.stt = STTService()
            self.stt.initialize()
            
            # Initialize TTS
            self.logger.info("Initializing text-to-speech...")
            self.tts = TTSService()
            self.tts.initialize()
            
            # Initialize wake listener
            self.logger.info("Initializing wake word listener...")
            self.wake_listener = WakeListener(callback=self.on_wake_word)
            
            # Start web dashboard if enabled
            if not self.no_gui and self.config.get("web.enabled", True):
                self.start_dashboard()
                
            self.logger.info("=" * 60)
            self.logger.info("Envy initialized successfully!")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}", exc_info=True)
            return False
            
    def start_dashboard(self):
        """Start web dashboard in separate thread."""
        from web.dashboard import start_dashboard
        
        self.dashboard_thread = threading.Thread(
            target=start_dashboard,
            daemon=True
        )
        self.dashboard_thread.start()
        
        host = self.config.get("web.host", "127.0.0.1")
        port = self.config.get("web.port", 8080)
        self.logger.info(f"Dashboard started at http://{host}:{port}")
        
    def on_wake_word(self):
        """Callback when wake word is detected."""
        if self.processing:
            self.logger.debug("Already processing, ignoring wake word")
            return
            
        self.processing = True
        
        try:
            self.logger.info("Wake word detected! Listening...")
            
            # Speak acknowledgment
            self.tts.speak("Yes?", blocking=True)
            
            # Record and transcribe
            text = self.stt.record_and_transcribe(duration=5.0)
            
            if text:
                self.logger.info(f"You said: {text}")
                
                # Process request
                asyncio.run(self.process_request(text))
            else:
                self.logger.warning("No speech detected")
                self.tts.speak("I didn't catch that. Please try again.", blocking=False)
                
        except Exception as e:
            self.logger.error(f"Error processing wake word: {e}", exc_info=True)
            
        finally:
            self.processing = False
            
    async def process_request(self, text: str):
        """Process user request."""
        try:
            result = await self.router.process_request(text)
            self.logger.info(f"Request processed: {result['success']}")
            
        except Exception as e:
            self.logger.error(f"Error processing request: {e}", exc_info=True)
            self.tts.speak("Sorry, I encountered an error processing that request.", blocking=False)
            
    def run(self):
        """Run Envy (blocking)."""
        if not self.initialize():
            self.logger.error("Failed to initialize Envy")
            return 1
            
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Envy is now running. Press Ctrl+C to stop.")
        
        # Start wake listener (blocking)
        try:
            self.wake_listener.start()
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Runtime error: {e}", exc_info=True)
            
        self.shutdown()
        return 0
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.wake_listener:
            self.wake_listener.stop()
            
    def shutdown(self):
        """Shutdown Envy gracefully."""
        self.logger.info("Shutting down Envy...")
        
        if self.wake_listener:
            self.wake_listener.stop()
            
        if self.tts:
            self.tts.stop()
            
        self.logger.info("Envy shut down complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Envy Personal Assistant")
    parser.add_argument('--profile', choices=['low', 'balanced', 'power'], 
                       help='Resource profile')
    parser.add_argument('--no-gui', action='store_true',
                       help='Run without web dashboard')
    parser.add_argument('--config', help='Path to config file')
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = EnvyOrchestrator(
        profile=args.profile,
        no_gui=args.no_gui
    )
    
    # Run
    exit_code = orchestrator.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
