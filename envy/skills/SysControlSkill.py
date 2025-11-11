#!/usr/bin/env python3
"""
SysControlSkill - Safe system control with confirmations.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent))
from base_skill import BaseSkill

logger = logging.getLogger(__name__)


class SysControlSkill(BaseSkill):
    """Skill for system control operations."""
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system command."""
        text = params.get('text', '')
        command = params.get('command', '')
        
        if not command:
            # Try to extract command from text
            import re
            cmd_match = re.search(r'(open|launch|run)\s+(.+)', text, re.IGNORECASE)
            if cmd_match:
                command = cmd_match.group(2)
            else:
                return {
                    'success': False,
                    'error': 'No command specified'
                }
        
        # Check if command is allowed (sandbox check should happen in manager)
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            self.logger.info(f"Executed command: {command}")
            
            return {
                'success': result.returncode == 0,
                'command': command,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'message': f'Executed: {command}'
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out'
            }
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def requires_confirmation(self, params: Dict[str, Any]) -> bool:
        """Always require confirmation for system commands."""
        return True
