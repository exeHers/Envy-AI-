#!/usr/bin/env python3
"""
Test LLM Adapter
Validates local and fallback LLM functionality
"""

import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.llm_adapter import LLMAdapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_llm_adapter():
    """Test LLM adapter"""
    logger.info("=" * 60)
    logger.info("TEST: LLM Adapter")
    logger.info("=" * 60)
    
    config = {
        'llm': {
            'primary_backend': 'local',
            'local': {
                'enabled': True,
                'engine': 'llama-cpp',
                'model_path': './models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf',
                'context_length': 2048,
                'max_tokens': 256,
                'temperature': 0.7,
                'gpu_layers': 0
            },
            'remote': {
                'enabled': False
            }
        },
        'resource_profile': 'balanced',
        'profiles': {
            'balanced': {'use_gpu': False}
        },
        'general': {'models_dir': './models'}
    }
    
    try:
        # Initialize LLM adapter
        llm = LLMAdapter(config)
        
        logger.info("Loading LLM model...")
        llm.load_model()
        
        # Test intent classification (always works)
        logger.info("Testing intent classification...")
        intent = llm.classify_intent("Create a Python file that prints hello")
        logger.info(f"Intent: {intent['intent']} (confidence: {intent['confidence']})")
        logger.info("✓ Intent classification working")
        
        # Test generation (may fallback)
        logger.info("Testing text generation...")
        prompt = "What is 2+2?"
        response = llm.generate(prompt)
        
        logger.info(f"Prompt: {prompt}")
        logger.info(f"Response: {response[:200]}...")
        logger.info("✓ LLM generation completed")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ LLM test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_llm_adapter()
    sys.exit(0 if success else 1)
