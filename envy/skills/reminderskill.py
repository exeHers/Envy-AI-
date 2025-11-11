"""ReminderSkill - Set reminders and alarms."""
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path
import json


logger = logging.getLogger(__name__)


class ReminderSkill(BaseSkill):
    """Skill for setting reminders."""
    
    def execute(self, command: str) -> Dict[str, Any]:
        """Execute reminder command."""
        logger.info(f"ReminderSkill executing: {command}")
        
        # Extract reminder text
        reminder_match = re.search(r'remind\s+me\s+to\s+(.+?)(?:\s+at|\s+in|$)', command.lower())
        if not reminder_match:
            reminder_match = re.search(r'remind\s+me\s+(.+?)(?:\s+at|\s+in|$)', command.lower())
        
        reminder_text = reminder_match.group(1) if reminder_match else "Reminder"
        
        # Extract time
        time_match = re.search(r'at\s+(\d+)\s*(am|pm)?', command.lower())
        if not time_match:
            time_match = re.search(r'in\s+(\d+)\s*(minute|hour)', command.lower())
        
        reminder_time = None
        if time_match:
            if "at" in command.lower():
                hour = int(time_match.group(1))
                am_pm = time_match.group(2) if len(time_match.groups()) > 1 else None
                if am_pm == "pm" and hour != 12:
                    hour += 12
                elif am_pm == "am" and hour == 12:
                    hour = 0
                now = datetime.now()
                reminder_time = now.replace(hour=hour, minute=0, second=0)
                if reminder_time < now:
                    reminder_time += timedelta(days=1)
            else:
                # "in X minutes/hours"
                amount = int(time_match.group(1))
                unit = time_match.group(2) if len(time_match.groups()) > 1 else "minute"
                delta = timedelta(minutes=amount) if "minute" in unit else timedelta(hours=amount)
                reminder_time = datetime.now() + delta
        
        if not reminder_time:
            # Default to 1 hour from now
            reminder_time = datetime.now() + timedelta(hours=1)
        
        # Save reminder
        envy_dir = Path(__file__).parent.parent
        workspace_path = envy_dir / self.config.get("skills.sandbox.allowed_paths", ["workspace"])[0]
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        reminders_file = workspace_path / "reminders.json"
        reminders = []
        if reminders_file.exists():
            try:
                with open(reminders_file, 'r') as f:
                    reminders = json.load(f)
            except:
                reminders = []
        
        reminder_data = {
            "text": reminder_text,
            "time": reminder_time.isoformat(),
            "created": datetime.now().isoformat()
        }
        reminders.append(reminder_data)
        
        try:
            with open(reminders_file, 'w') as f:
                json.dump(reminders, f, indent=2)
            
            logger.info(f"Created reminder: {reminder_text} at {reminder_time}")
            return {
                "success": True,
                "response": f"I'll remind you to {reminder_text} at {reminder_time.strftime('%I:%M %p')}.",
                "data": reminder_data
            }
        except Exception as e:
            logger.error(f"Failed to save reminder: {e}")
            return {
                "success": False,
                "response": f"I encountered an error setting the reminder: {str(e)}",
                "data": {}
            }
