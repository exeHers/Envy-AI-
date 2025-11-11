"""
ReminderSkill: Create and manage reminders
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timedelta
import re

from skills.base_skill import BaseSkill
from services.config_loader import get_config


class ReminderSkill(BaseSkill):
    """Skill for managing reminders"""
    
    def __init__(self):
        super().__init__("ReminderSkill")
        self.description = "Create and manage reminders"
        self.actions = ['create_reminder', 'list_reminders', 'delete_reminder']
        
        # Load settings
        storage_file = self.config.get('skills.reminder_skill.storage_file', 'config/reminders.json')
        base_dir = Path(__file__).parent.parent
        self.storage_file = base_dir / storage_file
        
        # Ensure parent directory exists
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load reminders
        self.reminders: List[Dict[str, Any]] = []
        self._load_reminders()
        
        self.logger.info(f"ReminderSkill initialized ({len(self.reminders)} reminders)")
    
    def execute(self, action: str, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute reminder skill action"""
        
        if action == 'create_reminder':
            return self.create_reminder(command, parameters)
        elif action == 'list_reminders':
            return self.list_reminders(command, parameters)
        elif action == 'delete_reminder':
            return self.delete_reminder(command, parameters)
        else:
            return self.error_response(f"Unknown action: {action}")
    
    def create_reminder(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new reminder"""
        self.logger.info(f"Creating reminder: {command}")
        
        # Parse reminder from command
        reminder_text, when = self._parse_reminder_command(command)
        
        if not reminder_text:
            return self.error_response("Could not understand reminder content")
        
        # Create reminder
        reminder = {
            'id': len(self.reminders) + 1,
            'text': reminder_text,
            'when': when,
            'created': datetime.now().isoformat(),
            'completed': False
        }
        
        self.reminders.append(reminder)
        self._save_reminders()
        
        # Format response
        when_str = when if isinstance(when, str) else when.strftime('%Y-%m-%d %H:%M')
        response = f"Reminder created: {reminder_text}. When: {when_str}"
        
        return self.success_response(response, data=reminder)
    
    def list_reminders(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """List all reminders"""
        self.logger.info("Listing reminders")
        
        if not self.reminders:
            return self.success_response("You have no reminders.")
        
        active_reminders = [r for r in self.reminders if not r.get('completed', False)]
        
        if not active_reminders:
            return self.success_response("You have no active reminders.")
        
        # Format list
        reminder_list = []
        for r in active_reminders:
            when = r.get('when', 'unscheduled')
            reminder_list.append(f"- {r['text']} ({when})")
        
        response = f"You have {len(active_reminders)} reminder(s):\n" + "\n".join(reminder_list)
        
        return self.success_response(
            f"You have {len(active_reminders)} reminders",
            data={'reminders': active_reminders, 'list': reminder_list}
        )
    
    def delete_reminder(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a reminder"""
        # Implementation for deleting reminders
        return self.error_response("Delete reminder not yet implemented")
    
    def _parse_reminder_command(self, command: str) -> tuple[str, Any]:
        """Parse reminder command to extract text and time"""
        command_lower = command.lower()
        
        # Remove "remind me to" prefix
        text = command_lower
        for prefix in ['remind me to', 'remind me', 'reminder to', 'reminder']:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break
        
        # Look for time indicators
        when = "later"  # default
        
        # Check for specific times
        time_patterns = {
            'tomorrow': lambda: datetime.now() + timedelta(days=1),
            'next week': lambda: datetime.now() + timedelta(weeks=1),
            'tonight': lambda: datetime.now().replace(hour=20, minute=0),
            'in an hour': lambda: datetime.now() + timedelta(hours=1),
            'in 1 hour': lambda: datetime.now() + timedelta(hours=1),
        }
        
        for pattern, time_func in time_patterns.items():
            if pattern in command_lower:
                when = time_func()
                # Remove time from text
                text = text.replace(pattern, '').strip()
                break
        
        return text, when
    
    def _load_reminders(self):
        """Load reminders from storage"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r') as f:
                    self.reminders = json.load(f)
                self.logger.info(f"Loaded {len(self.reminders)} reminders")
            except Exception as e:
                self.logger.error(f"Failed to load reminders: {e}")
                self.reminders = []
        else:
            self.reminders = []
    
    def _save_reminders(self):
        """Save reminders to storage"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.reminders, f, indent=2)
            self.logger.info(f"Saved {len(self.reminders)} reminders")
        except Exception as e:
            self.logger.error(f"Failed to save reminders: {e}")


def main():
    """Test reminder skill standalone"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    skill = ReminderSkill()
    
    # Test create reminder
    commands = [
        "remind me to buy milk tomorrow",
        "reminder to call mom",
        "remind me to exercise in an hour",
    ]
    
    for cmd in commands:
        print(f"\n--- Testing: {cmd} ---")
        result = skill.execute('create_reminder', cmd, {})
        print(f"Success: {result['success']}")
        print(f"Response: {result.get('response', result.get('error'))}")
    
    # Test list
    print("\n--- Listing reminders ---")
    result = skill.execute('list_reminders', '', {})
    print(f"Response: {result.get('response', result.get('error'))}")


if __name__ == "__main__":
    main()
