"""
CodeSkill: Create, edit, and manage code files
"""
import os
import re
from pathlib import Path
from typing import Dict, Any

from skills.base_skill import BaseSkill
from services.config_loader import get_config


class CodeSkill(BaseSkill):
    """Skill for code and file operations"""
    
    def __init__(self):
        super().__init__("CodeSkill")
        self.description = "Create and manage code files"
        self.actions = ['create_file', 'read_file', 'edit_file', 'delete_file']
        
        # Load settings
        workspace_dir = self.config.get('skills.code_skill.workspace_dir', 'workspace')
        base_dir = Path(__file__).parent.parent
        self.workspace_dir = base_dir / workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        self.allowed_extensions = self.config.get('skills.code_skill.allowed_extensions', 
                                                  ['.py', '.js', '.txt', '.md'])
        self.max_file_size_kb = self.config.get('skills.code_skill.max_file_size_kb', 1024)
        
        self.logger.info(f"CodeSkill initialized (workspace: {self.workspace_dir})")
    
    def execute(self, action: str, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code skill action"""
        
        if action == 'create_file':
            return self.create_file(command, parameters)
        elif action == 'read_file':
            return self.read_file(command, parameters)
        elif action == 'edit_file':
            return self.edit_file(command, parameters)
        elif action == 'delete_file':
            return self.delete_file(command, parameters)
        else:
            return self.error_response(f"Unknown action: {action}")
    
    def create_file(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new file from voice command"""
        self.logger.info(f"Creating file from command: {command}")
        
        # Extract filename and content from command
        filename, content = self._parse_create_command(command)
        
        if not filename:
            return self.error_response("Could not determine filename from command")
        
        # Validate extension
        ext = Path(filename).suffix
        if ext and ext not in self.allowed_extensions:
            return self.error_response(f"File extension {ext} not allowed")
        
        # Create file path
        file_path = self.workspace_dir / filename
        
        # Check if file exists
        if file_path.exists():
            return self.error_response(f"File {filename} already exists")
        
        try:
            # Write file
            with open(file_path, 'w') as f:
                f.write(content)
            
            self.logger.info(f"Created file: {file_path}")
            return self.success_response(
                f"Created {filename} successfully",
                data={'path': str(file_path), 'size': len(content)}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create file: {e}")
            return self.error_response(f"Failed to create file: {e}")
    
    def _parse_create_command(self, command: str) -> tuple[str, str]:
        """Parse create file command to extract filename and content"""
        command_lower = command.lower()
        
        # Try to find filename patterns
        # Pattern: "create <filename> that <content>"
        # Pattern: "make a file called <filename> with <content>"
        
        filename = None
        content = ""
        
        # Look for filename
        patterns = [
            r'create\s+([^\s]+\.[\w]+)',  # "create test.py"
            r'file\s+called\s+([^\s]+\.[\w]+)',  # "file called test.py"
            r'make\s+([^\s]+\.[\w]+)',  # "make test.py"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command_lower)
            if match:
                filename = match.group(1)
                break
        
        # Look for content
        content_patterns = [
            r'that\s+(.+)',
            r'with\s+(.+)',
            r'containing\s+(.+)',
        ]
        
        for pattern in content_patterns:
            match = re.search(pattern, command_lower)
            if match:
                content_desc = match.group(1)
                # Generate code based on description
                content = self._generate_code(filename, content_desc)
                break
        
        # Default content if none specified
        if not content and filename:
            if filename.endswith('.py'):
                content = '# Auto-generated Python file\nprint("Hello from Envy")\n'
            elif filename.endswith('.js'):
                content = '// Auto-generated JavaScript file\nconsole.log("Hello from Envy");\n'
            else:
                content = '# Auto-generated file by Envy\n'
        
        return filename, content
    
    def _generate_code(self, filename: str, description: str) -> str:
        """Generate code based on description"""
        description_lower = description.lower()
        
        if filename.endswith('.py'):
            if 'print' in description_lower and 'hello' in description_lower:
                return '#!/usr/bin/env python3\n# Auto-generated by Envy\n\nprint("hello")\n'
            elif 'hello world' in description_lower:
                return '#!/usr/bin/env python3\nprint("Hello, World!")\n'
            else:
                return f'#!/usr/bin/env python3\n# {description}\n\nprint("Generated by Envy")\n'
        
        elif filename.endswith('.js'):
            if 'hello' in description_lower:
                return '// Auto-generated by Envy\nconsole.log("Hello");\n'
            else:
                return f'// {description}\nconsole.log("Generated by Envy");\n'
        
        else:
            return f'# {description}\nAuto-generated by Envy\n'
    
    def read_file(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents"""
        # Extract filename from command
        filename = parameters.get('filename') or self._extract_filename(command)
        
        if not filename:
            return self.error_response("Could not determine filename")
        
        file_path = self.workspace_dir / filename
        
        if not file_path.exists():
            return self.error_response(f"File {filename} not found")
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            return self.success_response(
                f"Read {filename}",
                data={'content': content}
            )
        except Exception as e:
            return self.error_response(f"Failed to read file: {e}")
    
    def edit_file(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Edit existing file"""
        return self.error_response("Edit file not implemented yet")
    
    def delete_file(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Delete file (requires confirmation)"""
        return self.error_response("Delete file not implemented yet")
    
    def _extract_filename(self, command: str) -> str:
        """Extract filename from command"""
        patterns = [
            r'([^\s]+\.[\w]+)',  # any file.ext pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command)
            if match:
                return match.group(1)
        
        return ""


def main():
    """Test code skill standalone"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    skill = CodeSkill()
    
    # Test create file
    commands = [
        "create test.py that prints hello",
        "make a file called hello.js with hello world",
    ]
    
    for cmd in commands:
        print(f"\n--- Testing: {cmd} ---")
        result = skill.execute('create_file', cmd, {})
        print(f"Success: {result['success']}")
        print(f"Response: {result.get('response', result.get('error'))}")


if __name__ == "__main__":
    main()
