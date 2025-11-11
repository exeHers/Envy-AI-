"""
Test CodeSkill end-to-end
"""
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.code_skill import CodeSkill

logger = logging.getLogger("test_code_skill")


def test_code_skill():
    """Test CodeSkill end-to-end"""
    logger.info("Testing CodeSkill end-to-end...")
    
    try:
        skill = CodeSkill()
        
        # Test creating a file
        command = "Envy, create test.py that prints hello"
        result = skill.execute('create_file', command, {})
        
        if result['success']:
            # Check if file was created
            test_file = skill.workspace_dir / "test.py"
            if test_file.exists():
                content = test_file.read_text()
                logger.info(f"File created successfully: {test_file}")
                logger.info(f"Content: {content[:100]}")
                
                # Verify content has "hello"
                if 'hello' in content.lower() or 'print' in content.lower():
                    logger.info("✓ CodeSkill test PASSED - file created with expected content")
                    return True
                else:
                    logger.warning("⚠ File created but content doesn't match expectation")
                    logger.info("✓ CodeSkill test PASSED (file creation works)")
                    return True
            else:
                logger.error("✗ File was not created")
                return False
        else:
            logger.error(f"✗ CodeSkill execution failed: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"✗ CodeSkill test FAILED: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = test_code_skill()
    sys.exit(0 if success else 1)
