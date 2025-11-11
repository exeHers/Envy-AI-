# 🎤 Envy AI Assistant

**Full Jarvis-style personal assistant with voice interaction, web dashboard, and 24/7 operation.**

Envy is a complete, self-hosted AI assistant that runs locally on your machine. It features wake-word detection, speech-to-text, text-to-speech, natural language understanding, and a modular skill system—all without requiring paid API keys for core functionality.

---

## ✨ Features

- **🎙️ Voice Interaction**: Always-listening wake word ("Envy") with low CPU usage
- **🗣️ Speech Recognition**: Streaming STT using VOSK and Faster-Whisper
- **🔊 Text-to-Speech**: High-quality voice synthesis with pyttsx3/Coqui-TTS
- **🤖 Local LLM**: Runs quantized models locally (TinyLlama, Mistral) via llama.cpp
- **🔌 Modular Skills**: Plugin-based skill system (Code, Research, System, Reminders)
- **🌐 Web Dashboard**: Beautiful web interface for logs, config, and manual commands
- **🔒 Security**: Sandboxed execution with confirmation workflows for destructive actions
- **⚙️ Resource Profiles**: Low, balanced, and power modes for different hardware
- **📦 Easy Setup**: One-command installers for Linux and Windows
- **🆓 100% Free**: No paid APIs required, all local processing

---

## 🚀 Quick Start

### One-Command Installation (Linux)

```bash
cd envy
chmod +x install_envy.sh
./install_envy.sh --local-demo
```

### One-Command Installation (Windows)

```cmd
cd envy
install_envy.bat
```

### Run Envy

```bash
# Linux/Mac
./run_envy_local.sh

# Windows
run_envy_local.bat
```

### Access Web Dashboard

Open your browser to: **http://localhost:8080**

---

## 📋 Requirements

### Minimum Hardware

- **CPU**: Intel i3 or equivalent (2+ cores)
- **RAM**: 4GB (8GB recommended)
- **GPU**: Optional (GTX 1070 or better for faster inference)
- **Storage**: 5GB free space

### Tested Configuration

- **CPU**: Intel i3
- **GPU**: NVIDIA GTX 1070 (8GB)
- **RAM**: 16GB
- **OS**: Linux, Windows 10/11

### Software

- Python 3.8+ (3.10+ recommended)
- PortAudio (for audio capture)
- CUDA (optional, for GPU acceleration)

---

## 🛠️ Installation

### Detailed Installation (Linux)

1. **Clone or extract the repository**
   ```bash
   cd envy
   ```

2. **Run the installer**
   ```bash
   chmod +x install_envy.sh
   ./install_envy.sh
   ```

3. **The installer will**:
   - Check Python version
   - Install system dependencies (portaudio, ffmpeg, espeak)
   - Create virtual environment
   - Install Python packages
   - Download AI models (VOSK, TinyLlama)
   - Create run scripts

4. **Start Envy**
   ```bash
   ./run_envy_local.sh
   ```

### Detailed Installation (Windows)

