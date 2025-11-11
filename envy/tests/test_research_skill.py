#!/usr/bin/env python3
"""
Test Research Skill
Validates research capability (acceptance test requirement)
"""

import os
import sys
import logging
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from skills.research_skill import ResearchSkill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_research_skill():
    """Test research skill"""
    logger.info("=" * 60)
    logger.info("TEST: ResearchSkill - Research Topic")
    logger.info("=" * 60)
    
    # Setup output directory
    output_dir = './artifacts/research'
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    config = {
        'skills': {
            'research_skill': {
                'output_dir': output_dir,
                'max_sources': 5
            }
        }
    }
    
    try:
        # Initialize research skill
        skill = ResearchSkill(config)
        logger.info("✓ ResearchSkill initialized")
        
        # Test research (ACCEPTANCE TEST)
        logger.info("Testing: 'Envy, research Python programming'")
        result = skill.execute("Research Python programming language")
        
        logger.info(f"Result: {result}")
        logger.info(f"Summary: {result.get('summary', '')}")
        
        # Verify output file was created
        output_file = result.get('output_file', '')
        if output_file and os.path.exists(output_file):
            logger.info(f"✓ Research file created: {output_file}")
            
            # Read and verify content
            with open(output_file, 'r') as f:
                content = f.read()
            
            logger.info(f"Research file preview:\n{content[:500]}...")
            
            # Check for expected content
            if 'Python' in content:
                logger.info("✓ Research file contains expected content")
                logger.info("=" * 60)
                logger.info("✓ ACCEPTANCE TEST PASSED: ResearchSkill End-to-End")
                logger.info("=" * 60)
                return True
            else:
                logger.error("✗ Research content incorrect")
                return False
        else:
            logger.error(f"✗ Research file not created")
            return False
    
    except Exception as e:
        logger.error(f"✗ ResearchSkill test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_research_skill()
    sys.exit(0 if success else 1)
