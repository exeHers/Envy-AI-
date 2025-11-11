# 🤖 ENVY - Personal AI Assistant

Full-featured voice-activated AI assistant that runs locally on your hardware. Built with privacy, performance, and modularity in mind.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- **🎤 Voice-Activated**: Always-listening wake word detection ("Envy")
- **💬 Natural Conversations**: Speech-to-text and text-to-speech
- **🧠 Local LLM**: Runs on your hardware (no cloud required)
- **🔌 Modular Skills**: Extensible plugin system
- **🌐 Web Dashboard**: Monitor and control via browser
- **🔒 Privacy-First**: All processing happens locally
- **⚡ Resource-Efficient**: Optimized for i3 CPU + GTX 1070 (8GB VRAM)

## 🚀 Quick Start

### One-Command Install

**Linux:**
```bash
chmod +x install_envy.sh && ./install_envy.sh
```

**Windows:**
```batch
install_envy.bat
```

### Run Envy

```bash
./run_envy_local.sh
```

That's it! Envy will start listening for the wake word "Envy" and the web dashboard will be available at http://localhost:8080

## 📋 Requirements

### Hardware
- **CPU**: Intel i3 or better (4+ cores recommended)
- **RAM**: 16GB (minimum 8GB)
- **GPU**: NVIDIA GTX 1070 (8GB VRAM) or similar (optional but recommended)
- **Storage**: 10GB free space

### Software
- **OS**: Linux (Ubuntu 20.04+), Windows 10/11
- **Python**: 3.10 or higher
- **Audio**: Working microphone and speakers

## 🎯 Core Skills

Envy comes with built-in skills:

### CodeSkill
Create files and write code via voice commands.

**Example**: "Envy, create test.py that prints hello"

### ResearchSkill
Research topics and generate summaries.

**Example**: "Envy, research quantum computing"

### ReminderSkill
Manage reminders and notifications.

**Example**: "Envy, remind me to take a break in 10 minutes"

### SysControlSkill
Execute system commands (disabled by default for security).

**Example**: "Envy, run uptime"

## 🏗️ Architecture

```
envy/
├── main.py              # Main entry point
├── config/              # Configuration files
├── services/            # Core services (STT, TTS, LLM, etc.)
├── skills/              # Skill plugins
├── web/                 # Web dashboard
├── tests/               # Automated tests
└── scripts/             # Installation and utility scripts
```

### Microservices
- **Wake Listener**: VOSK-based keyword detection
- **STT Service**: Faster-Whisper for speech recognition
- **TTS Service**: pyttsx3 for speech synthesis
- **LLM Adapter**: Local llama.cpp + optional remote fallback
- **Router**: Intent classification and skill dispatch
- **Skill Manager**: Plugin execution and sandboxing
- **Web Dashboard**: FastAPI + modern HTML/JS interface

## ⚙️ Configuration

Edit `config/envy.yaml` to customize Envy's behavior:

```yaml
system:
  profile: "balanced"  # Options: low, balanced, power

resources:
  max_cpu_percent: 50
  gpu_enabled: true

wake:
  keyword: "envy"
  sensitivity: 0.5

llm:
  primary: "local"  # Options: local, remote
```

### Performance Profiles

- **low**: Minimal resource usage, slower response
- **balanced**: Default, good balance of speed and resources
- **power**: Maximum performance, higher resource usage

## 🔒 Security

Envy is designed with security in mind:

- **Sandboxed Execution**: Skills run in isolated environments
- **Confirmation Required**: Destructive actions need approval
- **Command Whitelist**: System commands are restricted by default
- **No Cloud Required**: All processing happens locally

See [docs/security.md](docs/security.md) for details.

## 📚 Documentation

- [Installation Guide - Linux](docs/install-linux.md)
- [Installation Guide - Windows](docs/install-windows.md)
- [Security Documentation](docs/security.md)
- [Creating Custom Skills](docs/custom-skills.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🧪 Testing

Run automated acceptance tests:

```bash
./tests/run_tests.sh
```

Tests verify:
- ✅ Wake word detection
- ✅ STT pipeline
- ✅ TTS synthesis
- ✅ LLM responses
- ✅ CodeSkill (create files)
- ✅ ResearchSkill (generate summaries)

## 🔧 Advanced Usage

### Run as Service

**Linux (systemd):**
```bash
sudo ./scripts/install_service_linux.sh
sudo systemctl start envy
```

**Windows:**
```batch
# Run as administrator
scripts\install_service_windows.bat
```

### Download Models

```bash
./scripts/download_models.sh
```

This downloads:
- VOSK model for wake word detection
- Whisper models (auto-downloaded on first use)
- Optional: Llama-2-7B-Chat (quantized, ~3.8GB)

### Custom Configuration

```bash
python main.py --profile power --no-gui
```

Options:
- `--profile`: Performance profile (low/balanced/power)
- `--no-gui`: Run without web dashboard (headless mode)

## 🐛 Troubleshooting

### Audio Issues
```bash
# Test microphone
arecord -l

# Test speakers
speaker-test -t wav -c 2
```

### GPU Not Detected
```bash
# Check NVIDIA GPU
nvidia-smi

# Install CUDA toolkit if needed
```

### Model Download Failed
Models can be downloaded manually:
- VOSK: https://alphacephei.com/vosk/models
- Llama: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF

Place models in `models/` directory.

### Remote Fallback
If local LLM fails, enable remote fallback in config:
```yaml
llm:
  remote:
    enabled: true
    provider: "huggingface"
```

## 🤝 Contributing

Envy is open source! Contributions welcome.

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- [VOSK](https://alphacephei.com/vosk/) - Wake word detection
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - Speech recognition
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Local LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) - Text-to-speech

## 📬 Support

For issues and questions:
- Check [docs/troubleshooting.md](docs/troubleshooting.md)
- Open an issue on GitHub
- Review logs in `artifacts/logs/envy.log`

---

**Made with ❤️ by the Cursor AI community**
