"""
Core skills for Envy assistant.
"""
import asyncio
import logging
import os
import re
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class CodeSkill:
    """Skill for creating and editing code files."""
    
    def __init__(self, config: dict):
        self.name = "CodeSkill"
        self.config = config
        self.workspace = config.get('workspace', '.')
    
    async def execute(self, user_text: str, context: dict) -> dict:
        """Execute code-related commands."""
        logger.info(f"CodeSkill executing: {user_text}")
        
        # Extract file creation command
        # Pattern: "create test.py that prints hello"
        create_match = re.search(r'create\s+(\S+)\s+(?:that\s+)?(.+)', user_text, re.IGNORECASE)
        if create_match:
            filename = create_match.group(1)
            content_desc = create_match.group(2)
            
            # Generate code content
            content = self._generate_code_content(content_desc, filename)
            
            # Write file
            filepath = os.path.join(self.workspace, filename)
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            logger.info(f"Created file: {filepath}")
            return {
                'response': f"Created {filename} with the requested code.",
                'outputs': [{'type': 'file', 'path': filepath}]
            }
        
        return {
            'response': "I didn't understand the code command. Try: 'create filename.py that prints hello'",
            'outputs': []
        }
    
    def _generate_code_content(self, description: str, filename: str) -> str:
        """Generate code content from description."""
        desc_lower = description.lower()
        
        # Simple rule-based code generation
        if 'print' in desc_lower:
            if 'hello' in desc_lower:
                return 'print("hello")\n'
            else:
                # Extract what to print
                print_match = re.search(r'prints?\s+(.+)', desc_lower)
                if print_match:
                    text = print_match.group(1).strip()
                    return f'print("{text}")\n'
                return 'print("Hello from Envy")\n'
        
        # Default Python file
        if filename.endswith('.py'):
            return f'# {description}\nprint("Hello from Envy")\n'
        
        return f'# {description}\n'
    
    def requires_confirmation(self, user_text: str) -> bool:
        """Check if file write requires confirmation."""
        user_lower = user_text.lower()
        # Check for overwrite scenarios
        return 'overwrite' in user_lower or 'replace' in user_lower


class ResearchSkill:
    """Skill for researching topics."""
    
    def __init__(self, config: dict):
        self.name = "ResearchSkill"
        self.config = config
        self.output_dir = config.get('output_dir', 'artifacts')
    
    async def execute(self, user_text: str, context: dict) -> dict:
        """Execute research command."""
        logger.info(f"ResearchSkill executing: {user_text}")
        
        # Extract research topic
        research_match = re.search(r'research\s+(.+)', user_text, re.IGNORECASE)
        if research_match:
            topic = research_match.group(1).strip()
            
            # Generate research summary (simplified - would use web search in production)
            summary = await self._research_topic(topic)
            
            # Save to file
            os.makedirs(self.output_dir, exist_ok=True)
            filename = f"research_{topic.replace(' ', '_')[:50]}.txt"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(f"Research Summary: {topic}\n")
                f.write(f"Date: {datetime.now().isoformat()}\n\n")
                f.write(summary)
            
            logger.info(f"Research saved to: {filepath}")
            return {
                'response': f"I've researched {topic} and saved a summary to {filename}.",
                'outputs': [{'type': 'file', 'path': filepath}]
            }
        
        return {
            'response': "I didn't understand the research command. Try: 'research quantum computing'",
            'outputs': []
        }
    
    async def _research_topic(self, topic: str) -> str:
        """Research a topic (simplified implementation)."""
        # In production, this would use web search APIs
        # For now, return a placeholder summary
        return f"""
Topic: {topic}

Summary:
This is a placeholder research summary for {topic}. In a full implementation, 
this would include web search results, key findings, and references.

Key Points:
- {topic} is an interesting subject
- Further research would provide more detailed information
- Multiple sources should be consulted for comprehensive understanding

Note: This is a demo response. Enable web search integration for real research.
"""
    
    def requires_confirmation(self, user_text: str) -> bool:
        return False


