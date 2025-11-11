"""Reminder skill for scheduling reminders."""
import asyncio
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timedelta


class ReminderSkill:
    """Skill for setting and managing reminders."""
    
    def __init__(self):
        self.data_dir = Path.cwd() / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.reminders_file = self.data_dir / "reminders.json"
        self.reminders = self._load_reminders()
        
    def _load_reminders(self) -> list:
        """Load reminders from file."""
        if self.reminders_file.exists():
            try:
                with open(self.reminders_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
        
    def _save_reminders(self):
        """Save reminders to file."""
        with open(self.reminders_file, 'w') as f:
            json.dump(self.reminders, f, indent=2)
            
    async def set_reminder(self, message: str = None, time: str = None, **kwargs) -> Dict[str, Any]:
        """Set a reminder."""
        result = {
            "success": False,
            "response": "",
            "data": {}
        }
        
        if not message:
            result["response"] = "No reminder message specified"
            return result
            
        # Extract message and time from input
        if not time:
            message, time = self._parse_reminder(message)
            
        # Create reminder
        reminder = {
            "id": len(self.reminders) + 1,
            "message": message,
            "time": time,
            "created": datetime.now().isoformat(),
            "triggered": False
        }
        
        self.reminders.append(reminder)
        self._save_reminders()
        
        result["success"] = True
        result["response"] = f"Reminder set: {message} at {time}"
        result["data"] = reminder
        
        return result
        
    def _parse_reminder(self, text: str) -> tuple:
        """Parse reminder text to extract message and time."""
        text_lower = text.lower()
        
        # Default time (1 hour from now)
        time = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
        
        # Try to extract time information
        if "tomorrow" in text_lower:
            time = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
            text = text_lower.replace("tomorrow", "").strip()
        elif "tonight" in text_lower:
            tonight = datetime.now().replace(hour=20, minute=0)
            time = tonight.strftime("%Y-%m-%d %H:%M")
            text = text_lower.replace("tonight", "").strip()
        elif "in" in text_lower and "hour" in text_lower:
            # Extract hours
            words = text_lower.split()
            for i, word in enumerate(words):
                if word == "in" and i + 1 < len(words):
                    try:
                        hours = int(words[i + 1])
                        time = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                        
        # Clean message
        message = text.replace("remind me to", "").replace("reminder to", "").strip()
        
        return message, time
        
    async def list_reminders(self, **kwargs) -> Dict[str, Any]:
        """List all reminders."""
        result = {
            "success": True,
            "response": f"You have {len(self.reminders)} reminders",
            "data": {"reminders": self.reminders}
        }
        return result
