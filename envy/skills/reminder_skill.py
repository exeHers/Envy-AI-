"""
Reminder Skill - Manages reminders and notifications
MIT License
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re

import sys
sys.path.insert(0, str(Path(__file__).parent))
from __init__ import BaseSkill

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.config_manager import get_config

logger = logging.getLogger(__name__)


class ReminderSkill(BaseSkill):
    """Skill for managing reminders"""
    
    def __init__(self):
        super().__init__()
        self.config = get_config()
        
        base_path = Path(__file__).parent.parent
        storage_path = self.config.get('skills.reminder.storage_path', 'artifacts/reminders.json')
        self.storage_file = base_path / storage_path
        
        # Ensure parent directory exists
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.reminders: List[Dict[str, Any]] = []
        self.load_reminders()
        
        logger.info(f"ReminderSkill initialized (storage: {self.storage_file})")
    
    def execute(self, command: str) -> str:
        """Execute reminder command"""
        try:
            command_lower = command.lower()
            
            # List reminders
            if 'list' in command_lower or 'show' in command_lower:
                return self.list_reminders()
            
            # Add reminder
            else:
                return self.add_reminder(command)
                
        except Exception as e:
            logger.error(f"ReminderSkill execution failed: {e}")
            return f"Reminder operation failed: {str(e)}"
    
    def add_reminder(self, command: str) -> str:
        """Add a new reminder"""
        try:
            # Extract reminder text and time
            text, time_str = self.parse_reminder(command)
            
            if not text:
                return "Could not understand reminder. Try: 'remind me to X in 10 minutes'"
            
            # Calculate reminder time
            remind_time = self.parse_time(time_str)
            
            # Create reminder
            reminder = {
                'id': len(self.reminders) + 1,
                'text': text,
                'created': datetime.now().isoformat(),
                'remind_at': remind_time.isoformat() if remind_time else None,
                'active': True
            }
            
            self.reminders.append(reminder)
            self.save_reminders()
            
            logger.info(f"Added reminder: {text}")
            
            time_desc = remind_time.strftime('%I:%M %p') if remind_time else "now"
            return f"Reminder set: {text} at {time_desc}"
            
        except Exception as e:
            logger.error(f"Failed to add reminder: {e}")
            return f"Could not add reminder: {str(e)}"
    
    def parse_reminder(self, command: str) -> tuple[Optional[str], Optional[str]]:
        """Parse reminder text and time from command"""
        command_lower = command.lower()
        
        # Pattern: "remind me to X in Y"
        match = re.search(r'remind me to (.+?) in (.+)', command_lower)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        # Pattern: "reminder to X"
        match = re.search(r'remind(?:er)? to (.+)', command_lower)
        if match:
            return match.group(1).strip(), None
        
        # Pattern: "remember X"
        match = re.search(r'remember (.+)', command_lower)
        if match:
            return match.group(1).strip(), None
        
        return None, None
    
    def parse_time(self, time_str: Optional[str]) -> datetime:
        """Parse time string into datetime"""
        now = datetime.now()
        
        if not time_str:
            return now
        
        time_lower = time_str.lower()
        
        # Parse "X minutes"
        match = re.search(r'(\d+)\s*minutes?', time_lower)
        if match:
            minutes = int(match.group(1))
            return now + timedelta(minutes=minutes)
        
        # Parse "X hours"
        match = re.search(r'(\d+)\s*hours?', time_lower)
        if match:
            hours = int(match.group(1))
            return now + timedelta(hours=hours)
        
        # Parse "X days"
        match = re.search(r'(\d+)\s*days?', time_lower)
        if match:
            days = int(match.group(1))
            return now + timedelta(days=days)
        
        # Default: now
        return now
    
    def list_reminders(self) -> str:
        """List all active reminders"""
        active = [r for r in self.reminders if r.get('active', True)]
        
        if not active:
            return "No active reminders."
        
        lines = [f"{len(active)} active reminder(s):"]
        for reminder in active[:5]:  # Show max 5
            text = reminder['text']
            remind_at = reminder.get('remind_at')
            if remind_at:
                dt = datetime.fromisoformat(remind_at)
                time_str = dt.strftime('%I:%M %p')
                lines.append(f"- {text} at {time_str}")
            else:
                lines.append(f"- {text}")
        
        return "\n".join(lines)
    
    def load_reminders(self):
        """Load reminders from storage"""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r') as f:
                    self.reminders = json.load(f)
                logger.info(f"Loaded {len(self.reminders)} reminders")
            else:
                self.reminders = []
        except Exception as e:
            logger.error(f"Failed to load reminders: {e}")
            self.reminders = []
    
    def save_reminders(self):
        """Save reminders to storage"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.reminders, f, indent=2)
            logger.debug("Reminders saved")
        except Exception as e:
            logger.error(f"Failed to save reminders: {e}")
    
    def requires_confirmation(self) -> bool:
        return False
    
    def get_description(self) -> str:
        return "Manages reminders and notifications"
