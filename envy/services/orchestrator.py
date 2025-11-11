"""Main Envy orchestrator - coordinates all services."""
import logging
import threading
import time
import sys
import os
from typing import Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.config_loader import EnvyConfig
from services.utils import setup_logging, check_resources
from services.wake_listener import WakeWordListener
from services.stt_service import STTService
from services.tts_service import TTSService
from services.llm_adapter import LLMAdapter
from services.router import Router
from services.skill_manager import SkillManager
from skills.generalskill import GeneralSkill


class EnvyOrchestrator:
    """Main orchestrator for Envy personal assistant."""
    
    def __init__(self, config_path: str = "config/envy.yaml"):
        self.config = EnvyConfig.load_from_file(config_path)
        self.logger = setup_logging(self.config)
        
        # Initialize services
        self.wake_listener = None
        self.stt_service = None
        self.tts_service = None
        self.llm_adapter = None
        self.router = None
        self.skill_manager = None
        
        self.is_running = False
        self.current_transcript = ""
        
    def initialize(self):
        """Initialize all services."""
        self.logger.info("Initializing Envy...")
        
        # Initialize LLM adapter
        self.llm_adapter = LLMAdapter(self.config, self.logger)
        if not self.llm_adapter.initialize():
            self.logger.warning("LLM adapter initialization failed, continuing with limited functionality")
        
        # Initialize router
        self.router = Router(self.config, self.llm_adapter, self.logger)
        
        # Initialize skill manager
        self.skill_manager = SkillManager(self.config, self.logger)
        
        # Add GeneralSkill with LLM adapter (if not already loaded)
        if 'GeneralSkill' not in self.skill_manager.skills:
            general_skill = GeneralSkill(self.config, self.llm_adapter, self.logger)
            self.skill_manager.skills['GeneralSkill'] = general_skill
        
        # Initialize TTS
        self.tts_service = TTSService(self.config, self.logger)
        self.tts_service.initialize()
        
        # Initialize STT
        self.stt_service = STTService(self.config, self.logger)
        self.stt_service.initialize()
        
        # Initialize wake word listener
        self.wake_listener = WakeWordListener(self.config, self.logger)
        if not self.wake_listener.initialize():
            self.logger.error("Failed to initialize wake word listener")
            return False
        
        self.logger.info("Envy initialized successfully")
        return True
    
    def on_wake_word_detected(self):
        """Handle wake word detection."""
        self.logger.info("Wake word detected!")
        
        # Speak acknowledgment
        self.tts_service.speak("Yes?", async_mode=True)
        
        # Start recording
        self.current_transcript = ""
        
        def on_transcript(text: str, final: bool):
            if final:
                self.current_transcript += text + " "
            self.logger.info(f"Transcript: {text}")
        
        self.stt_service.start_recording(callback=on_transcript, duration=5.0)
        
        # Wait for recording to complete
        time.sleep(5.5)
        transcript = self.stt_service.stop_recording()
        
        if not transcript:
            transcript = self.current_transcript.strip()
        
        if transcript:
            self.process_command(transcript)
        else:
            self.logger.warning("No transcript received")
            self.tts_service.speak("I didn't catch that.", async_mode=True)
    
    def process_command(self, text: str):
        """Process user command."""
        self.logger.info(f"Processing command: {text}")
        
        # Route to appropriate skill
        route_result = self.router.route(text)
        skill_name = route_result['skill_name']
        
        # Execute skill
        result = self.skill_manager.execute_skill(skill_name, route_result)
        
        if result.get('requires_confirmation'):
            self.logger.info("Action requires confirmation")
            self.tts_service.speak("This action requires confirmation. Please confirm in the dashboard.", async_mode=True)
            return
        
        if result.get('success'):
            response = result.get('message', result.get('response', 'Done.'))
            self.logger.info(f"Skill execution successful: {response}")
        else:
            error = result.get('error', 'Unknown error')
            response = f"I encountered an error: {error}"
            self.logger.error(f"Skill execution failed: {error}")
        
        # Speak response
        self.tts_service.speak(response, async_mode=True)
    
    def start(self):
        """Start Envy assistant."""
        if not self.initialize():
            self.logger.error("Failed to initialize Envy")
            return False
        
        self.is_running = True
        
        # Start wake word listener
        self.wake_listener.start(self.on_wake_word_detected)
        
        self.logger.info("Envy is now running. Say 'Envy' to activate.")
        
        # Monitor resources
        threading.Thread(target=self._monitor_resources, daemon=True).start()
        
        return True
    
    def _monitor_resources(self):
        """Monitor resource usage."""
        while self.is_running:
            try:
                resources = check_resources(self.config)
                
                # Check limits
                if resources['cpu_percent'] > self.config.resources.max_cpu_percent:
                    self.logger.warning(f"High CPU usage: {resources['cpu_percent']}%")
                
                if resources['memory_mb'] > self.config.resources.max_memory_mb:
                    self.logger.warning(f"High memory usage: {resources['memory_mb']}MB")
                
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                time.sleep(30)
    
    def stop(self):
        """Stop Envy assistant."""
        self.is_running = False
        
        if self.wake_listener:
            self.wake_listener.stop()
        
        if self.stt_service:
            self.stt_service.stop_recording()
        
        if self.tts_service:
            self.tts_service.stop()
        
        self.logger.info("Envy stopped")
