"""SysControlSkill - System control commands."""
import logging
import subprocess
from typing import Dict, Any
from .base_skill import BaseSkill


logger = logging.getLogger(__name__)


class SysControlSkill(BaseSkill):
    """Skill for system control commands (requires confirmation)."""
    
    def execute(self, command: str) -> Dict[str, Any]:
        """Execute system control command."""
        logger.info(f"SysControlSkill executing: {command}")
        
        # Check if sandboxed
        if self.is_sandboxed():
            allowed_commands = self.config.get("skills.sandbox.allowed_commands", [])
            if not allowed_commands:
                return {
                    "success": False,
                    "response": "System commands are disabled for security. Enable them in config/envy.yaml",
                    "data": {}
                }
        
        # Extract command
        cmd_match = command.lower()
        
        # For demo, we'll only allow safe commands
        safe_commands = ["echo", "date", "whoami", "pwd"]
        
        # Check if command is safe
        is_safe = any(cmd in cmd_match for cmd in safe_commands)
        
        if not is_safe:
            return {
                "success": False,
                "response": "This system command requires explicit confirmation and is not in the safe list.",
                "data": {
                    "requires_confirmation": True
                }
            }
        
        try:
            # Execute safe command
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout + result.stderr
            
            return {
                "success": True,
                "response": f"Command executed. Output: {output[:100]}",
                "data": {
                    "command": command,
                    "output": output,
                    "return_code": result.returncode
                }
            }
        except Exception as e:
            logger.error(f"System command failed: {e}")
            return {
                "success": False,
                "response": f"I encountered an error executing the command: {str(e)}",
                "data": {}
            }
