"""CodeSkill - Create and edit code files."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from services.core_skills import CodeSkill as CoreCodeSkill

class CodeSkill(CoreCodeSkill):
    """CodeSkill for Envy assistant."""
    pass
