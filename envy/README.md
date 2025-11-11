# Envy Personal Assistant 🤖

A complete, locally-running Jarvis-style personal assistant with voice control, LLM integration, and modular skills.

## ✨ Features

- **Wake Word Detection**: Always-listening "Envy" keyword detection with minimal CPU usage
- **Speech-to-Text**: Streaming transcription using Whisper (quantized for efficiency)
- **Text-to-Speech**: Natural voice synthesis with pyttsx3
- **Local LLM**: Run models locally with llama.cpp (no paid APIs required)
- **Modular Skills**: Extensible plugin system for custom capabilities
  - **CodeSkill**: Create and edit code files via voice
  - **ResearchSkill**: Research topics and generate summaries
  - **SysControlSkill**: Execute safe system commands
  - **ReminderSkill**: Set and manage reminders
- **Web Dashboard**: Modern web interface for monitoring and control
- **24/7 Operation**: Run as a system service (systemd/Windows service)
- **Resource Profiles**: Optimized for different hardware (low/balanced/power)

## 🚀 Quick Start

### One-Command Installation

**Linux:**
```bash
cd envy
./installers/install_envy.sh
```

**Windows:**
```cmd
cd envy
installers\install_envy.bat
```

### Run Envy

```bash
./run_envy_local.sh --profile balanced
```

Or simply:
```bash
./start-envy.sh
```

The web dashboard will be available at http://127.0.0.1:8080

## 📋 Requirements

### Minimum Hardware
- CPU: Intel i3 or equivalent (4 cores recommended)
- RAM: 4GB (8GB+ recommended)
- GPU: Optional (GTX 1070 8GB or similar for faster inference)
- Storage: 10GB free space

### Software
- Python 3.10 or higher
- Linux or Windows
- Audio input/output devices
- (Optional) CUDA 11.x for GPU acceleration

## 🔧 Configuration

Edit `config/envy.yaml` to customize:

```yaml
profile: balanced  # low, balanced, or power

wake_word:
  keyword: "envy"
  sensitivity: 0.5

llm:
  local:
    enabled: true
    model_path: "models/llama-2-7b-chat.Q4_K_M.gguf"
    n_gpu_layers: 20  # Use GPU if available
```

### Resource Profiles

- **Low**: ~40% CPU, 2GB RAM (CPU-only, tiny models)
- **Balanced**: ~60% CPU, 4GB RAM (GPU optional, base models) *default*
- **Power**: ~80% CPU, 8GB RAM (GPU recommended, small models)

## 🎯 Usage

### Voice Commands

1. Say "Envy" to wake the assistant
2. Wait for acknowledgment ("Yes?")
3. Give your command

**Examples:**
- "Envy, create a file called hello.py that prints hello world"
- "Envy, research quantum computing"
- "Envy, remind me to call mom tomorrow"
- "Envy, run the date command"

### Web Dashboard

Access the dashboard at http://127.0.0.1:8080 to:
- View activity logs
- Send manual commands
- Monitor system status
- Confirm actions requiring permission

## 📦 Project Structure

```
envy/
├── services/          # Core services
│   ├── wake_listener.py
│   ├── stt_service.py
│   ├── tts_service.py
│   ├── llm_adapter.py
│   ├── router.py
│   └── skill_manager.py
├── skills/            # Modular skills
│   ├── code_skill.py
│   ├── research_skill.py
│   ├── sys_control_skill.py
│   └── reminder_skill.py
├── web/              # Web dashboard
│   └── dashboard.py
├── config/           # Configuration
│   └── envy.yaml
├── tests/            # Test suite
├── installers/       # Installation scripts
├── models/           # AI models
├── workspace/        # User workspace
└── envy_main.py      # Main entry point
```

## 🧪 Testing

Run the acceptance test suite:

```bash
source venv/bin/activate
pytest tests/test_acceptance.py -v
```

Or use the test script:
```bash
./tests/run_tests.sh
```

Tests verify:
- ✓ Wake word detection
- ✓ Speech-to-text pipeline
- ✓ Text-to-speech synthesis
- ✓ LLM inference or fallback
- ✓ CodeSkill creates files
- ✓ ResearchSkill generates summaries
- ✓ Router processes requests

## 🔒 Security

### Sandboxing
- System commands are whitelisted by default
- Destructive actions require voice + dashboard confirmation
- Skills run in isolated processes with timeouts

### Configuration
Edit `config/envy.yaml`:

```yaml
sys_control:
  whitelist_commands:
    - ls
    - pwd
    - date
  require_voice_confirmation: true
  require_dashboard_confirmation: true
```

See [docs/security.md](docs/security.md) for details.

## 📚 Documentation

- [Linux Installation Guide](docs/install-linux.md)
- [Windows Installation Guide](docs/install-windows.md)
- [Security Guide](docs/security.md)
- [Configuration Reference](docs/configuration.md)
- [Creating Custom Skills](docs/custom-skills.md)

## 🔄 Service Mode

### Linux (systemd)

```bash
sudo systemctl start envy
sudo systemctl enable envy  # Start on boot
sudo systemctl status envy
```

### Windows

Use `start-envy.bat` or install as a Windows service (see install guide).

## 🐛 Troubleshooting

### "VOSK model not found"
Run: `./installers/download_models.sh`

### "No LLM model available"
Edit `config/envy.yaml` and set:
```yaml
llm:
  remote:
    enabled: true  # Use fallback responses
```

### Audio issues
Check your audio devices:
```bash
python3 -c "import sounddevice; print(sounddevice.query_devices())"
```

### High CPU usage
Switch to "low" profile in config or use CPU-only mode:
```yaml
profile: low
llm:
  local:
    n_gpu_layers: 0  # Disable GPU
```

## 🤝 Contributing

Envy is MIT licensed. Contributions welcome!

To add a new skill:
1. Create `skills/my_skill.py`
2. Implement skill class with async methods
3. Add to `enabled_skills` in config
4. Restart Envy

See [docs/custom-skills.md](docs/custom-skills.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

Built with:
- [VOSK](https://alphacephei.com/vosk/) - Wake word detection
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper) - Speech recognition
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) - Text-to-speech
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Local LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework

## 📞 Support

For issues and questions, see the troubleshooting section or check configuration files.

---

**Envy** - Your local, privacy-focused personal assistant. No cloud required. ✨
