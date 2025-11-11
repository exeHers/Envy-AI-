"""ReminderSkill - Set and manage reminders."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from services.core_skills import ReminderSkill as CoreReminderSkill

class ReminderSkill(CoreReminderSkill):
    """ReminderSkill for Envy assistant."""
    pass
