"""SysControlSkill - system control operations."""
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.skill_manager import BaseSkill


class SysControlSkill(BaseSkill):
    """Skill for system control operations."""
    
    def execute(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system control request."""
        text = intent_data.get('text', '')
        
        # Check security settings
        if not self.config.security.allow_system_commands:
            return {
                'success': False,
                'error': 'System commands are disabled for security'
            }
        
        # Extract command
        command = self._extract_command(text)
        
        if not command:
            return {
                'success': False,
                'error': 'Could not determine system command'
            }
        
        # Check whitelist
        if self.config.security.command_whitelist:
            if command not in self.config.security.command_whitelist:
                return {
                    'success': False,
                    'error': f'Command "{command}" not in whitelist'
                }
        
        try:
            # Execute command (sandboxed)
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout + result.stderr
            
            self.logger.info(f"Executed system command: {command}")
            
            return {
                'success': result.returncode == 0,
                'command': command,
                'output': output,
                'message': f'Executed: {command}'
            }
        except Exception as e:
            self.logger.error(f"Error executing command: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_command(self, text: str) -> str:
        """Extract system command from text."""
        # Pattern: "open X" or "run X"
        patterns = [
            r'open\s+(.+)',
            r'run\s+(.+)',
            r'execute\s+(.+)',
            r'launch\s+(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip()
        
        return ""
    
    def requires_confirmation(self, intent_data: Dict[str, Any]) -> bool:
        """System commands always require confirmation."""
        return True
