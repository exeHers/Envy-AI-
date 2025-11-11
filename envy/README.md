# Envy - Personal Assistant

A full-featured Jarvis-style personal assistant that runs locally on your machine. Voice-activated, web-enabled, and designed to run 24/7.

## Quick Start

```bash
# Linux/Mac
./install_envy.sh --local-demo

# Windows
install_envy.bat --local-demo
```

Then run:
```bash
./run_envy_local.sh --profile balanced
```

## Features

- 🎤 **Voice Activation**: Wake word "Envy" with continuous listening
- 🗣️ **Speech-to-Text**: Real-time transcription using Whisper
- 💬 **Text-to-Speech**: Natural voice responses
- 🧠 **Local LLM**: Runs entirely offline using quantized models
- 🌐 **Web Dashboard**: Monitor and control via browser
- 🔌 **Modular Skills**: Extensible plugin system
- 🔒 **Security**: Sandboxed execution with confirmation flows

## System Requirements

- **Minimum**: Intel i3, 16GB RAM, 8GB VRAM (GTX 1070)
- **OS**: Linux (systemd) or Windows
- **Python**: 3.10+

## Installation

### Linux

```bash
chmod +x install_envy.sh
./install_envy.sh --local-demo
```

### Windows

```cmd
install_envy.bat --local-demo
```

## Usage

### Start Envy

```bash
# Balanced mode (recommended)
./run_envy_local.sh --profile balanced

# Low resource mode
./run_envy_local.sh --profile low

# Power mode (uses more resources)
./run_envy_local.sh --profile power
```

### Web Dashboard

Open your browser to: http://127.0.0.1:8080

### Voice Commands

Say "Envy" followed by your command:
- "Envy, create test.py that prints hello"
- "Envy, research quantum computing"
- "Envy, remind me to call mom at 3pm"

## Configuration

Edit `config/envy.yaml` to customize:
- Resource limits
- Model paths
- Skill settings
- Security options

## Skills

Built-in skills:
- **CodeSkill**: Create and edit files
- **ResearchSkill**: Web research and summaries
- **SysControlSkill**: System control (requires confirmation)
- **ReminderSkill**: Set reminders and alarms

Add custom skills by placing Python modules in `skills/`.

## Troubleshooting

### Wake word not detected
- Check microphone permissions
- Adjust sensitivity in `config/envy.yaml`
- Ensure VOSK model is downloaded

### High CPU/GPU usage
- Switch to `low` profile
- Reduce model size in config
- Disable GPU acceleration

### LLM too slow
- Use quantized models (q4_0)
- Enable remote free fallback (opt-in)
- Reduce context size

## Changing Models

### STT Model
Edit `config/envy.yaml`:
```yaml
stt:
  model: "base"  # Change to tiny/base/small/medium
```

### LLM Model
1. Download quantized model to `models/`
2. Update `config/envy.yaml`:
```yaml
llm:
  local:
    model_path: "models/your-model.gguf"
```

## Security

- All system commands require confirmation
- File operations are sandboxed
- Dangerous actions require voice + dashboard confirmation

See `docs/security.md` for details.

## License

MIT License - See LICENSE file

## Support

For issues and questions, check:
- `docs/install-linux.md`
- `docs/install-windows.md`
- `docs/security.md`