class SysControlSkill:
    """Skill for system control commands."""
    
    def __init__(self, config: dict):
        self.name = "SysControlSkill"
        self.config = config
        self.allowed_commands = config.get('security', {}).get('allowed_commands', [])
        self.sandbox_enabled = config.get('security', {}).get('sandbox_enabled', True)
    
    async def execute(self, user_text: str, context: dict) -> dict:
        """Execute system control command."""
        logger.info(f"SysControlSkill executing: {user_text}")
        
        # Extract command
        command_match = re.search(r'(?:run|execute|open|close)\s+(.+)', user_text, re.IGNORECASE)
        if command_match:
            command = command_match.group(1).strip()
            
            # Check if command is allowed
            if self.sandbox_enabled and self.allowed_commands:
                if command not in self.allowed_commands:
                    return {
                        'response': f"Command '{command}' is not in the allowed list. Add it to config to enable.",
                        'outputs': []
                    }
            
            # Execute command (with safety checks)
            if self._is_safe_command(command):
                try:
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    output = result.stdout or result.stderr
                    return {
                        'response': f"Executed command: {command}",
                        'outputs': [{'type': 'command_output', 'content': output}]
                    }
                except Exception as e:
                    return {
                        'response': f"Error executing command: {str(e)}",
                        'outputs': []
                    }
            else:
                return {
                    'response': f"Command '{command}' requires additional confirmation for safety.",
                    'outputs': []
                }
        
        return {
            'response': "I didn't understand the system command. Try: 'run ls'",
            'outputs': []
        }
    
    def _is_safe_command(self, command: str) -> bool:
        """Check if command is safe to execute."""
        safe_patterns = ['ls', 'pwd', 'date', 'echo', 'cat', 'head', 'tail']
        dangerous_patterns = ['rm', 'del', 'format', 'shutdown', 'kill', 'sudo']
        
        command_lower = command.lower()
        
        if any(pattern in command_lower for pattern in dangerous_patterns):
            return False
        
        if any(pattern in command_lower for pattern in safe_patterns):
            return True
        
        return False
    
    def requires_confirmation(self, user_text: str) -> bool:
        """Most system commands require confirmation."""
        return True


class ReminderSkill:
    """Skill for setting reminders."""
    
    def __init__(self, config: dict):
        self.name = "ReminderSkill"
        self.config = config
        self.reminders_file = os.path.join(config.get('data_dir', '.'), 'reminders.json')
        self.reminders: List[Dict[str, Any]] = []
        self._load_reminders()
    
    def _load_reminders(self):
        """Load reminders from file."""
        if os.path.exists(self.reminders_file):
            try:
                import json
                with open(self.reminders_file, 'r') as f:
                    self.reminders = json.load(f)
            except Exception:
                self.reminders = []
        else:
            self.reminders = []
    
    def _save_reminders(self):
        """Save reminders to file."""
        import json
        os.makedirs(os.path.dirname(self.reminders_file) if os.path.dirname(self.reminders_file) else '.', exist_ok=True)
        with open(self.reminders_file, 'w') as f:
            json.dump(self.reminders, f, indent=2)
    
    async def execute(self, user_text: str, context: dict) -> dict:
        """Execute reminder command."""
        logger.info(f"ReminderSkill executing: {user_text}")
        
        # Extract reminder details
        remind_match = re.search(r'remind\s+me\s+(?:to\s+)?(.+?)(?:\s+in\s+(\d+)\s*(minute|hour|day)s?)?', user_text, re.IGNORECASE)
        if remind_match:
            reminder_text = remind_match.group(1).strip()
            time_amount = remind_match.group(2)
            time_unit = remind_match.group(3) if remind_match.group(3) else 'minute'
            
            # Calculate reminder time
            if time_amount:
                delta_map = {'minute': timedelta(minutes=int(time_amount)),
                           'hour': timedelta(hours=int(time_amount)),
                           'day': timedelta(days=int(time_amount))}
                reminder_time = datetime.now() + delta_map.get(time_unit, timedelta(minutes=int(time_amount)))
            else:
                reminder_time = datetime.now() + timedelta(minutes=5)  # Default 5 minutes
            
            # Add reminder
            reminder = {
                'id': len(self.reminders),
                'text': reminder_text,
                'time': reminder_time.isoformat(),
                'created': datetime.now().isoformat()
            }
            self.reminders.append(reminder)
            self._save_reminders()
            
            logger.info(f"Reminder set: {reminder_text} at {reminder_time}")
            return {
                'response': f"I'll remind you to {reminder_text} at {reminder_time.strftime('%H:%M')}.",
                'outputs': [{'type': 'reminder', 'data': reminder}]
            }
        
        return {
            'response': "I didn't understand the reminder command. Try: 'remind me to call mom in 30 minutes'",
            'outputs': []
        }
    
    def requires_confirmation(self, user_text: str) -> bool:
        return False
