#!/usr/bin/env python3
"""
Code Skill - Creates and modifies code files
Handles file creation, editing, and basic code generation
"""

import os
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CodeSkill:
    """Skill for creating and manipulating code files"""
    
    def __init__(self, config):
        self.config = config
        skill_config = config.get('skills', {}).get('code_skill', {})
        self.workspace_dir = skill_config.get('workspace_dir', './workspace')
        self.allowed_extensions = skill_config.get('allowed_extensions', ['.py', '.js', '.txt', '.md'])
        
        # Create workspace directory
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        logger.info(f"CodeSkill initialized, workspace: {self.workspace_dir}")
    
    def execute(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute code creation/modification"""
        
        # Parse the request
        parsed = self._parse_request(input_text)
        
        if not parsed:
            return {
                'success': False,
                'error': 'Could not parse code request',
                'response': "I couldn't understand what file you want to create."
            }
        
        action = parsed['action']
        filename = parsed['filename']
        content = parsed.get('content', '')
        
        if action == 'create':
            return self._create_file(filename, content, input_text)
        elif action == 'modify':
            return self._modify_file(filename, content)
        elif action == 'read':
            return self._read_file(filename)
        else:
            return {
                'success': False,
                'error': f'Unknown action: {action}',
                'response': f"I don't know how to {action} a file."
            }
    
    def _parse_request(self, input_text: str) -> Optional[Dict[str, Any]]:
        """Parse user request to extract action, filename, and content"""
        text_lower = input_text.lower()
        
        # Extract filename
        filename_pattern = r'(\w+\.(?:py|js|txt|md|json|yaml|html|css))'
        match = re.search(filename_pattern, input_text, re.IGNORECASE)
        
        if not match:
            # Try to infer filename from context
            if 'test' in text_lower and ('py' in text_lower or 'python' in text_lower):
                filename = 'test.py'
            else:
                return None
        else:
            filename = match.group(1)
        
        # Determine action
        if any(word in text_lower for word in ['create', 'make', 'write', 'generate']):
            action = 'create'
        elif any(word in text_lower for word in ['modify', 'edit', 'change', 'update']):
            action = 'modify'
        elif any(word in text_lower for word in ['read', 'show', 'display']):
            action = 'read'
        else:
            action = 'create'  # Default
        
        # Extract content description
        content_keywords = ['that', 'which', 'to']
        content_desc = input_text
        for keyword in content_keywords:
            if keyword in text_lower:
                parts = input_text.lower().split(keyword, 1)
                if len(parts) > 1:
                    content_desc = parts[1].strip()
                    break
        
        return {
            'action': action,
            'filename': filename,
            'content_description': content_desc,
            'original_text': input_text
        }
    
    def _create_file(self, filename: str, content_desc: str, original_text: str) -> Dict[str, Any]:
        """Create a new file"""
        
        # Validate filename
        _, ext = os.path.splitext(filename)
        if ext not in self.allowed_extensions:
            return {
                'success': False,
                'error': f'File extension not allowed: {ext}',
                'response': f"Sorry, I can't create {ext} files for security reasons."
            }
        
        filepath = os.path.join(self.workspace_dir, filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            return {
                'success': False,
                'error': 'File already exists',
                'response': f"The file {filename} already exists. Did you want to modify it?"
            }
        
        # Generate file content based on request
        content = self._generate_content(filename, content_desc, original_text)
        
        # Create file
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            
            logger.info(f"Created file: {filepath}")
            
            return {
                'success': True,
                'action': 'file_created',
                'filepath': filepath,
                'filename': filename,
                'response': f"I've created {filename} in the workspace.",
                'content': content
            }
        
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"Sorry, I couldn't create the file: {str(e)}"
            }
    
    def _generate_content(self, filename: str, content_desc: str, original_text: str) -> str:
        """Generate file content based on description"""
        
        _, ext = os.path.splitext(filename)
        text_lower = original_text.lower()
        
        if ext == '.py':
            # Python file
            if 'hello' in text_lower or 'print hello' in text_lower:
                return '#!/usr/bin/env python3\n\nprint("hello from envy")\n'
            elif 'test' in text_lower:
                return '#!/usr/bin/env python3\n\ndef test_example():\n    assert True\n\nif __name__ == "__main__":\n    test_example()\n    print("Tests passed!")\n'
            else:
                return f'#!/usr/bin/env python3\n\n# {filename}\n# Generated by Envy\n\ndef main():\n    pass\n\nif __name__ == "__main__":\n    main()\n'
        
        elif ext == '.js':
            # JavaScript file
            if 'hello' in text_lower:
                return 'console.log("hello from envy");\n'
            else:
                return f'// {filename}\n// Generated by Envy\n\nfunction main() {{\n    // Your code here\n}}\n\nmain();\n'
        
        elif ext == '.md':
            # Markdown file
            return f'# {filename}\n\nGenerated by Envy.\n\n## Description\n\n{content_desc}\n'
        
        elif ext == '.txt':
            # Plain text
            return f'{filename}\nGenerated by Envy\n\n{content_desc}\n'
        
        else:
            # Generic content
            return f'# {filename}\n# Generated by Envy\n'
    
    def _modify_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Modify an existing file"""
        filepath = os.path.join(self.workspace_dir, filename)
        
        if not os.path.exists(filepath):
            return {
                'success': False,
                'error': 'File not found',
                'response': f"The file {filename} doesn't exist. Did you want to create it?"
            }
        
        # For now, append to file
        try:
            with open(filepath, 'a') as f:
                f.write(f'\n# Modified by Envy\n{content}\n')
            
            return {
                'success': True,
                'action': 'file_modified',
                'filepath': filepath,
                'response': f"I've modified {filename}."
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response': f"Sorry, I couldn't modify the file: {str(e)}"
            }
    
    def _read_file(self, filename: str) -> Dict[str, Any]:
        """Read a file"""
        filepath = os.path.join(self.workspace_dir, filename)
        
        if not os.path.exists(filepath):
            return {
                'success': False,
                'error': 'File not found',
                'response': f"The file {filename} doesn't exist."
            }
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            return {
                'success': True,
                'action': 'file_read',
                'filepath': filepath,
                'content': content,
                'response': f"Here's the content of {filename}."
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response': f"Sorry, I couldn't read the file: {str(e)}"
            }
    
    def is_destructive(self, input_text: str) -> bool:
        """Check if action is destructive"""
        # File creation is generally safe in workspace
        # Modification and deletion would be destructive
        text_lower = input_text.lower()
        return any(word in text_lower for word in ['delete', 'remove', 'erase'])
    
    def preview_action(self, input_text: str) -> str:
        """Preview the action"""
        parsed = self._parse_request(input_text)
        if parsed:
            return f"{parsed['action']} file: {parsed['filename']}"
        return "Create/modify code file"


def main():
    """Standalone test"""
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'skills': {
            'code_skill': {
                'workspace_dir': './workspace',
                'allowed_extensions': ['.py', '.js', '.txt', '.md']
            }
        }
    }
    
    skill = CodeSkill(config)
    
    # Test file creation
    result = skill.execute("Create test.py that prints hello")
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
