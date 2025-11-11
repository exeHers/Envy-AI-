"""ResearchSkill - Research topics and generate summaries."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from services.core_skills import ResearchSkill as CoreResearchSkill

class ResearchSkill(CoreResearchSkill):
    """ResearchSkill for Envy assistant."""
    pass
