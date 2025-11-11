# Creating Custom Skills

Learn how to extend Envy with custom skills.

## Overview

Envy uses a modular skill system where skills are Python classes that inherit from `BaseSkill`. Skills are automatically loaded from the `skills/` directory.

## Skill Structure

### Basic Template

```python
"""
My Custom Skill
Brief description
MIT License
"""

import logging
from pathlib import Path
import sys

# Import base skill
sys.path.insert(0, str(Path(__file__).parent))
from __init__ import BaseSkill

# Import config if needed
sys.path.insert(0, str(Path(__file__).parent.parent))
from services.config_manager import get_config

logger = logging.getLogger(__name__)


class MySkill(BaseSkill):
    """Custom skill description"""
    
    def __init__(self):
        super().__init__()
        self.config = get_config()
        # Initialize your skill here
        
        logger.info("MySkill initialized")
    
    def execute(self, command: str) -> str:
        """
        Execute the skill with the given command
        
        Args:
            command: Voice command from user
            
        Returns:
            Response text to speak back to user
        """
        try:
            # Your skill logic here
            logger.info(f"Executing MySkill with: {command}")
            
            # Do something with the command
            result = self.process_command(command)
            
            return f"MySkill completed: {result}"
            
        except Exception as e:
            logger.error(f"MySkill failed: {e}")
            return f"MySkill encountered an error: {str(e)}"
    
    def process_command(self, command: str):
        """Your custom logic"""
        # Implement your functionality
        return "result"
    
    def requires_confirmation(self) -> bool:
        """Whether this skill requires user confirmation"""
        return False  # Set to True for dangerous operations
    
    def get_description(self) -> str:
        """Get skill description"""
        return "This is my custom skill"
```

### File Naming

Skills must follow naming conventions:

- **Class name**: `CamelCase` (e.g., `MySkill`, `WeatherSkill`)
- **File name**: `snake_case` (e.g., `my_skill.py`, `weather_skill.py`)

Example:
- Class: `WeatherSkill`
- File: `skills/weather_skill.py`

## Skill Methods

### Required Methods

#### `__init__(self)`

Initialize your skill:

```python
def __init__(self):
    super().__init__()
    self.config = get_config()
    # Load resources, initialize APIs, etc.
```

#### `execute(self, command: str) -> str`

Main execution method:

```python
def execute(self, command: str) -> str:
    """
    Process user command and return response
    
    Args:
        command: Raw voice command from user
        
    Returns:
        Text response to speak back
    """
    # Your logic here
    return "Response text"
```

### Optional Methods

#### `requires_confirmation(self) -> bool`

Indicate if skill needs user approval:

```python
def requires_confirmation(self) -> bool:
    return True  # Require confirmation for this skill
```

#### `get_description(self) -> str`

Provide skill description:

```python
def get_description(self) -> str:
    return "Checks the weather forecast"
```

## Example Skills

### Simple Echo Skill

```python
"""
Echo Skill - Repeats back what user says
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from __init__ import BaseSkill


class EchoSkill(BaseSkill):
    """Echoes back user input"""
    
    def execute(self, command: str) -> str:
        # Simply repeat the command
        return f"You said: {command}"
    
    def get_description(self) -> str:
        return "Repeats back what you say"
```

### Calculator Skill

```python
"""
Calculator Skill - Performs basic math
"""

import re
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from __init__ import BaseSkill

logger = logging.getLogger(__name__)


class CalculatorSkill(BaseSkill):
    """Performs basic calculations"""
    
    def execute(self, command: str) -> str:
        try:
            # Extract math expression
            expression = self.extract_math(command)
            
            if not expression:
                return "I couldn't find a math expression to calculate."
            
            # Evaluate safely
            result = self.safe_eval(expression)
            
            return f"The answer is {result}"
            
        except Exception as e:
            logger.error(f"Calculator error: {e}")
            return "I couldn't calculate that."
    
    def extract_math(self, command: str):
        """Extract math expression from command"""
        # Remove common words
        command = command.lower()
        command = command.replace("what is", "")
        command = command.replace("calculate", "")
        command = command.replace("compute", "")
        
        # Find math pattern
        pattern = r'[\d\+\-\*/\(\)\s]+'
        match = re.search(pattern, command)
        
        if match:
            return match.group(0).strip()
        
        return None
    
    def safe_eval(self, expression: str):
        """Safely evaluate math expression"""
        # Whitelist safe characters
        if not re.match(r'^[\d\+\-\*/\(\)\s\.]+$', expression):
            raise ValueError("Invalid expression")
        
        # Evaluate
        return eval(expression)
    
    def get_description(self) -> str:
        return "Performs basic math calculations"
```

### API Integration Skill

