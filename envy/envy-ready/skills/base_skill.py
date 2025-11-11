#!/usr/bin/env python3
"""
Base Skill Class
All skills should inherit from this class.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BaseSkill(ABC):
    """Base class for all skills."""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"skill.{self.name}")
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill with given parameters."""
        pass
    
    def requires_confirmation(self, params: Dict[str, Any]) -> bool:
        """Check if this skill execution requires confirmation."""
        return False
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate parameters before execution."""
        return True
