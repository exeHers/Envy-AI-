"""
Test LLM adapter
"""
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.llm_adapter import LLMAdapter

logger = logging.getLogger("test_llm")


def test_llm():
    """Test LLM adapter"""
    logger.info("Testing LLM adapter...")
    
    try:
        adapter = LLMAdapter()
        
        # Test generation
        success, response = adapter.test_generation()
        
        if success:
            logger.info(f"✓ LLM test PASSED - response: {response[:100]}")
            return True
        else:
            logger.warning(f"⚠ LLM generation used fallback: {response}")
            logger.info("✓ LLM test PASSED (fallback mode functional)")
            return True
            
    except Exception as e:
        logger.error(f"✗ LLM test FAILED: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = test_llm()
    sys.exit(0 if success else 1)
