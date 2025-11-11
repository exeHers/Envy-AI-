"""Base skill class for Envy."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any


logger = logging.getLogger(__name__)


class BaseSkill(ABC):
    """Base class for all Envy skills."""
    
    def __init__(self, config):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def execute(self, command: str) -> Dict[str, Any]:
        """Execute the skill with the given command."""
        pass
    
    def requires_confirmation(self) -> bool:
        """Check if this skill requires confirmation."""
        return self.name in self.config.get("skills.require_confirmation", [])
    
    def is_sandboxed(self) -> bool:
        """Check if this skill runs in sandbox."""
        return self.config.get("skills.sandbox.enabled", True)
