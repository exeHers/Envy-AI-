#!/usr/bin/env python3
"""
Envy Personal Assistant - Main Entry Point
MIT License
"""

import os
import sys
import logging
import argparse
import signal
import threading
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.config_manager import get_config
from services.wake_listener import WakeListener
from services.stt_service import STTService
from services.tts_service import TTSService
from services.llm_adapter import LLMAdapter
from services.skill_manager import SkillManager
from services.router import Router
from web.dashboard import start_dashboard, set_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('artifacts/logs/envy.log')
    ]
)
logger = logging.getLogger(__name__)


class EnvyAssistant:
    """Main Envy Assistant orchestrator"""
    
    def __init__(self, profile: str = 'balanced', headless: bool = False):
        self.profile = profile
        self.headless = headless
        self.running = False
        self.config = None
        
        # Services
        self.wake_listener = None
        self.skill_manager = None
        self.router = None
        self.dashboard_thread = None
        
        logger.info(f"Initializing Envy (profile: {profile}, headless: {headless})")
    
    def initialize(self):
        """Initialize all services"""
        try:
            # Load configuration
            self.config = get_config()
            self.config.set('system.profile', self.profile)
            
            logger.info("Initializing services...")
            
            # Initialize skill manager
            self.skill_manager = SkillManager()
            self.skill_manager.load_skills()
            logger.info(f"Loaded skills: {self.skill_manager.list_skills()}")
            
            # Initialize router
            self.router = Router(self.skill_manager)
            
            # Initialize wake listener
            self.wake_listener = WakeListener(on_wake_callback=self.on_wake)
            
            # Start web dashboard if not headless
            if not self.headless and self.config.get('web.enabled', True):
                self.start_dashboard()
            
            logger.info("Envy initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Envy: {e}")
            raise
    
    def start(self):
        """Start Envy assistant"""
        try:
            if self.running:
                logger.warning("Envy is already running")
                return
            
            logger.info("Starting Envy...")
            self.running = True
            
            # Start wake listener
            self.wake_listener.start()
            
            logger.info("🤖 Envy is now listening for the wake word 'Envy'...")
            
            # Keep running
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error running Envy: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop Envy assistant"""
        if not self.running:
            return
        
        logger.info("Stopping Envy...")
        self.running = False
        
        # Stop wake listener
        if self.wake_listener:
            self.wake_listener.stop()
        
        logger.info("Envy stopped")
    
    def on_wake(self):
        """Callback when wake word is detected"""
        try:
            logger.info("🎤 Wake word detected, processing command...")
            
            # Process wake event in router
            self.router.process_wake_event()
            
        except Exception as e:
            logger.error(f"Error processing wake event: {e}")
    
    def start_dashboard(self):
        """Start web dashboard in separate thread"""
        try:
            host = self.config.get('web.host', '127.0.0.1')
            port = self.config.get('web.port', 8080)
            
            # Register router with dashboard
            set_router(self.router)
            
            # Start dashboard in thread
            self.dashboard_thread = threading.Thread(
                target=start_dashboard,
                args=(host, port),
                daemon=True
            )
            self.dashboard_thread.start()
            
            logger.info(f"Web dashboard started at http://{host}:{port}")
            
        except Exception as e:
            logger.error(f"Failed to start dashboard: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Envy Personal Assistant')
    parser.add_argument('--profile', default='balanced', 
                       choices=['low', 'balanced', 'power'],
                       help='Performance profile')
    parser.add_argument('--no-gui', '--headless', action='store_true',
                       help='Run without web dashboard')
    parser.add_argument('--config', help='Path to config file')
    
    args = parser.parse_args()
    
    # Banner
    print("=" * 60)
    print("🤖 ENVY - Personal AI Assistant")
    print("=" * 60)
    print()
    
    try:
        # Create Envy instance
        envy = EnvyAssistant(profile=args.profile, headless=args.no_gui)
        
        # Initialize
        envy.initialize()
        
        # Setup signal handlers
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received")
            envy.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start
        envy.start()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
