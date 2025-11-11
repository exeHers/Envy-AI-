# 🤖 ENVY - DEPLOYMENT GUIDE

## Package Contents

You have received **envy-ready.zip** containing the complete Envy Personal Assistant system.

## Quick Start

### 1. Extract Package

```bash
unzip envy-ready.zip
cd envy/
```

### 2. Install

**Linux:**
```bash
chmod +x install_envy.sh
./install_envy.sh
```

**Windows:**
```batch
install_envy.bat
```

### 3. Download Models (Required)

```bash
./scripts/download_models.sh
```

Or manually download:
- VOSK model: https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
- Extract to `models/` directory

### 4. Run

```bash
./run_envy_local.sh
```

Access dashboard at: **http://localhost:8080**

## Package Structure

```
envy/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── config/
│   └── envy.yaml          # Configuration file
├── services/              # Core services
│   ├── wake_listener.py   # Wake word detection
│   ├── stt_service.py     # Speech-to-text
│   ├── tts_service.py     # Text-to-speech
│   ├── llm_adapter.py     # Language model
│   ├── router.py          # Command routing
│   └── skill_manager.py   # Skill execution
├── skills/                # Skill plugins
│   ├── code_skill.py      # Create files via voice
│   ├── research_skill.py  # Research summaries
│   ├── sys_control_skill.py # System commands (disabled)
│   └── reminder_skill.py  # Manage reminders
├── web/                   # Web dashboard
│   ├── dashboard.py       # FastAPI backend
│   └── templates/         # Frontend HTML
├── tests/                 # Automated tests
│   ├── test_acceptance.py # Acceptance test suite
│   └── run_tests.sh       # Test runner
├── scripts/               # Utility scripts
│   ├── download_models.sh # Model downloader
│   ├── install_service_linux.sh
│   └── install_service_windows.bat
├── docs/                  # Documentation
│   ├── install-linux.md
│   ├── install-windows.md
│   ├── security.md
│   ├── troubleshooting.md
│   └── custom-skills.md
├── install_envy.sh        # Linux installer
├── install_envy.bat       # Windows installer
├── run_envy_local.sh      # Quick start (Linux)
├── run_envy_local.bat     # Quick start (Windows)
├── LICENSE                # MIT License
└── README.md              # Project overview
```

## System Requirements

### Hardware
- **CPU**: Intel i3 or better (tested on i3)
- **RAM**: 16GB (minimum 8GB)
- **GPU**: NVIDIA GTX 1070 (8GB VRAM) or similar - optional but recommended
- **Storage**: 10GB free space

### Software
- **OS**: Linux (Ubuntu 20.04+) or Windows 10/11
- **Python**: 3.10 or higher
- **Audio**: Working microphone and speakers

## Configuration for Your Hardware

Edit `config/envy.yaml`:

```yaml
system:
  profile: "balanced"  # Options: low, balanced, power

resources:
  max_cpu_percent: 50
  max_memory_mb: 4096
  gpu_enabled: true
  gpu_memory_fraction: 0.7

llm:
  local:
    threads: 4
    gpu_layers: 20  # Adjust for your VRAM
```

### For Intel i3 + GTX 1070

The default "balanced" profile is optimized for this setup:
- Uses up to 50% CPU (prevents system freeze)
- Allocates 4GB RAM max
- Offloads 20 LLM layers to GPU
- Total VRAM usage: ~4-6GB (fits in 8GB)

### If No GPU

```yaml
resources:
  gpu_enabled: false

llm:
  local:
    gpu_layers: 0
```

## Running Tests

Verify installation:

```bash
./tests/run_tests.sh
```

All 6 acceptance tests should pass.

## Optional: Install as Service

### Linux (24/7 Background Service)

```bash
sudo ./scripts/install_service_linux.sh
sudo systemctl start envy
sudo systemctl status envy
```

### Windows (Background Service)

1. Install NSSM: https://nssm.cc/download
2. Run as administrator:
   ```batch
   scripts\install_service_windows.bat
   ```

## Using Envy

