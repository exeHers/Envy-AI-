# Envy - Personal Assistant

A full-featured Jarvis-style personal assistant with voice interaction, web dashboard, and 24/7 operation capabilities.

## Quick Start

### Linux/macOS
```bash
./install_envy.sh --local-demo
./run_envy_local.sh --profile balanced
```

### Windows
```cmd
install_envy.bat
run_envy_local.bat
```

## Features

- **Wake Word Detection**: Always-listening "Envy" wake word with minimal CPU usage
- **Speech-to-Text**: Streaming STT using Whisper or VOSK
- **Text-to-Speech**: Natural voice responses
- **Local LLM**: Runs entirely offline using quantized models (llama.cpp)
- **Modular Skills**: Plugin-based skill system
- **Web Dashboard**: Real-time monitoring and control
- **24/7 Operation**: Systemd/Windows service support
- **Resource Safe**: Configurable CPU/GPU limits for i3 + GTX 1070

## System Requirements

- **Minimum**: Intel i3, GTX 1070 (8GB), 16GB RAM
- **OS**: Linux (systemd) or Windows 10+
- **Python**: 3.10 or higher
- **CUDA**: Optional but recommended for GPU acceleration

## Installation

See detailed installation guides:
- [Linux Installation](docs/install-linux.md)
- [Windows Installation](docs/install-windows.md)

## Configuration

Edit `config/envy.yaml` to customize:
- Resource profiles (low, balanced, power)
- Model paths and sizes
- Skill enablement
- Security settings

## Skills

- **CodeSkill**: Create and edit code files
- **ResearchSkill**: Research topics and generate summaries
- **SysControlSkill**: Safe system control with confirmations
- **ReminderSkill**: Set and manage reminders

## Security

All destructive actions require:
1. Voice confirmation
2. Dashboard confirmation
3. Audit logging

See [Security Documentation](docs/security.md) for details.

## Troubleshooting

### Wake word not detected
- Check microphone permissions
- Adjust sensitivity in `config/envy.yaml`
- Verify VOSK model is downloaded

### High CPU/GPU usage
- Switch to "low" profile: `--profile low`
- Reduce model size in config
- Disable GPU acceleration

### LLM too slow
- Use quantized models (q4_0 or q4_1)
- Enable GPU layers if available
- Consider remote_free fallback (opt-in)

## Changing Models

### STT Model
Edit `config/envy.yaml` → `stt.model_size` (tiny/base/small/medium/large)

### LLM Model
1. Download quantized model to `models/`
2. Update `config/envy.yaml` → `llm.local.model_path`
3. Restart Envy

### TTS Voice
Edit `config/envy.yaml` → `tts.voice_id` (system-specific)

## License

MIT License - See LICENSE file for details.

## Support

Check `artifacts/envy.log` for detailed logs and error messages.
