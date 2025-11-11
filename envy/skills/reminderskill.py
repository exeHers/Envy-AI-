"""ReminderSkill - sets reminders and alerts."""
import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import re
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.skill_manager import BaseSkill


class ReminderSkill(BaseSkill):
    """Skill for setting reminders."""
    
    def __init__(self, config, logger: Optional[logging.Logger] = None):
        super().__init__(config, logger)
        self.reminders_file = Path("artifacts/reminders.json")
        self.reminders_file.parent.mkdir(parents=True, exist_ok=True)
    
    def execute(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute reminder request."""
        text = intent_data.get('text', '')
        
        # Extract reminder details
        reminder_text, time_str = self._parse_reminder(text)
        
        if not reminder_text:
            return {
                'success': False,
                'error': 'Could not determine reminder text'
            }
        
        try:
            # Load existing reminders
            reminders = self._load_reminders()
            
            # Create reminder
            reminder = {
                'id': len(reminders) + 1,
                'text': reminder_text,
                'time': time_str or 'asap',
                'created': datetime.now().isoformat(),
                'completed': False
            }
            
            reminders.append(reminder)
            
            # Save reminders
            self._save_reminders(reminders)
            
            self.logger.info(f"Reminder created: {reminder_text}")
            
            return {
                'success': True,
                'reminder': reminder,
                'message': f'Reminder set: {reminder_text}'
            }
        except Exception as e:
            self.logger.error(f"Error creating reminder: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_reminder(self, text: str) -> tuple:
        """Parse reminder text and time."""
        # Pattern: "remind me to X" or "remind me about X"
        patterns = [
            r'remind\s+me\s+to\s+(.+)',
            r'remind\s+me\s+about\s+(.+)',
            r'reminder\s+(.+)',
        ]
        
        reminder_text = ""
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                reminder_text = match.group(1).strip()
                break
        
        # Extract time if mentioned
        time_str = None
        time_patterns = [
            r'in\s+(\d+)\s+(minute|hour|day)',
            r'at\s+(\d+:\d+)',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text.lower())
            if match:
                time_str = match.group(0)
                break
        
        return reminder_text, time_str
    
    def _load_reminders(self) -> list:
        """Load reminders from file."""
        if self.reminders_file.exists():
            try:
                with open(self.reminders_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_reminders(self, reminders: list):
        """Save reminders to file."""
        with open(self.reminders_file, 'w') as f:
            json.dump(reminders, f, indent=2)
    
    def requires_confirmation(self, intent_data: Dict[str, Any]) -> bool:
        """Reminders don't require confirmation."""
        return False
