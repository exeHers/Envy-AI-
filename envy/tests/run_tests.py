#!/usr/bin/env python3
"""
Run all Envy tests and generate reports
"""
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
log_file = Path(__file__).parent.parent / "artifacts" / "tests" / "test-run.log"
log_file.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("TestRunner")


def run_all_tests():
    """Run all acceptance tests"""
    logger.info("="*60)
    logger.info("ENVY ACCEPTANCE TESTS")
    logger.info("="*60)
    logger.info(f"Started at: {datetime.now()}")
    logger.info("")
    
    results = {}
    
    # Test 1: Wake Word Detection
    logger.info("TEST 1: Wake Word Detection")
    try:
        from tests.test_wake_word import test_wake_word
        results['wake_word'] = test_wake_word()
    except Exception as e:
        logger.error(f"Wake word test failed: {e}")
        results['wake_word'] = False
    
    # Test 2: STT Service
    logger.info("\nTEST 2: Speech-to-Text Service")
    try:
        from tests.test_stt import test_stt
        results['stt'] = test_stt()
    except Exception as e:
        logger.error(f"STT test failed: {e}")
        results['stt'] = False
    
    # Test 3: TTS Service
    logger.info("\nTEST 3: Text-to-Speech Service")
    try:
        from tests.test_tts import test_tts
        results['tts'] = test_tts()
    except Exception as e:
        logger.error(f"TTS test failed: {e}")
        results['tts'] = False
    
    # Test 4: LLM Adapter
    logger.info("\nTEST 4: LLM Adapter")
    try:
        from tests.test_llm import test_llm
        results['llm'] = test_llm()
    except Exception as e:
        logger.error(f"LLM test failed: {e}")
        results['llm'] = False
    
    # Test 5: CodeSkill
    logger.info("\nTEST 5: CodeSkill End-to-End")
    try:
        from tests.test_code_skill import test_code_skill
        results['code_skill'] = test_code_skill()
    except Exception as e:
        logger.error(f"CodeSkill test failed: {e}")
        results['code_skill'] = False
    
    # Test 6: ResearchSkill
    logger.info("\nTEST 6: ResearchSkill End-to-End")
    try:
        from tests.test_research_skill import test_research_skill
        results['research_skill'] = test_research_skill()
    except Exception as e:
        logger.error(f"ResearchSkill test failed: {e}")
        results['research_skill'] = False
    
    # Summary
    logger.info("")
    logger.info("="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{test_name:20s} : {status}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    logger.info("")
    logger.info(f"Total: {passed}/{total} tests passed")
    logger.info(f"Completed at: {datetime.now()}")
    logger.info("="*60)
    
    # Save results
    results_file = Path(__file__).parent.parent / "artifacts" / "tests" / "test-results.txt"
    with open(results_file, 'w') as f:
        f.write(f"Envy Test Results - {datetime.now()}\n")
        f.write("="*60 + "\n\n")
        for test_name, passed in results.items():
            status = "PASS" if passed else "FAIL"
            f.write(f"{test_name}: {status}\n")
        f.write(f"\nTotal: {passed}/{total} tests passed\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
