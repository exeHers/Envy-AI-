#!/usr/bin/env python3
"""
Test Code Skill
Validates file creation capability (acceptance test requirement)
"""

import os
import sys
import logging
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from skills.code_skill import CodeSkill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_code_skill():
    """Test code skill - create test.py"""
    logger.info("=" * 60)
    logger.info("TEST: CodeSkill - Create test.py")
    logger.info("=" * 60)
    
    # Setup workspace
    workspace_dir = './workspace'
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)
    os.makedirs(workspace_dir)
    
    config = {
        'skills': {
            'code_skill': {
                'workspace_dir': workspace_dir,
                'allowed_extensions': ['.py', '.js', '.txt', '.md']
            }
        }
    }
    
    try:
        # Initialize code skill
        skill = CodeSkill(config)
        logger.info("✓ CodeSkill initialized")
        
        # Test file creation (ACCEPTANCE TEST)
        logger.info("Testing: 'Envy, create test.py that prints hello'")
        result = skill.execute("Create test.py that prints hello")
        
        logger.info(f"Result: {result}")
        
        # Verify file was created
        test_file = os.path.join(workspace_dir, 'test.py')
        if os.path.exists(test_file):
            logger.info(f"✓ File created: {test_file}")
            
            # Read and verify content
            with open(test_file, 'r') as f:
                content = f.read()
            
            logger.info(f"File content:\n{content}")
            
            # Check for expected content
            if 'hello' in content.lower():
                logger.info("✓ File contains expected content")
                logger.info("=" * 60)
                logger.info("✓ ACCEPTANCE TEST PASSED: CodeSkill End-to-End")
                logger.info("=" * 60)
                return True
            else:
                logger.error("✗ File content incorrect")
                return False
        else:
            logger.error(f"✗ File not created: {test_file}")
            return False
    
    except Exception as e:
        logger.error(f"✗ CodeSkill test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_code_skill()
    sys.exit(0 if success else 1)
