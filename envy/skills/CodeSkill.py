#!/usr/bin/env python3
"""
CodeSkill - Creates and edits code files.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent))
from base_skill import BaseSkill

logger = logging.getLogger(__name__)


class CodeSkill(BaseSkill):
    """Skill for creating and editing code files."""
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create or edit a code file."""
        text = params.get('text', '')
        filename = params.get('filename')
        content = params.get('content', '')
        
        # Extract filename from text if not provided
        if not filename:
            import re
            file_match = re.search(r'(\S+\.\w+)', text)
            if file_match:
                filename = file_match.group(1)
            else:
                return {
                    'success': False,
                    'error': 'No filename specified'
                }
        
        # Extract content from text if not provided
        if not content:
            if 'print' in text.lower():
                content_match = re.search(r'print[s]?\s+(.+)', text, re.IGNORECASE)
                if content_match:
                    content = f'print({content_match.group(1)})'
                else:
                    content = 'print("hello")'
            elif 'hello' in text.lower():
                content = 'print("hello")'
            else:
                content = f'# {text}\nprint("Hello from Envy")'
        
        # Ensure filename has extension
        if '.' not in filename:
            filename = f'{filename}.py'
        
        try:
            file_path = Path(filename)
            
            # Create file
            file_path.write_text(content)
            
            self.logger.info(f"Created file: {file_path}")
            
            return {
                'success': True,
                'filename': str(file_path),
                'content': content,
                'message': f'Created {filename}'
            }
        except Exception as e:
            self.logger.error(f"Failed to create file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def requires_confirmation(self, params: Dict[str, Any]) -> bool:
        """Require confirmation if overwriting existing file."""
        filename = params.get('filename')
        if filename:
            file_path = Path(filename)
            if file_path.exists():
                return True
        return False
