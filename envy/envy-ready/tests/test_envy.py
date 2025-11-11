#!/usr/bin/env python3
"""
Automated Test Suite for Envy
"""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('artifacts/tests/test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EnvyTester:
    """Test suite for Envy."""
    
    def __init__(self):
        self.envy_dir = Path(__file__).parent.parent
        self.artifacts_dir = self.envy_dir / 'artifacts' / 'tests'
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def run_all_tests(self):
        """Run all tests."""
        logger.info("=" * 60)
        logger.info("Envy Test Suite")
        logger.info("=" * 60)
        
        tests = [
            ("Wake Word Detection", self.test_wake_word),
            ("STT Pipeline", self.test_stt),
            ("TTS Pipeline", self.test_tts),
            ("CodeSkill", self.test_code_skill),
            ("ResearchSkill", self.test_research_skill),
            ("Router", self.test_router),
            ("LLM Adapter", self.test_llm_adapter),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\nRunning: {test_name}")
            try:
                result = test_func()
                if result:
                    self.passed += 1
                    logger.info(f"✓ PASSED: {test_name}")
                else:
                    self.failed += 1
                    logger.error(f"✗ FAILED: {test_name}")
                self.results.append({'test': test_name, 'passed': result})
            except Exception as e:
                self.failed += 1
                logger.error(f"✗ ERROR in {test_name}: {e}")
                self.results.append({'test': test_name, 'passed': False, 'error': str(e)})
        
        self._print_summary()
        return self.failed == 0
    
    def test_wake_word(self) -> bool:
        """Test wake word detection."""
        try:
            # Import wake listener
            sys.path.insert(0, str(self.envy_dir / 'src'))
            from wake_listener.wake_listener import WakeWordListener
            import yaml
            
            config_path = self.envy_dir / 'config' / 'envy.yaml'
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            wake_config = config.get('wake', {})
            listener = WakeWordListener(wake_config)
            
            if listener.initialize():
                logger.info("Wake listener initialized successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Wake word test failed: {e}")
            return False
    
    def test_stt(self) -> bool:
        """Test STT service."""
        try:
            sys.path.insert(0, str(self.envy_dir / 'src'))
            from stt_service.stt_service import STTService
            import yaml
            
            config_path = self.envy_dir / 'config' / 'envy.yaml'
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            stt_config = config.get('stt', {})
            # Use VOSK for testing (lighter)
            stt_config['engine'] = 'vosk'
            service = STTService(stt_config)
            
            if service.initialize():
                logger.info("STT service initialized successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"STT test failed: {e}")
            return False
    
    def test_tts(self) -> bool:
        """Test TTS service."""
        try:
            sys.path.insert(0, str(self.envy_dir / 'src'))
            from tts_service.tts_service import TTSService
            import yaml
            
            config_path = self.envy_dir / 'config' / 'envy.yaml'
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            tts_config = config.get('tts', {})
            service = TTSService(tts_config)
            
            if service.initialize():
                # Test synthesis
                output_path = self.artifacts_dir / 'test_tts_output.wav'
                result = service.speak("Test message from Envy", save_path=output_path)
                if result or output_path.exists():
                    logger.info("TTS service working")
                    return True
            return False
        except Exception as e:
            logger.error(f"TTS test failed: {e}")
            return False
    
    def test_code_skill(self) -> bool:
        """Test CodeSkill end-to-end."""
        try:
            sys.path.insert(0, str(self.envy_dir))
            sys.path.insert(0, str(self.envy_dir / 'src'))
            
            from skills.CodeSkill import CodeSkill
            
            skill = CodeSkill()
            params = {
                'text': 'create test.py that prints hello',
                'filename': 'test.py',
                'content': 'print("hello")'
            }
            
            result = skill.execute(params)
            
            if result.get('success'):
                # Check if file was created
                test_file = self.envy_dir / 'test.py'
                if test_file.exists():
                    content = test_file.read_text()
                    if 'hello' in content.lower():
                        logger.info("CodeSkill created file successfully")
                        # Cleanup
                        test_file.unlink()
                        return True
            return False
        except Exception as e:
            logger.error(f"CodeSkill test failed: {e}")
            return False
    
    def test_research_skill(self) -> bool:
        """Test ResearchSkill."""
        try:
            sys.path.insert(0, str(self.envy_dir))
            sys.path.insert(0, str(self.envy_dir / 'src'))
            
            from skills.ResearchSkill import ResearchSkill
            
            skill = ResearchSkill()
            params = {
                'text': 'research artificial intelligence',
                'topic': 'artificial intelligence'
            }
            
            result = skill.execute(params)
            
            if result.get('success'):
                output_file = Path(result.get('output_file', ''))
                if output_file.exists():
                    logger.info("ResearchSkill generated summary")
                    return True
            return False
        except Exception as e:
            logger.error(f"ResearchSkill test failed: {e}")
            return False
    
    def test_router(self) -> bool:
        """Test router."""
        try:
            sys.path.insert(0, str(self.envy_dir / 'src'))
            from router.router import Router
            from llm_adapter.llm_adapter import LLMAdapter
            import yaml
            
            config_path = self.envy_dir / 'config' / 'envy.yaml'
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            router_config = config.get('router', {})
            llm_config = config.get('llm', {})
            
            llm_adapter = LLMAdapter(llm_config)
            llm_adapter.initialize()
            
            router = Router(router_config, llm_adapter)
            
            test_text = "Envy, create test.py that prints hello"
            skill, params = router.route(test_text)
            
            if skill == 'CodeSkill':
                logger.info("Router correctly identified CodeSkill")
                return True
            return False
        except Exception as e:
            logger.error(f"Router test failed: {e}")
            return False
    
    def test_llm_adapter(self) -> bool:
        """Test LLM adapter."""
        try:
            sys.path.insert(0, str(self.envy_dir / 'src'))
            from llm_adapter.llm_adapter import LLMAdapter
            import yaml
            
            config_path = self.envy_dir / 'config' / 'envy.yaml'
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            llm_config = config.get('llm', {})
            adapter = LLMAdapter(llm_config)
            
            if adapter.initialize():
                response = adapter.generate("Hello, what can you do?")
                if response:
                    logger.info(f"LLM adapter responded: {response[:50]}...")
                    return True
            return False
        except Exception as e:
            logger.error(f"LLM adapter test failed: {e}")
            return False
    
    def _print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 60)
        logger.info("Test Summary")
        logger.info("=" * 60)
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")
        logger.info(f"Total: {self.passed + self.failed}")
        
        # Save results
        results_file = self.artifacts_dir / 'test_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\nResults saved to: {results_file}")


def main():
    """Main entry point."""
    tester = EnvyTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
