"""
Envy Skills - Plugin System
MIT License
"""

class BaseSkill:
    """Base class for all skills"""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    def execute(self, command: str) -> str:
        """
        Execute the skill with the given command
        Returns response text
        """
        raise NotImplementedError("Skill must implement execute()")
    
    def requires_confirmation(self) -> bool:
        """Whether this skill requires user confirmation"""
        return False
    
    def get_description(self) -> str:
        """Get skill description"""
        return "No description available"
