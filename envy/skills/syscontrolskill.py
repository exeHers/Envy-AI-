"""SysControlSkill - System control commands."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from services.core_skills import SysControlSkill as CoreSysControlSkill

class SysControlSkill(CoreSysControlSkill):
    """SysControlSkill for Envy assistant."""
    pass
