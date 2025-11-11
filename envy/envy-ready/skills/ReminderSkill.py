#!/usr/bin/env python3
"""
ReminderSkill - Sets and manages reminders.
"""

import logging
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from base_skill import BaseSkill

logger = logging.getLogger(__name__)


class ReminderSkill(BaseSkill):
    """Skill for setting reminders."""
    
    def __init__(self):
        super().__init__()
        self.reminders_file = Path('artifacts/reminders.json')
        self.reminders_file.parent.mkdir(parents=True, exist_ok=True)
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set a reminder."""
        text = params.get('text', '')
        message = params.get('message', text)
        delay = params.get('delay', 5)  # Default 5 minutes
        unit = params.get('unit', 'minute')
        
        # Calculate reminder time
        if unit == 'minute':
            reminder_time = datetime.now() + timedelta(minutes=delay)
        elif unit == 'hour':
            reminder_time = datetime.now() + timedelta(hours=delay)
        elif unit == 'day':
            reminder_time = datetime.now() + timedelta(days=delay)
        else:
            reminder_time = datetime.now() + timedelta(minutes=delay)
        
        try:
            # Load existing reminders
            reminders = self._load_reminders()
            
            # Add new reminder
            reminder_id = int(time.time())
            reminders.append({
                'id': reminder_id,
                'message': message,
                'time': reminder_time.isoformat(),
                'created': datetime.now().isoformat()
            })
            
            # Save reminders
            self._save_reminders(reminders)
            
            self.logger.info(f"Reminder set: {message} at {reminder_time}")
            
            return {
                'success': True,
                'reminder_id': reminder_id,
                'message': message,
                'reminder_time': reminder_time.isoformat(),
                'message': f'Reminder set for {reminder_time.strftime("%Y-%m-%d %H:%M:%S")}'
            }
        except Exception as e:
            self.logger.error(f"Failed to set reminder: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _load_reminders(self) -> list:
        """Load reminders from file."""
        if self.reminders_file.exists():
            try:
                with open(self.reminders_file) as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_reminders(self, reminders: list):
        """Save reminders to file."""
        with open(self.reminders_file, 'w') as f:
            json.dump(reminders, f, indent=2)
