#!/usr/bin/env python3
"""
System Control Skill - Executes safe system commands
Sandboxed execution with whitelist for security
"""

import os
import logging
import subprocess
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class SysControlSkill:
    """Skill for executing system commands safely"""
    
    def __init__(self, config):
        self.config = config
        skill_config = config.get('skills', {}).get('sys_control_skill', {})
        self.whitelist_mode = skill_config.get('whitelist_mode', True)
        self.allowed_commands = skill_config.get('allowed_commands', [
            'echo', 'date', 'uptime', 'whoami'
        ])
        
        logger.info(f"SysControlSkill initialized, whitelist mode: {self.whitelist_mode}")
    
    def execute(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute system command"""
        
        # Extract command
        command = self._extract_command(input_text)
        
        if not command:
            return {
                'success': False,
                'error': 'Could not extract command',
                'response': "I couldn't understand what command you want to run."
            }
        
        # Validate command
        if not self._is_allowed(command):
            logger.warning(f"Command not allowed: {command}")
            return {
                'success': False,
                'error': 'Command not allowed',
                'response': f"Sorry, the command '{command[0]}' is not in the whitelist for security reasons."
            }
        
        # Execute command
        return self._execute_command(command)
    
    def _extract_command(self, input_text: str) -> Optional[List[str]]:
        """Extract command from input text"""
        text_lower = input_text.lower()
        
        # Remove command prefixes
        for prefix in ['run', 'execute', 'command', 'system']:
            text_lower = text_lower.replace(prefix, '')
        
        # Clean up
        command_str = text_lower.strip()
        
        if not command_str:
            return None
        
        # Split into command and args
        parts = command_str.split()
        
        if len(parts) > 0:
            return parts
        
        return None
    
    def _is_allowed(self, command: List[str]) -> bool:
        """Check if command is allowed"""
        if not self.whitelist_mode:
            # In non-whitelist mode, block dangerous commands
            dangerous = ['rm', 'dd', 'mkfs', 'format', 'del', 'shutdown', 'reboot']
            return command[0] not in dangerous
        
        # Whitelist mode - only allow specific commands
        return command[0] in self.allowed_commands
    
    def _execute_command(self, command: List[str]) -> Dict[str, Any]:
        """Execute the command safely"""
        try:
            logger.info(f"Executing command: {' '.join(command)}")
            
            # Execute with timeout
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            if result.returncode == 0:
                logger.info(f"Command succeeded: {output[:100]}")
                return {
                    'success': True,
                    'action': 'command_executed',
                    'command': ' '.join(command),
                    'output': output,
                    'response': f"Command executed successfully. Output: {output}"
                }
            else:
                logger.warning(f"Command failed: {error}")
                return {
                    'success': False,
                    'error': error,
                    'command': ' '.join(command),
                    'response': f"Command failed: {error}"
                }
        
        except subprocess.TimeoutExpired:
            logger.error("Command timed out")
            return {
                'success': False,
                'error': 'Command timed out',
                'response': "The command took too long to execute and was cancelled."
            }
        
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"Error executing command: {str(e)}"
            }
    
    def is_destructive(self, input_text: str) -> bool:
        """Check if command is destructive"""
        text_lower = input_text.lower()
        
        # Destructive keywords
        destructive_keywords = [
            'delete', 'remove', 'rm', 'format', 'erase',
            'shutdown', 'reboot', 'restart', 'kill'
        ]
        
        return any(keyword in text_lower for keyword in destructive_keywords)
    
    def preview_action(self, input_text: str) -> str:
        """Preview the action"""
        command = self._extract_command(input_text)
        if command:
            return f"Execute command: {' '.join(command)}"
        return "Execute system command"


def main():
    """Standalone test"""
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'skills': {
            'sys_control_skill': {
                'whitelist_mode': True,
                'allowed_commands': ['echo', 'date', 'uptime', 'whoami']
            }
        }
    }
    
    skill = SysControlSkill(config)
    
    # Test command execution
    result = skill.execute("run echo hello")
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
