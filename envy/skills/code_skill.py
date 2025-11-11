"""Code creation skill."""
import os
from pathlib import Path
from typing import Dict, Any


class CodeSkill:
    """Skill for creating and manipulating code files."""
    
    def __init__(self):
        self.workspace = Path.cwd() / "workspace"
        self.workspace.mkdir(exist_ok=True)
        
    async def create_file(self, filename: str = None, content: str = None, description: str = None, **kwargs) -> Dict[str, Any]:
        """Create a code file."""
        result = {
            "success": False,
            "response": "",
            "data": {}
        }
        
        # Extract filename from description if not provided
        if not filename and description:
            # Try to extract filename from description
            words = description.lower().split()
            for i, word in enumerate(words):
                if any(ext in word for ext in [".py", ".js", ".txt", ".md", ".sh"]):
                    filename = word
                    break
                elif word in ["file", "called", "named"] and i + 1 < len(words):
                    filename = words[i + 1]
                    break
                    
        if not filename:
            result["response"] = "No filename specified"
            return result
            
        # Clean filename
        filename = filename.strip("'\"")
        
        # Determine content based on filename and description
        if not content:
            if description:
                content = self._generate_content(filename, description)
            else:
                content = "# TODO: Add content\n"
                
        # Create file
        try:
            file_path = self.workspace / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(content)
                
            result["success"] = True
            result["response"] = f"Created file {filename} in workspace"
            result["data"] = {
                "path": str(file_path),
                "filename": filename,
                "size": len(content)
            }
            
        except Exception as e:
            result["response"] = f"Failed to create file: {str(e)}"
            
        return result
        
    def _generate_content(self, filename: str, description: str) -> str:
        """Generate file content based on description."""
        description_lower = description.lower()
        
        # Python file
        if filename.endswith('.py'):
            if "hello" in description_lower or "print" in description_lower:
                if "world" in description_lower:
                    return '#!/usr/bin/env python3\n\nprint("Hello, World!")\n'
                else:
                    return '#!/usr/bin/env python3\n\nprint("hello from envy")\n'
            else:
                return f'#!/usr/bin/env python3\n# {description}\n\ndef main():\n    pass\n\nif __name__ == "__main__":\n    main()\n'
                
        # JavaScript file
        elif filename.endswith('.js'):
            if "hello" in description_lower:
                return 'console.log("hello from envy");\n'
            else:
                return f'// {description}\n\nfunction main() {{\n    // TODO: Implement\n}}\n\nmain();\n'
                
        # Bash script
        elif filename.endswith('.sh'):
            return f'#!/bin/bash\n# {description}\n\necho "hello from envy"\n'
            
        # Text/Markdown
        elif filename.endswith(('.txt', '.md')):
            return f'# {filename}\n\n{description}\n'
            
        # Default
        else:
            return f'# {description}\n\n'
            
    async def edit_file(self, filename: str = None, content: str = None, **kwargs) -> Dict[str, Any]:
        """Edit an existing file."""
        result = {
            "success": False,
            "response": "",
            "data": {}
        }
        
        if not filename:
            result["response"] = "No filename specified"
            return result
            
        file_path = self.workspace / filename
        
        if not file_path.exists():
            result["response"] = f"File {filename} not found"
            return result
            
        try:
            with open(file_path, 'w') as f:
                f.write(content)
                
            result["success"] = True
            result["response"] = f"Updated file {filename}"
            result["data"] = {
                "path": str(file_path),
                "filename": filename
            }
            
        except Exception as e:
            result["response"] = f"Failed to edit file: {str(e)}"
            
        return result