```python
"""
Weather Skill - Fetches weather information
"""

import requests
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from __init__ import BaseSkill

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.config_manager import get_config

logger = logging.getLogger(__name__)


class WeatherSkill(BaseSkill):
    """Gets weather information"""
    
    def __init__(self):
        super().__init__()
        self.config = get_config()
        
        # Get API key from config
        self.api_key = self.config.get('skills.weather.api_key', '')
        self.location = self.config.get('skills.weather.default_location', 'London')
    
    def execute(self, command: str) -> str:
        try:
            # Extract location from command
            location = self.extract_location(command) or self.location
            
            # Fetch weather
            weather = self.get_weather(location)
            
            if weather:
                temp = weather['temp']
                desc = weather['description']
                return f"The weather in {location} is {desc} with a temperature of {temp} degrees."
            else:
                return "I couldn't fetch the weather information."
                
        except Exception as e:
            logger.error(f"Weather skill error: {e}")
            return "Weather information is not available right now."
    
    def extract_location(self, command: str):
        """Extract location from command"""
        command_lower = command.lower()
        
        if " in " in command_lower:
            parts = command_lower.split(" in ")
            if len(parts) > 1:
                return parts[1].strip()
        
        return None
    
    def get_weather(self, location: str):
        """Fetch weather from API"""
        if not self.api_key:
            logger.warning("No weather API key configured")
            return None
        
        # Example using OpenWeatherMap API (free tier)
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': location,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'temp': data['main']['temp'],
                    'description': data['weather'][0]['description']
                }
        except Exception as e:
            logger.error(f"Weather API error: {e}")
        
        return None
    
    def get_description(self) -> str:
        return "Provides weather information for locations"
```

## Configuration

Add skill configuration to `config/envy.yaml`:

```yaml
skills:
  enabled:
    - CodeSkill
    - ResearchSkill
    - MySkill  # Add your skill here
  
  # Skill-specific config
  my_skill:
    setting1: "value1"
    setting2: 42
```

Access in skill:

```python
def __init__(self):
    super().__init__()
    self.config = get_config()
    self.my_setting = self.config.get('skills.my_skill.setting1', 'default')
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
def execute(self, command: str) -> str:
    try:
        result = self.risky_operation(command)
        return f"Success: {result}"
    except Exception as e:
        logger.error(f"Skill error: {e}")
        return "I encountered an error processing that request."
```

### 2. Logging

Use logging for debugging:

```python
import logging
logger = logging.getLogger(__name__)

# In your skill
logger.info("Skill executing...")
logger.debug(f"Command details: {command}")
logger.error(f"Error occurred: {e}")
```

### 3. Timeouts

Long operations should have timeouts:

```python
import requests

def fetch_data(self):
    response = requests.get(url, timeout=5)  # 5 second timeout
```

### 4. Resource Cleanup

Clean up resources:

```python
def execute(self, command: str) -> str:
    file = None
    try:
        file = open("temp.txt", "w")
        # Use file
    finally:
        if file:
            file.close()
```

### 5. Security

Be cautious with user input:

```python
# DON'T do this
eval(command)  # Dangerous!
os.system(command)  # Dangerous!

# DO this
# Validate and sanitize input
if self.is_safe_input(command):
    # Process
```

## Testing Your Skill

Create a test file `tests/test_my_skill.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.my_skill import MySkill

def test_my_skill():
    skill = MySkill()
    result = skill.execute("test command")
    print(f"Result: {result}")
    assert result is not None

if __name__ == "__main__":
    test_my_skill()
    print("Test passed!")
```

Run it:

```bash
python tests/test_my_skill.py
```

## Registering Your Skill

1. **Create skill file**: `skills/my_skill.py`
2. **Enable in config**:
   ```yaml
   skills:
     enabled:
       - MySkill
   ```
3. **Restart Envy**

Skills are auto-loaded on startup!

## Advanced Features

### Using External Libraries

Install in requirements and import:

```python
# In your skill
import numpy as np
import pandas as pd

def process_data(self):
    data = np.array([1, 2, 3])
    # Process...
```

### State Management

Maintain state between calls:

```python
class StatefulSkill(BaseSkill):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.history = []
    
    def execute(self, command: str) -> str:
        self.counter += 1
        self.history.append(command)
        return f"Call number {self.counter}"
```

### Async Operations

For long-running tasks:

```python
import threading

def execute(self, command: str) -> str:
    # Start background task
    thread = threading.Thread(target=self.long_task, args=(command,))
    thread.start()
    
    return "Task started in background"

def long_task(self, command):
    # Do something that takes time
    pass
```

### File I/O

Read and write files:

```python
from pathlib import Path

def save_data(self, data):
    output_dir = Path(__file__).parent.parent / "artifacts" / "my_skill"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "output.txt", "w") as f:
        f.write(data)
```

## Skill Ideas

- **News Skill**: Fetch and summarize news
- **Music Skill**: Control music playback
- **Timer Skill**: Set timers and alarms
- **Note Skill**: Take and retrieve notes
- **Email Skill**: Send emails
- **Calendar Skill**: Manage calendar events
- **Translation Skill**: Translate text
- **Dictionary Skill**: Define words
- **Joke Skill**: Tell jokes
- **Quote Skill**: Provide inspirational quotes

## Troubleshooting

### Skill Not Loading

1. Check file name matches class name convention
2. Verify skill is enabled in config
3. Check logs: `cat artifacts/logs/envy.log | grep MySkill`
4. Test skill independently

### Skill Timing Out

Increase timeout in config:

```yaml
skills:
  timeout: 120  # 2 minutes
```

### Import Errors

Ensure paths are correct:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from __init__ import BaseSkill
```

---

**Happy skill building! Share your skills with the Envy community!**
