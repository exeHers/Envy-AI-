"""System control skill for executing system commands."""
import asyncio
import subprocess
from typing import Dict, Any
from pathlib import Path


class SysControlSkill:
    """Skill for controlling system operations (sandboxed)."""
    
    def __init__(self):
        # Whitelist of safe commands
        self.whitelist = [
            "ls", "pwd", "date", "echo", "whoami",
            "df", "free", "uptime", "uname"
        ]
        self.max_command_length = 200
        
    async def execute_command(self, command: str = None, **kwargs) -> Dict[str, Any]:
        """Execute a system command (sandboxed)."""
        result = {
            "success": False,
            "response": "",
            "data": {}
        }
        
        if not command:
            result["response"] = "No command specified"
            return result
            
        # Extract actual command from description
        command = self._extract_command(command)
        
        # Validate command
        if not self._is_safe_command(command):
            result["response"] = f"Command '{command}' is not in the whitelist for safety reasons"
            return result
            
        if len(command) > self.max_command_length:
            result["response"] = f"Command too long (max {self.max_command_length} chars)"
            return result
            
        # Execute command
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=10
            )
            
            output = stdout.decode().strip()
            error = stderr.decode().strip()
            
            result["success"] = process.returncode == 0
            result["response"] = output if output else (error if error else "Command executed")
            result["data"] = {
                "command": command,
                "exit_code": process.returncode,
                "stdout": output,
                "stderr": error
            }
            
        except asyncio.TimeoutError:
            result["response"] = "Command execution timed out"
            
        except Exception as e:
            result["response"] = f"Command execution error: {str(e)}"
            
        return result
        
    def _extract_command(self, text: str) -> str:
        """Extract command from text."""
        text_lower = text.lower()
        
        # Remove common phrases
        phrases = ["run", "execute", "command", "the command"]
        for phrase in phrases:
            text_lower = text_lower.replace(phrase, "")
            
        return text.strip()
        
    def _is_safe_command(self, command: str) -> bool:
        """Check if command is in whitelist."""
        # Get the base command (first word)
        base_command = command.split()[0] if command else ""
        
        return base_command in self.whitelist
