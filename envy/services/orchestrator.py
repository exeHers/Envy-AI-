"""Main orchestrator service for Envy."""
import logging
import sys
import os
from pathlib import Path
import threading
import time
from typing import Optional

# Add services to path
sys.path.insert(0, str(Path(__file__).parent))

from services.config_loader import Config
from services.wake_listener import WakeWordListener
from services.stt_service import STTService
from services.tts_service import TTSService
from services.llm_adapter import LLMAdapter
from services.router import Router


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('artifacts/envy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EnvyOrchestrator:
    """Main orchestrator for Envy personal assistant."""
    
    def __init__(self, config_path: Optional[str] = None, profile: str = "balanced"):
        self.config = Config(config_path)
        self.config.apply_profile(profile)
        
        # Initialize services
        logger.info("Initializing Envy services...")
        self.tts_service = TTSService(self.config)
        self.stt_service = STTService(self.config)
        self.llm_adapter = LLMAdapter(self.config)
        self.router = Router(self.config, self.llm_adapter)
        self.wake_listener: Optional[WakeWordListener] = None
        
        self.running = False
        self.pending_confirmation: Optional[dict] = None
    
    def _on_wake_word_detected(self):
        """Callback when wake word is detected."""
        logger.info("Wake word detected!")
        
        # Speak wake response
        wake_response = self.config.get("persona.responses.wake", "Yes?")
        self.tts_service.speak(wake_response)
        
        # Record and transcribe
        logger.info("Recording user command...")
        text = self.stt_service.record_and_transcribe(duration=5.0)
        
        if not text:
            logger.warning("No transcription received")
            return
        
        logger.info(f"User said: {text}")
        
        # Route to skill
        result = self.router.route(text)
        
        # Handle result
        if result.get("requires_confirmation"):
            self.pending_confirmation = result
            logger.info("Action requires confirmation")
            # In full implementation, this would trigger dashboard confirmation
            # For now, we'll proceed with a warning
            self.tts_service.speak("This action requires confirmation. Proceeding anyway for demo.")
        
        # Speak response
        response = result.get("response", "Done.")
        self.tts_service.speak(response)
    
    def start(self):
        """Start Envy assistant."""
        if self.running:
            logger.warning("Envy is already running")
            return
        
        logger.info("Starting Envy personal assistant...")
        self.running = True
        
        # Initialize wake word listener
        self.wake_listener = WakeWordListener(self.config, self._on_wake_word_detected)
        
        # Start wake word listener in background
        try:
            self.wake_listener.start_async()
            logger.info("Envy is now listening for wake word 'Envy'...")
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.stop()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self.stop()
    
    def stop(self):
        """Stop Envy assistant."""
        logger.info("Stopping Envy...")
        self.running = False
        if self.wake_listener:
            self.wake_listener.stop()
        logger.info("Envy stopped")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Envy Personal Assistant")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument("--profile", type=str, default="balanced", choices=["low", "balanced", "power"],
                       help="Resource profile")
    parser.add_argument("--no-gui", action="store_true", help="Run without GUI")
    
    args = parser.parse_args()
    
    # Change to envy directory
    envy_dir = Path(__file__).parent
    os.chdir(envy_dir)
    
    # Create necessary directories
    Path("artifacts").mkdir(exist_ok=True)
    Path("workspace").mkdir(exist_ok=True)
    
    orchestrator = EnvyOrchestrator(args.config, args.profile)
    orchestrator.start()


if __name__ == "__main__":
    main()
