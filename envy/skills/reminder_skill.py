#!/usr/bin/env python3
"""
Reminder Skill - Sets and manages reminders
Stores reminders and provides notification capabilities
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import re

logger = logging.getLogger(__name__)


class ReminderSkill:
    """Skill for setting and managing reminders"""
    
    def __init__(self, config):
        self.config = config
        skill_config = config.get('skills', {}).get('reminder_skill', {})
        self.storage_file = skill_config.get('storage_file', './data/reminders.json')
        
        # Create data directory
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        
        # Load existing reminders
        self.reminders = self._load_reminders()
        
        logger.info(f"ReminderSkill initialized, storage: {self.storage_file}")
    
    def execute(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute reminder task"""
        
        # Parse reminder request
        parsed = self._parse_reminder(input_text)
        
        if not parsed:
            return {
                'success': False,
                'error': 'Could not parse reminder',
                'response': "I couldn't understand when or what you want to be reminded about."
            }
        
        action = parsed.get('action', 'create')
        
        if action == 'create':
            return self._create_reminder(parsed)
        elif action == 'list':
            return self._list_reminders()
        elif action == 'delete':
            return self._delete_reminder(parsed)
        else:
            return {
                'success': False,
                'error': f'Unknown action: {action}',
                'response': f"I don't know how to {action} reminders."
            }
    
    def _parse_reminder(self, input_text: str) -> Optional[Dict[str, Any]]:
        """Parse reminder from input text"""
        text_lower = input_text.lower()
        
        # Determine action
        if any(word in text_lower for word in ['list', 'show', 'what are my']):
            return {'action': 'list'}
        
        if any(word in text_lower for word in ['delete', 'remove', 'cancel']):
            return {'action': 'delete', 'text': input_text}
        
        # Default to create
        action = 'create'
        
        # Extract time
        time_info = self._extract_time(input_text)
        
        # Extract message
        message = self._extract_message(input_text)
        
        if not message:
            return None
        
        return {
            'action': action,
            'message': message,
            'time': time_info.get('datetime'),
            'time_str': time_info.get('description', 'later'),
            'original_text': input_text
        }
    
    def _extract_time(self, input_text: str) -> Dict[str, Any]:
        """Extract time information from text"""
        text_lower = input_text.lower()
        now = datetime.now()
        
        # Parse relative time
        if 'in' in text_lower:
            # "in 5 minutes", "in 1 hour"
            match = re.search(r'in (\d+) (minute|hour|day)s?', text_lower)
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                
                if unit == 'minute':
                    target_time = now + timedelta(minutes=value)
                    return {
                        'datetime': target_time,
                        'description': f'in {value} minute{"s" if value > 1 else ""}'
                    }
                elif unit == 'hour':
                    target_time = now + timedelta(hours=value)
                    return {
                        'datetime': target_time,
                        'description': f'in {value} hour{"s" if value > 1 else ""}'
                    }
                elif unit == 'day':
                    target_time = now + timedelta(days=value)
                    return {
                        'datetime': target_time,
                        'description': f'in {value} day{"s" if value > 1 else ""}'
                    }
        
        # Parse absolute time
        if 'tomorrow' in text_lower:
            target_time = now + timedelta(days=1)
            return {
                'datetime': target_time,
                'description': 'tomorrow'
            }
        
        if 'later' in text_lower or 'sometime' in text_lower:
            target_time = now + timedelta(hours=1)
            return {
                'datetime': target_time,
                'description': 'later'
            }
        
        # Default to 1 hour
        return {
            'datetime': now + timedelta(hours=1),
            'description': 'in 1 hour'
        }
    
    def _extract_message(self, input_text: str) -> Optional[str]:
        """Extract reminder message from text"""
        text_lower = input_text.lower()
        
        # Remove command words
        for word in ['remind', 'reminder', 'to', 'me', 'about', 'that']:
            text_lower = text_lower.replace(word, '')
        
        # Remove time phrases
        time_phrases = [
            r'in \d+ (minute|hour|day)s?',
            r'tomorrow',
            r'later',
            r'sometime'
        ]
        
        for pattern in time_phrases:
            text_lower = re.sub(pattern, '', text_lower)
        
        # Clean up
        message = text_lower.strip()
        
        if len(message) > 3:
            return message
        
        # Fallback - use original text
        return input_text
    
    def _create_reminder(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new reminder"""
        reminder = {
            'id': len(self.reminders) + 1,
            'message': parsed['message'],
            'time': parsed['time'].isoformat() if parsed['time'] else None,
            'time_str': parsed['time_str'],
            'created': datetime.now().isoformat(),
            'completed': False
        }
        
        self.reminders.append(reminder)
        self._save_reminders()
        
        logger.info(f"Created reminder: {reminder}")
        
        return {
            'success': True,
            'action': 'reminder_created',
            'reminder': reminder,
            'response': f"I'll remind you {parsed['time_str']}: {parsed['message']}"
        }
    
    def _list_reminders(self) -> Dict[str, Any]:
        """List all reminders"""
        active_reminders = [r for r in self.reminders if not r['completed']]
        
        if not active_reminders:
            return {
                'success': True,
                'action': 'reminders_listed',
                'reminders': [],
                'response': "You have no active reminders."
            }
        
        # Format reminder list
        reminder_list = []
        for r in active_reminders:
            reminder_list.append(f"- {r['time_str']}: {r['message']}")
        
        response = f"You have {len(active_reminders)} reminder{'s' if len(active_reminders) > 1 else ''}: " + ", ".join([r['message'] for r in active_reminders[:3]])
        
        return {
            'success': True,
            'action': 'reminders_listed',
            'reminders': active_reminders,
            'response': response
        }
    
    def _delete_reminder(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a reminder"""
        # For simplicity, delete the most recent reminder
        if self.reminders:
            deleted = self.reminders.pop()
            self._save_reminders()
            
            return {
                'success': True,
                'action': 'reminder_deleted',
                'response': f"I've deleted the reminder: {deleted['message']}"
            }
        else:
            return {
                'success': False,
                'error': 'No reminders to delete',
                'response': "You don't have any reminders to delete."
            }
    
    def _load_reminders(self) -> List[Dict[str, Any]]:
        """Load reminders from storage"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading reminders: {e}")
        
        return []
    
    def _save_reminders(self):
        """Save reminders to storage"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.reminders, f, indent=2)
            logger.debug("Reminders saved")
        except Exception as e:
            logger.error(f"Error saving reminders: {e}")
    
    def is_destructive(self, input_text: str) -> bool:
        """Reminders are not destructive"""
        return False
    
    def preview_action(self, input_text: str) -> str:
        """Preview the action"""
        parsed = self._parse_reminder(input_text)
        if parsed:
            action = parsed.get('action', 'create')
            if action == 'create':
                return f"Set reminder: {parsed.get('message', 'unknown')}"
            else:
                return f"{action} reminder"
        return "Manage reminder"


def main():
    """Standalone test"""
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'skills': {
            'reminder_skill': {
                'storage_file': './data/reminders.json'
            }
        }
    }
    
    skill = ReminderSkill(config)
    
    # Test reminder creation
    result = skill.execute("Remind me in 30 minutes to check on the project")
    print(f"Result: {result}")
    
    # Test listing reminders
    result = skill.execute("List my reminders")
    print(f"List result: {result}")


if __name__ == "__main__":
    main()
