"""
System Control Skill - Executes system commands (DISABLED by default)
MIT License
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent))
from __init__ import BaseSkill

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.config_manager import get_config

logger = logging.getLogger(__name__)


class SysControlSkill(BaseSkill):
    """Skill for executing system commands (sandboxed)"""
    
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.enabled = self.config.get('skills.syscontrol.enabled', False)
        self.whitelist = self.config.get('skills.syscontrol.whitelist', [])
        self.blacklist = self.config.get('skills.syscontrol.blacklist', [])
        self.require_confirmation = self.config.get('skills.syscontrol.require_confirmation', True)
        
        logger.info(f"SysControlSkill initialized (enabled: {self.enabled})")
    
    def execute(self, command: str) -> str:
        """Execute system command"""
        try:
            if not self.enabled:
                return "System control is disabled for safety. Enable in config if needed."
            
            # Extract actual command
            sys_command = self.extract_command(command)
            
            if not sys_command:
                return "Could not extract system command."
            
            # Validate command
            if not self.is_safe_command(sys_command):
                return f"Command '{sys_command}' is not allowed for safety reasons."
            
            logger.info(f"Executing system command: {sys_command}")
            
            # Execute command with timeout
            result = subprocess.run(
                sys_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout.strip()
            if result.returncode != 0:
                error = result.stderr.strip()
                logger.warning(f"Command failed: {error}")
                return f"Command failed: {error}"
            
            logger.info(f"Command output: {output[:100]}")
            
            return f"Command executed. Output: {output}"
            
        except subprocess.TimeoutExpired:
            return "Command timed out."
        except Exception as e:
            logger.error(f"SysControlSkill execution failed: {e}")
            return f"System command failed: {str(e)}"
    
    def extract_command(self, command: str) -> Optional[str]:
        """Extract system command from voice command"""
        command_lower = command.lower()
        
        # Pattern: "run ls"
        if 'run ' in command_lower:
            return command.split('run ', 1)[1].strip()
        
        # Pattern: "execute pwd"
        if 'execute ' in command_lower:
            return command.split('execute ', 1)[1].strip()
        
        # Pattern: "system uptime"
        if 'system ' in command_lower:
            return command.split('system ', 1)[1].strip()
        
        return None
    
    def is_safe_command(self, command: str) -> bool:
        """Check if command is safe to execute"""
        # Check blacklist first
        for blocked in self.blacklist:
            if blocked in command.lower():
                logger.warning(f"Blocked command contains: {blocked}")
                return False
        
        # If whitelist is empty, allow any non-blacklisted command
        if not self.whitelist:
            return True
        
        # Check whitelist
        for allowed in self.whitelist:
            if command.startswith(allowed):
                return True
        
        logger.warning(f"Command not in whitelist: {command}")
        return False
    
    def requires_confirmation(self) -> bool:
        return self.require_confirmation
    
    def get_description(self) -> str:
        return "Executes system commands (disabled by default for security)"
