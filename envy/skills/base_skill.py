"""
Base class for all skills
"""
import logging
from typing import Dict, Any
from abc import ABC, abstractmethod

from services.config_loader import get_config


class BaseSkill(ABC):
    """Base skill class"""
    
    def __init__(self, name: str):
        self.name = name
        self.config = get_config()
        self.logger = logging.getLogger(self.name)
        self.description = "Base skill"
        self.actions = []
    
    @abstractmethod
    def execute(self, action: str, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skill action"""
        pass
    
    def success_response(self, message: str, data: Any = None) -> Dict[str, Any]:
        """Create success response"""
        result = {
            'success': True,
            'response': message
        }
        if data is not None:
            result['data'] = data
        return result
    
    def error_response(self, error: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'success': False,
            'error': error
        }
