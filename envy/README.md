# Envy Personal Assistant

A full-featured Jarvis-style personal assistant with voice activation, web dashboard, and 24/7 operation capabilities. Designed to run locally on modest hardware (Intel i3, GTX 1070, 16GB RAM) without requiring paid APIs.

## Quick Start

### One-Command Installer

**Linux:**
```bash
./install_envy.sh
```

**Windows:**
```cmd
install_envy.bat
```

### Run Envy

**Linux:**
```bash
./run_envy_local.sh
```

**Windows:**
```cmd
run_envy_local.bat
```

## Features

- **Wake Word Detection**: Always-listening "Envy" wake word using VOSK
- **Speech-to-Text**: Real-time transcription using VOSK (with optional Whisper support)
- **Text-to-Speech**: Natural voice output using pyttsx3
- **LLM Integration**: Local llama.cpp support with free remote fallback
- **Modular Skills**: Plugin-based skill system (CodeSkill, ResearchSkill, SysControlSkill, ReminderSkill)
- **Web Dashboard**: FastAPI-based dashboard for monitoring and manual commands
- **Resource Management**: Configurable CPU/GPU/memory limits
- **Security**: Sandboxed execution with confirmation requirements

## Architecture

Envy uses a microservice architecture:

- **Wake Listener**: Continuously listens for "Envy" wake word
- **STT Service**: Handles speech-to-text conversion
- **TTS Service**: Handles text-to-speech synthesis
- **LLM Adapter**: Manages local/remote LLM inference
- **Router**: Classifies intents and routes to skills
- **Skill Manager**: Executes modular skills
- **Web Dashboard**: Provides web interface for monitoring

## Configuration

Edit `config/envy.yaml` to customize:

- Resource profiles (low, balanced, power)
- Wake word sensitivity
- STT/TTS engines
- LLM provider (local/remote)
- Security settings
- Skill enablement

## Skills

### CodeSkill
Creates and modifies code files based on voice commands.

Example: "Envy, create test.py that prints hello"

### ResearchSkill
Performs research and information gathering.

Example: "Envy, research python programming"

### SysControlSkill
System control operations (requires explicit enablement).

Example: "Envy, open calculator"

### ReminderSkill
Sets reminders and alerts.

Example: "Envy, remind me to call John"

## Requirements

- Python 3.10+
- 16GB RAM (minimum)
- GTX 1070 (8GB VRAM) or equivalent (optional, for GPU acceleration)
- Linux or Windows

## Installation Details

See `docs/install-linux.md` and `docs/install-windows.md` for detailed installation instructions.

## Security

See `docs/security.md` for security documentation and sandboxing details.

## Troubleshooting

### Wake word not detected
- Check microphone permissions
- Adjust sensitivity in `config/envy.yaml`
- Ensure VOSK model is downloaded

### STT not working
- Verify VOSK model is present in `models/`
- Check audio device permissions
- Try different audio input device

### LLM not responding
- Check if local model is available (if using local provider)
- Enable remote fallback in config if local model unavailable
- Verify network connectivity for remote endpoints

## License

MIT License - see LICENSE file

## Contributing

This is a complete, self-contained project. All code is MIT licensed and generated for this project.
