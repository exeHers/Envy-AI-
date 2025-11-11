"""CodeSkill - creates and modifies code files."""
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.skill_manager import BaseSkill


class CodeSkill(BaseSkill):
    """Skill for creating and modifying code files."""
    
    def execute(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code creation/modification."""
        text = intent_data.get('text', '')
        
        # Extract filename and content from text
        filename, content = self._parse_code_request(text)
        
        if not filename:
            return {
                'success': False,
                'error': 'Could not determine filename from request'
            }
        
        try:
            # Create file
            file_path = Path(filename)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not content:
                # Generate default content based on file extension
                content = self._generate_default_content(filename)
            
            file_path.write_text(content)
            
            self.logger.info(f"Created file: {filename}")
            
            return {
                'success': True,
                'filename': filename,
                'content': content,
                'message': f'Created {filename}'
            }
        except Exception as e:
            self.logger.error(f"Error creating file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_code_request(self, text: str) -> tuple:
        """Parse code request to extract filename and content."""
        # Pattern: "create test.py that prints hello"
        patterns = [
            r'(?:create|write|make)\s+(\S+\.\w+)\s+(?:that|which)\s+(.+)',
            r'(?:create|write|make)\s+(\S+\.\w+)',
        ]
        
        filename = None
        content = None
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                filename = match.group(1)
                if len(match.groups()) > 1:
                    content_desc = match.group(2)
                    content = self._generate_content_from_description(filename, content_desc)
                break
        
        return filename, content
    
    def _generate_content_from_description(self, filename: str, description: str) -> str:
        """Generate code content from description."""
        ext = Path(filename).suffix.lower()
        
        if 'print' in description.lower() and ext == '.py':
            # Extract what to print
            print_match = re.search(r'print[s]?\s+(.+)', description.lower())
            if print_match:
                content = print_match.group(1).strip()
                # Clean up content
                content = content.replace('hello', '"hello"')
                return f'print({content})\n'
        
        return self._generate_default_content(filename)
    
    def _generate_default_content(self, filename: str) -> str:
        """Generate default content based on file extension."""
        ext = Path(filename).suffix.lower()
        
        defaults = {
            '.py': 'print("Hello from Envy")\n',
            '.js': 'console.log("Hello from Envy");\n',
            '.html': '<!DOCTYPE html>\n<html><head><title>Envy</title></head><body><h1>Hello from Envy</h1></body></html>\n',
            '.txt': 'Hello from Envy\n',
        }
        
        return defaults.get(ext, f'# {filename}\n')
    
    def requires_confirmation(self, intent_data: Dict[str, Any]) -> bool:
        """Code creation doesn't require confirmation by default."""
        # Could check for overwrite scenarios
        return False