1. **Install Python** from [python.org](https://python.org) (3.10+)
   - Make sure to check "Add Python to PATH"

2. **Run the installer**
   ```cmd
   install_envy.bat
   ```

3. **Start Envy**
   ```cmd
   run_envy_local.bat
   ```

---

## 💡 Usage

### Voice Commands

1. **Wake the assistant**: Say "**Envy**"
2. **Give your command**: After hearing the activation tone, speak your request
3. **Wait for response**: Envy will process and respond

### Example Commands

```
"Envy, create test.py that prints hello"
→ Creates workspace/test.py with print statement

"Envy, research Python programming"
→ Generates research summary in artifacts/research/

"Envy, remind me in 30 minutes to check the oven"
→ Sets up a reminder

"Envy, run echo hello world"
→ Executes whitelisted system command

"Envy, what is the capital of France?"
→ Answers using local LLM or fallback
```

### Web Dashboard Commands

1. Open **http://localhost:8080**
2. Type commands in the input box
3. View logs and system status
4. Manage confirmations for destructive actions

---

## ⚙️ Configuration

Edit `config/envy.yaml` to customize:

### Resource Profiles

```yaml
resource_profile: "balanced"  # low, balanced, power
```

- **Low**: Minimal CPU/GPU usage, best for background operation
- **Balanced**: Default, good for most systems (i3 + GTX 1070)
- **Power**: Maximum quality, requires more resources

### Wake Word Settings

```yaml
wake_word:
  keyword: "envy"
  sensitivity: 0.5  # 0.0 to 1.0
```

### LLM Settings

```yaml
llm:
  primary_backend: "local"  # local, remote, hybrid
  local:
    model_path: "./models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    gpu_layers: 10  # 0 for CPU-only
```

### Security

```yaml
security:
  require_voice_confirmation: true
  require_dashboard_confirmation: true
  sandbox_execution: true
```

---

## 🧩 Skills

Envy includes four core skills:

### 1. Code Skill
Creates and modifies code files safely.

**Commands**:
- "Create [filename] that [description]"
- "Write a Python script to [task]"

**Example**: "Create hello.py that prints hello world"

### 2. Research Skill
Researches topics and creates markdown summaries.

**Commands**:
- "Research [topic]"
- "Find information about [subject]"

**Example**: "Research machine learning"

### 3. System Control Skill
Executes safe system commands (whitelist mode).

**Commands**:
- "Run [command]"
- "Execute echo [message]"

**Example**: "Run uptime"

### 4. Reminder Skill
Sets and manages reminders.

**Commands**:
- "Remind me [when] to [task]"
- "List my reminders"

**Example**: "Remind me in 1 hour to call John"

---

## 🧪 Testing

### Run All Tests

```bash
cd envy
bash tests/run_all_tests.sh
```

### Run Individual Tests

```bash
python3 tests/test_code_skill.py
python3 tests/test_research_skill.py
python3 tests/test_llm.py
```

### Test Coverage

- ✅ Wake word detection
- ✅ Speech-to-text (STT)
- ✅ Text-to-speech (TTS)
- ✅ LLM adapter (local + fallback)
- ✅ CodeSkill end-to-end
- ✅ ResearchSkill end-to-end

---

## 🔧 Troubleshooting

### Audio Issues (Linux)

```bash
# Test microphone
arecord -d 5 test.wav
aplay test.wav

# Check ALSA devices
aplay -l
arecord -l

# Fix permissions
sudo usermod -a -G audio $USER
```

### Model Download Issues

Models are auto-downloaded on first run. If download fails:

```bash
# Manually download VOSK model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d models/

# Manually download LLM model
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf -O models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### GPU Not Detected

```bash
# Check CUDA installation
nvidia-smi

# Reinstall llama-cpp-python with CUDA support
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install --force-reinstall llama-cpp-python
```

### ImportError for Dependencies

```bash
# Reinstall all dependencies
pip install --force-reinstall -r requirements.txt
```

---

## 🌐 24/7 Operation

### Linux (systemd)

```bash
cd installers
sudo bash install_service_linux.sh
sudo systemctl enable envy@$USER
sudo systemctl start envy@$USER
```

### Windows (Service)

```cmd
cd installers
REM Download NSSM from https://nssm.cc/download
install_service_windows.bat
```

---

## 📊 Performance

Tested on Intel i3 + GTX 1070 + 16GB RAM:

| Metric | Value |
|--------|-------|
| Wake word latency | <100ms |
| STT latency | 1-3s |
| LLM inference | 2-5s (local) |
| TTS latency | 1-2s |
| Memory usage | 2-4GB |
| CPU usage (idle) | <5% |
| CPU usage (active) | 20-60% |

---

## 🔒 Security

### Sandboxing

All skill execution is sandboxed:
- File operations limited to workspace
- System commands whitelist-only by default
- Network access optional

### Confirmations

Destructive actions require:
1. Voice confirmation
2. Web dashboard confirmation

### Privacy

- **100% local processing** (no data sent to cloud)
- Optional remote LLM fallback (disabled by default)
- All data stays on your machine

---

## 📚 Documentation

- [Linux Installation Guide](docs/install-linux.md)
- [Windows Installation Guide](docs/install-windows.md)
- [Security Documentation](docs/security.md)
- [Configuration Reference](config/envy.yaml)

---

## 🤝 Contributing

Envy is open source under the MIT License. Contributions welcome!

### Adding New Skills

1. Create `skills/my_skill.py`
2. Inherit from `BaseSkill`
3. Implement `execute()` method
4. Add config entry in `config/envy.yaml`

See existing skills for examples.

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file

---

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] Voice cloning for TTS
- [ ] Advanced memory/context
- [ ] Mobile app
- [ ] Cloud sync (optional)
- [ ] Plugin marketplace

---

## 💬 Support

For issues, questions, or feature requests:
- Check the [troubleshooting](#-troubleshooting) section
- Review existing issues
- Create a new issue with details

---

## 🙏 Acknowledgments

Built with:
- [VOSK](https://alphacephei.com/vosk/) - Speech recognition
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - LLM inference
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) - Fast STT
- [pyttsx3](https://github.com/nateshmbhat/pyttsx3) - Text-to-speech
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework

---

**Made with ❤️ for the local-first AI community**
