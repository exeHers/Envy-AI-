# 🎤 Envy Personal Assistant

A full Jarvis-style personal assistant with voice interaction, web dashboard, and 24/7 service capabilities. Runs locally on your hardware with no required paid APIs.

## ✨ Features

- **Wake Word Detection**: Always-listening "Envy" wake word with minimal CPU usage
- **Speech-to-Text**: Streaming STT using VOSK models
- **Text-to-Speech**: Natural voice output using pyttsx3
- **Local AI**: On-device language models via llama.cpp (with optional remote fallback)
- **Modular Skills**:
  - 📝 **CodeSkill**: Create and manage code files by voice
  - 🔍 **ResearchSkill**: Research topics and generate summaries
  - ⚙️ **SysControlSkill**: Execute safe system commands
  - ⏰ **ReminderSkill**: Voice-activated reminders
- **Web Dashboard**: Monitor status, view logs, execute commands
- **24/7 Service**: Systemd (Linux) and Windows service support
- **Resource Profiles**: Low, balanced, and power modes for different hardware

## 🚀 Quick Start

### Installation (One Command)

**Linux:**
```bash
bash install_envy.sh
```

**Windows:**
```batch
install_envy.bat
```

### Running Envy

**Linux:**
```bash
./run_envy_local.sh
```

**Windows:**
```batch
run_envy_local.bat
```

**With custom profile:**
```bash
./run_envy_local.sh --profile power
```

## 📋 Requirements

### Minimum Hardware
- **CPU**: Intel i3 or equivalent
- **RAM**: 4GB (8GB recommended)
- **Storage**: 5GB free space
- **GPU**: Optional (GTX 1070 or similar for accelerated inference)

### Software
- Python 3.10 or higher
- Linux: portaudio, espeak
- Windows: No additional requirements

## 🎯 Acceptance Tests

All tests are automated and can be run with:

```bash
source venv/bin/activate  # Linux
# or
venv\Scripts\activate.bat  # Windows

python tests/run_tests.py
```

Tests verify:
- ✅ Wake word detection
- ✅ Speech-to-text pipeline
- ✅ Text-to-speech output
- ✅ LLM response or fallback
- ✅ CodeSkill: Voice-controlled file creation
- ✅ ResearchSkill: Topic research and summary generation

## 📖 Usage Examples

### Voice Commands

After wake word "Envy":

- **Code Creation**: "Create test.py that prints hello world"
- **Research**: "Research quantum computing"
- **System Control**: "Show uptime"
- **Reminders**: "Remind me to call mom tomorrow"

### Web Dashboard

Start the dashboard:
```bash
source venv/bin/activate
python web/dashboard.py
```

Access at: `http://localhost:8080`

Features:
- Manual command entry
- System status monitoring
- Log viewing
- File browser
- Configuration editing

## ⚙️ Configuration

Edit `config/envy.yaml` to customize:

- **Resource Profile**: `low`, `balanced`, or `power`
- **Models**: Paths to VOSK and LLM models
- **Skills**: Enable/disable specific skills
- **Security**: Whitelist commands, require confirmations
- **Persona**: Adjust voice personality

Example:
```yaml
profile: balanced

wake_word:
  keyword: "envy"
  sensitivity: 0.5

llm:
  local_enabled: true
  remote_enabled: false  # No paid APIs by default

skills:
  code_skill:
    enabled: true
    workspace_dir: "workspace"
```

## 🔧 Advanced Setup

### Installing as a Service

**Linux (systemd):**
```bash
sudo bash scripts/install_service.sh
sudo systemctl start envy
sudo systemctl status envy
```

**Windows (NSSM):**
1. Download NSSM from https://nssm.cc/download
2. Run: `install_service_windows.bat` (as Administrator)

### Upgrading Models

For better performance with more powerful hardware:

1. **Better STT**: Download larger VOSK models or use Whisper
2. **Better LLM**: Download Llama-2-7B or Mistral-7B quantized models
3. Update paths in `config/envy.yaml`

See `models/README.md` for details.

### GPU Acceleration

If you have an NVIDIA GPU:

1. Install CUDA toolkit
2. Install GPU-enabled llama-cpp-python:
   ```bash
   pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir --config-settings=cmake.args="-DLLAMA_CUBLAS=on"
   ```
3. Set `llm.local_gpu_layers` in config (try 10-20 for GTX 1070)

## 📚 Documentation

- [Linux Installation Guide](docs/install-linux.md)
- [Windows Installation Guide](docs/install-windows.md)
- [Security Guide](docs/security.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🔒 Security

- **Sandboxed Execution**: Skills run with restricted permissions
- **Command Whitelist**: System commands limited to safe operations
- **Confirmation Required**: Dangerous actions require explicit confirmation
- **No External Data**: All processing is local by default

See [Security Guide](docs/security.md) for details.

## 🧪 Testing & Performance

### Run All Tests
```bash
python tests/run_tests.py
```

### Generate Performance Report
```bash
python scripts/perf_report.py
```

Reports CPU, memory, and GPU usage during operation.

## 🛠️ Development

### Project Structure
```
envy/
├── services/          # Core services (wake, STT, TTS, router, LLM)
├── skills/            # Modular skill plugins
├── web/              # Web dashboard
├── config/           # Configuration files
├── tests/            # Automated tests
├── scripts/          # Utilities and installers
├── models/           # AI models (downloaded)
├── workspace/        # User files and outputs
└── artifacts/        # Logs and test results
```

### Adding Custom Skills

1. Create `skills/my_skill.py`:
```python
from skills.base_skill import BaseSkill

class MySkill(BaseSkill):
    def __init__(self):
        super().__init__("MySkill")
        self.actions = ['my_action']
    
    def execute(self, action, command, parameters):
        # Your logic here
        return self.success_response("Done!")
```

2. Skill is auto-loaded by SkillManager

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🤝 Contributing

This is a self-contained project generated for local use. Feel free to modify and extend as needed.

## ⚠️ Troubleshooting

### Audio Issues
- Linux: Install portaudio: `sudo apt-get install portaudio19-dev`
- Check microphone permissions
- Test with: `python -c "import sounddevice; print(sounddevice.query_devices())"`

### Model Issues
- Run `bash scripts/download_models.sh` to download models
- Check `models/` directory has required files
- Verify internet connection for downloads

### LLM Not Working
- Check if model file exists: `ls -lh models/*.gguf`
- Try disabling local LLM and using fallback mode
- Enable remote endpoint in config (optional)

### Performance Issues
- Switch to 'low' profile: `--profile low`
- Disable GPU layers if causing issues
- Close other applications
- Run performance report: `python scripts/perf_report.py`

For more help, see [docs/troubleshooting.md](docs/troubleshooting.md)

## 📞 Support

Generated by Cursor AI for local deployment. Customize as needed for your environment.

---

**Made with ❤️ for local AI enthusiasts**
