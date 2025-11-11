"""
Code Skill - Creates files and writes code
MIT License
"""

import os
import re
import logging
from pathlib import Path
from typing import Optional, Tuple

# Import base skill from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent))
from __init__ import BaseSkill

# Import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.config_manager import get_config

logger = logging.getLogger(__name__)


class CodeSkill(BaseSkill):
    """Skill for creating files and writing code"""
    
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.workspace_path = Path(self.config.get('skills.code.workspace_path', '/workspace'))
        self.allowed_extensions = self.config.get('skills.code.allowed_extensions', ['.py', '.js', '.txt'])
        self.max_file_size_kb = self.config.get('skills.code.max_file_size_kb', 1024)
        
        logger.info(f"CodeSkill initialized (workspace: {self.workspace_path})")
    
    def execute(self, command: str) -> str:
        """Execute code creation command"""
        try:
            # Parse command to extract filename and content
            filename, content = self.parse_command(command)
            
            if not filename:
                return "Could not determine filename from command."
            
            # Validate filename
            if not self.is_allowed_file(filename):
                ext = Path(filename).suffix
                return f"File extension '{ext}' is not allowed. Allowed: {self.allowed_extensions}"
            
            # Create file
            file_path = self.workspace_path / filename
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(file_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Created file: {file_path}")
            
            return f"Created {filename} successfully."
            
        except Exception as e:
            logger.error(f"CodeSkill execution failed: {e}")
            return f"Failed to create file: {str(e)}"
    
    def parse_command(self, command: str) -> Tuple[Optional[str], str]:
        """
        Parse command to extract filename and content
        Returns: (filename, content)
        """
        command_lower = command.lower()
        
        # Try to find filename
        filename = None
        
        # Pattern 1: "create test.py that prints hello"
        match = re.search(r'create\s+(\S+\.\w+)', command_lower)
        if match:
            filename = match.group(1)
        
        # Pattern 2: "write hello.txt with content..."
        if not filename:
            match = re.search(r'write\s+(\S+\.\w+)', command_lower)
            if match:
                filename = match.group(1)
        
        # Pattern 3: "make file.py"
        if not filename:
            match = re.search(r'make\s+(\S+\.\w+)', command_lower)
            if match:
                filename = match.group(1)
        
        if not filename:
            # Try to find any filename-like pattern
            match = re.search(r'(\w+\.\w+)', command)
            if match:
                filename = match.group(1)
        
        # Generate content based on command
        content = self.generate_content(command, filename)
        
        return filename, content
    
    def generate_content(self, command: str, filename: Optional[str]) -> str:
        """Generate file content based on command"""
        command_lower = command.lower()
        
        # Determine file type
        if filename:
            ext = Path(filename).suffix.lower()
        else:
            ext = '.txt'
        
        # Python file
        if ext == '.py':
            if 'hello' in command_lower or 'print hello' in command_lower:
                return 'print("hello from envy")\n'
            elif 'test' in command_lower:
                return '# Test file created by Envy\nprint("Test successful")\n'
            else:
                return f'# File created by Envy\n# Command: {command}\nprint("File created")\n'
        
        # JavaScript file
        elif ext == '.js':
            if 'hello' in command_lower:
                return 'console.log("hello from envy");\n'
            else:
                return f'// File created by Envy\n// Command: {command}\nconsole.log("File created");\n'
        
        # Text file or unknown
        else:
            # Extract content if specified
            if 'with content' in command_lower:
                parts = command.split('with content', 1)
                if len(parts) > 1:
                    return parts[1].strip()
            
            if 'that says' in command_lower:
                parts = command.split('that says', 1)
                if len(parts) > 1:
                    return parts[1].strip()
            
            # Default content
            return f"File created by Envy\nCommand: {command}\n"
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        ext = Path(filename).suffix.lower()
        return ext in self.allowed_extensions
    
    def requires_confirmation(self) -> bool:
        """Code creation requires confirmation for certain operations"""
        return False  # Most code creation is safe
    
    def get_description(self) -> str:
        return "Creates files and writes code based on voice commands"
