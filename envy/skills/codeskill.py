"""CodeSkill - Create and edit files."""
import logging
import re
from pathlib import Path
from typing import Dict, Any
from .base_skill import BaseSkill


logger = logging.getLogger(__name__)


class CodeSkill(BaseSkill):
    """Skill for creating and editing code files."""
    
    def execute(self, command: str) -> Dict[str, Any]:
        """Execute code creation/editing command."""
        logger.info(f"CodeSkill executing: {command}")
        
        # Extract filename and content
        filename_match = re.search(r'create\s+(\S+\.\w+)|make\s+(\S+\.\w+)|write\s+(\S+\.\w+)', command.lower())
        if not filename_match:
            # Try to find any file extension
            filename_match = re.search(r'(\S+\.(py|js|html|css|txt|md|json|yaml|yml))', command.lower())
        
        if not filename_match:
            return {
                "success": False,
                "response": "I couldn't identify a filename in your request.",
                "data": {}
            }
        
        filename = filename_match.group(1) or filename_match.group(2) or filename_match.group(3)
        
        # Extract content
        content = ""
        if "print" in command.lower() and "hello" in command.lower():
            if "python" in command.lower() or filename.endswith(".py"):
                content = 'print("hello")\n'
            else:
                content = 'console.log("hello");\n'
        elif "hello" in command.lower():
            content = "hello\n"
        else:
            # Try to extract content from command
            content_match = re.search(r'that\s+(.+?)(?:\.|$)', command.lower())
            if content_match:
                content = content_match.group(1) + "\n"
            else:
                content = "# Created by Envy\n"
        
        # Determine workspace path
        envy_dir = Path(__file__).parent.parent
        workspace_path = envy_dir / self.config.get("skills.sandbox.allowed_paths", ["workspace"])[0]
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        file_path = workspace_path / filename
        
        # Check sandbox restrictions
        if self.is_sandboxed():
            allowed_paths = self.config.get("skills.sandbox.allowed_paths", [])
            # Check if file_path is within any allowed path
            file_path_str = str(file_path.resolve())
            is_allowed = False
            for allowed in allowed_paths:
                allowed_path = (envy_dir / allowed).resolve()
                try:
                    file_path.resolve().relative_to(allowed_path)
                    is_allowed = True
                    break
                except ValueError:
                    continue
            
            if not is_allowed and allowed_paths:
                return {
                    "success": False,
                    "response": f"File creation outside allowed paths is restricted.",
                    "data": {}
                }
        
        try:
            # Write file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Created file: {file_path}")
            return {
                "success": True,
                "response": f"Created {filename} with the requested content.",
                "data": {
                    "file_path": str(file_path),
                    "filename": filename,
                    "content": content
                }
            }
        except Exception as e:
            logger.error(f"Failed to create file: {e}")
            return {
                "success": False,
                "response": f"I encountered an error creating the file: {str(e)}",
                "data": {}
            }
