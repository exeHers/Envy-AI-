# Envy - Personal Assistant

A full-featured Jarvis-style personal assistant with voice activation, web dashboard, and 24/7 operation capability. Designed to run locally on modest hardware (Intel i3, GTX 1070, 16GB RAM) without requiring paid APIs.

## Quick Start

### One-Command Install

**Linux/Mac:**
```bash
bash scripts/install_envy.sh --local-demo
./run_envy_local.sh
```

**Windows:**
```cmd
scripts\install_envy.bat --local-demo
run_envy_local.bat
```

### Run Tests

```bash
./scripts/run_tests.sh
```

## Features

- **Wake Word Detection**: Always-listening "Envy" wake word using VOSK
- **Speech-to-Text**: Whisper-based STT with streaming support
- **Text-to-Speech**: pyttsx3 TTS with multiple voice options
- **Local LLM**: llama.cpp integration for offline operation
- **Modular Skills**: Plugin-based skill system
- **Web Dashboard**: FastAPI-based dashboard for monitoring and control
- **Resource-Safe**: Configurable CPU/GPU limits for different hardware profiles

## Architecture

Envy uses a microservices architecture:

- **WakeListener**: Continuously listens for wake word
- **STTService**: Handles speech-to-text conversion
- **TTSService**: Handles text-to-speech synthesis
- **LLMAdapter**: Manages LLM inference (local or remote fallback)
- **Router**: Routes user requests to appropriate skills
- **SkillManager**: Loads and manages skills
- **WebDashboard**: Provides web interface

## Skills

### CodeSkill
Create and edit code files via voice commands.
```
"Envy, create test.py that prints hello"
```

### ResearchSkill
Research topics and generate summaries.
```
"Envy, research quantum computing"
```

### SysControlSkill
Execute system commands (with safety checks).
```
"Envy, run ls"
```

### ReminderSkill
Set reminders and alerts.
```
"Envy, remind me to call mom in 30 minutes"
```

## Configuration

Edit `config/envy.yaml` to customize:

- Resource profiles (low, balanced, power)
- Model paths and settings
- Skill enablement
- Security settings
- Web dashboard settings

## Hardware Requirements

**Minimum:**
- CPU: Intel i3 or equivalent
- RAM: 8GB
- Storage: 10GB free space
- Audio: Microphone and speakers

**Recommended:**
- CPU: Intel i5 or better
- GPU: NVIDIA GTX 1070 (8GB VRAM) or better
- RAM: 16GB
- Storage: 20GB free space

## Installation Details

See detailed installation guides:
- [Linux Installation](docs/install-linux.md)
- [Windows Installation](docs/install-windows.md)
- [Security Guide](docs/security.md)

## Troubleshooting

### Wake word not detected
- Check microphone permissions
- Adjust sensitivity in `config/envy.yaml`
- Ensure VOSK model is downloaded

### STT not working
- Verify Whisper model is downloaded (auto-downloads on first use)
- Check audio device configuration
- Review logs in `artifacts/envy.log`

### LLM too slow
- Use smaller quantized models (Q4_0 or Q4_1)
- Enable GPU acceleration if available
- Switch to remote fallback for testing

### Web dashboard not accessible
- Check firewall settings
- Verify port 8080 is available
- Review `config/envy.yaml` web settings

## Development

### Running Tests
```bash
./scripts/run_tests.sh
```

### Performance Report
```bash
./scripts/perf-report-gen.sh
```

### Adding Custom Skills

1. Create a new file in `skills/` directory
2. Inherit from `BaseSkill` class
3. Implement `execute()` method
4. Add skill name to `config/envy.yaml` enabled skills list

Example:
```python
from services.skill_manager import BaseSkill

class MySkill(BaseSkill):
    async def execute(self, user_text: str, context: dict) -> dict:
        # Your skill logic here
        return {'response': 'Done!', 'outputs': []}
```

## License

MIT License - See LICENSE file for details.

## Support

For issues and questions, check the logs in `artifacts/envy.log` and review the documentation in `docs/`.
