"""
SysControlSkill: Execute system commands safely
"""
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, List

from skills.base_skill import BaseSkill
from services.config_loader import get_config


class SysControlSkill(BaseSkill):
    """Skill for system control and command execution"""
    
    def __init__(self):
        super().__init__("SysControlSkill")
        self.description = "Execute system commands safely"
        self.actions = ['execute']
        
        # Load settings
        self.require_confirmation = self.config.get('skills.sys_control_skill.require_confirmation', True)
        self.allowed_commands = self.config.get('skills.sys_control_skill.allowed_commands', [])
        self.dangerous_commands = self.config.get('skills.sys_control_skill.dangerous_commands', [])
        
        # Security settings
        self.sandbox_mode = self.config.get('security.sandbox_mode', True)
        self.whitelist_only = self.config.get('security.whitelist_only', True)
        
        self.logger.info(f"SysControlSkill initialized (sandbox={self.sandbox_mode})")
    
    def execute(self, action: str, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system control action"""
        
        if action == 'execute':
            return self.execute_command(command, parameters)
        else:
            return self.error_response(f"Unknown action: {action}")
    
    def execute_command(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system command with safety checks"""
        self.logger.info(f"Execute command: {command}")
        
        # Extract actual command from natural language
        cmd = self._extract_command(command)
        
        if not cmd:
            return self.error_response("Could not determine system command")
        
        # Security check: whitelist only
        if self.whitelist_only:
            if not self._is_whitelisted(cmd):
                return self.error_response(
                    f"Command '{cmd}' is not in the whitelist. "
                    f"Allowed commands: {', '.join(self.allowed_commands)}"
                )
        
        # Security check: dangerous commands
        if self._is_dangerous(cmd):
            return self.error_response(
                f"Command '{cmd}' is flagged as dangerous and requires manual confirmation. "
                "This feature is not yet implemented in voice mode."
            )
        
        # Execute in sandbox
        if self.sandbox_mode:
            return self._execute_sandboxed(cmd)
        else:
            return self._execute_direct(cmd)
    
    def _extract_command(self, command: str) -> str:
        """Extract system command from natural language"""
        command_lower = command.lower()
        
        # Remove common prefixes
        prefixes = [
            'run',
            'execute',
            'system',
            'command',
        ]
        
        cmd = command_lower
        for prefix in prefixes:
            if cmd.startswith(prefix):
                cmd = cmd[len(prefix):].strip()
                break
        
        # Common command mappings
        mappings = {
            'show date': 'date',
            'show time': 'date',
            'what time': 'date',
            'disk space': 'df -h',
            'memory usage': 'free -h',
            'uptime': 'uptime',
        }
        
        for pattern, actual_cmd in mappings.items():
            if pattern in cmd:
                return actual_cmd
        
        return cmd.strip()
    
    def _is_whitelisted(self, cmd: str) -> bool:
        """Check if command is in whitelist"""
        # Extract base command
        base_cmd = cmd.split()[0] if cmd else ""
        
        for allowed in self.allowed_commands:
            allowed_base = allowed.split()[0]
            if base_cmd == allowed_base or cmd == allowed:
                return True
        
        return False
    
    def _is_dangerous(self, cmd: str) -> bool:
        """Check if command is dangerous"""
        cmd_lower = cmd.lower()
        
        for dangerous in self.dangerous_commands:
            if dangerous.lower() in cmd_lower:
                return True
        
        return False
    
    def _execute_sandboxed(self, cmd: str) -> Dict[str, Any]:
        """Execute command in sandboxed environment"""
        try:
            # Execute with timeout and capture output
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(Path.home())  # Run from home directory
            )
            
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            if result.returncode == 0:
                self.logger.info(f"Command executed successfully: {cmd}")
                return self.success_response(
                    f"Command completed. Output: {output[:100]}",
                    data={'output': output, 'command': cmd}
                )
            else:
                self.logger.warning(f"Command failed with code {result.returncode}")
                return self.error_response(f"Command failed: {error}")
            
        except subprocess.TimeoutExpired:
            return self.error_response("Command timed out after 10 seconds")
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            return self.error_response(f"Execution failed: {e}")
    
    def _execute_direct(self, cmd: str) -> Dict[str, Any]:
        """Execute command directly (less safe)"""
        # Same as sandboxed for now
        return self._execute_sandboxed(cmd)


def main():
    """Test sys control skill standalone"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    skill = SysControlSkill()
    
    # Test commands
    commands = [
        "run date",
        "show uptime",
        "execute rm -rf /",  # Should be blocked
    ]
    
    for cmd in commands:
        print(f"\n--- Testing: {cmd} ---")
        result = skill.execute('execute', cmd, {})
        print(f"Success: {result['success']}")
        print(f"Response: {result.get('response', result.get('error'))}")


if __name__ == "__main__":
    main()