1. **Wake Word**: Say "Envy" to activate
2. **Voice Commands**:
   - "Envy, create test.py that prints hello"
   - "Envy, research quantum computing"
   - "Envy, remind me to take a break in 10 minutes"
3. **Web Dashboard**: Open http://localhost:8080
4. **Manual Commands**: Type commands in dashboard

## Troubleshooting

### Models Not Found

Run model download script:
```bash
./scripts/download_models.sh
```

Or enable remote LLM fallback in `config/envy.yaml`:
```yaml
llm:
  remote:
    enabled: true
```

### Audio Issues

**Linux:**
```bash
# Check microphone
arecord -l

# Test microphone
arecord -d 5 test.wav && aplay test.wav
```

**Windows:**
- Check microphone in Sound Settings
- Grant microphone permissions to Python

### High CPU Usage

Reduce resource usage:
```yaml
system:
  profile: "low"

resources:
  max_cpu_percent: 30

llm:
  local:
    threads: 2
```

### GPU Not Detected

```bash
# Check GPU
nvidia-smi

# Reinstall with CUDA support
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

## Documentation

- **README.md**: Project overview
- **docs/install-linux.md**: Detailed Linux installation
- **docs/install-windows.md**: Detailed Windows installation
- **docs/security.md**: Security features and best practices
- **docs/troubleshooting.md**: Common issues and solutions
- **docs/custom-skills.md**: Create your own skills

## Support

1. Check logs: `artifacts/logs/envy.log`
2. Read troubleshooting guide: `docs/troubleshooting.md`
3. Generate performance report: `./artifacts/perf-report-gen.sh`

## Key Features

✅ **100% Local Processing** - No cloud required (by default)
✅ **Free to Use** - No API keys needed for core functionality
✅ **Modular Skills** - Easy to extend with plugins
✅ **Resource Efficient** - Optimized for modest hardware
✅ **Secure** - Sandboxed execution, confirmation for dangerous actions
✅ **Web Dashboard** - Monitor and control via browser
✅ **24/7 Service** - Run as background service
✅ **Cross-Platform** - Linux and Windows support

## What's Included

- ✅ Complete source code (MIT License)
- ✅ Installers for Linux and Windows
- ✅ Service wrappers (systemd + Windows service)
- ✅ Automated acceptance tests
- ✅ Comprehensive documentation (6 guides)
- ✅ 4 skill plugins (Code, Research, SysControl, Reminder)
- ✅ Web dashboard with REST API
- ✅ Configuration system with 3 profiles
- ✅ Model download scripts
- ✅ Performance monitoring tools

## What You Need to Download

Due to size constraints, these are not included in the ZIP:

1. **VOSK Model** (~40MB) - Required for wake word
   - Download: https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
   - Or run: `./scripts/download_models.sh`

2. **Whisper Models** - Auto-downloaded on first use
   - Base model: ~140MB
   - Downloads automatically when needed

3. **LLM Model** (~3.8GB) - Optional for local LLM
   - Download: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF
   - File: `llama-2-7b-chat.Q4_0.gguf`
   - Or use remote fallback (free Hugging Face API)

## Performance Expectations

### Latency (Typical)
- Wake word detection: ~100-200ms
- Speech recognition: ~1-3s
- LLM inference: ~2-10s
- Speech synthesis: ~0.5-1s
- **Total wake-to-response: ~4-15s**

### Resource Usage (Peak)
- CPU: 50-70%
- RAM: 8-10GB
- VRAM: 4-6GB (if GPU enabled)

## License

MIT License - Free and open source. See LICENSE file.

## Build Info

- **Version**: 1.0.0
- **Built**: 2025-11-11
- **Built By**: Cursor AI Agent
- **Lines of Code**: 3500+ Python, 500+ HTML/CSS/JS
- **Files**: 40+ source files
- **Tests**: 6 automated acceptance tests

---

**🎉 Envy is ready to use! Start with `./run_envy_local.sh` and say "Envy" to activate.**

For detailed instructions, read **README.md** and the guides in **docs/**.
