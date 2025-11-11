# Installation Guide - Windows

Complete installation instructions for Envy on Windows 10/11.

## System Requirements

### Hardware
- **CPU**: Intel i3 or better (4+ cores recommended)
- **RAM**: 16GB minimum
- **GPU**: NVIDIA GTX 1070 (8GB VRAM) - optional but recommended
- **Storage**: 10GB free space
- **Audio**: Working microphone and speakers

### Software
- Windows 10 or Windows 11
- Python 3.10 or higher
- Microsoft Visual C++ 14.0 or greater

## Quick Installation

1. Download or clone Envy
2. Run `install_envy.bat`
3. Follow the prompts

## Detailed Installation

### 1. Install Python

Download Python 3.10+ from [python.org](https://www.python.org/downloads/)

**Important**: Check "Add Python to PATH" during installation!

Verify installation:
```cmd
python --version
pip --version
```

### 2. Install Visual C++ Build Tools

Some Python packages require compilation. Install:

[Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

Or install Visual Studio Community with "Desktop development with C++" workload.

### 3. Install Envy

Open Command Prompt or PowerShell:

```cmd
cd path\to\envy
install_envy.bat
```

The installer will:
- Create virtual environment
- Install Python dependencies
- Set up directories

### 4. Install GPU Support (Optional)

For NVIDIA GPU acceleration:

**Check GPU:**
```cmd
nvidia-smi
```

**Install CUDA Toolkit:**

Download from [NVIDIA CUDA Downloads](https://developer.nvidia.com/cuda-downloads)

Choose:
- Windows
- x86_64
- Your Windows version
- exe (local)

**Install CUDA-enabled llama-cpp-python:**

```cmd
call venv\Scripts\activate.bat
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

### 5. Download Models

Models can be downloaded manually or using the download script.

**Manual Download:**

1. **VOSK Model** (Required for wake word)
   - Download: https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
   - Extract to: `models\vosk-model-small-en-us-0.15\`

2. **Llama Model** (Optional for local LLM)
   - Download: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF
   - File: `llama-2-7b-chat.Q4_0.gguf`
   - Place in: `models\`

**Using Script (requires wget or curl):**
```cmd
scripts\download_models.bat
```

## Configuration

### 1. Edit Configuration

Open `config\envy.yaml` in a text editor:

```cmd
notepad config\envy.yaml
```

### 2. Optimize for Your Hardware

**For Intel i3 + GTX 1070:**

```yaml
system:
  profile: "balanced"

resources:
  max_cpu_percent: 50
  max_memory_mb: 4096
  gpu_enabled: true
  gpu_memory_fraction: 0.7

llm:
  local:
    enabled: true
    threads: 4
    gpu_layers: 20
```

**CPU-Only Mode:**
```yaml
resources:
  gpu_enabled: false

llm:
  local:
    threads: 4
    gpu_layers: 0
```

### 3. Configure Audio

Windows usually works out-of-the-box, but you may need to:

1. Open **Sound Settings**
2. Set default microphone
3. Test microphone in "Sound Control Panel"
4. Grant microphone permissions to Python

## Running Envy

### Using Quick-Start Script

Double-click `run_envy_local.bat` or:

```cmd
run_envy_local.bat
```

### Manual Start

```cmd
call venv\Scripts\activate.bat
python main.py
```

### With Options

```cmd
python main.py --profile balanced
python main.py --no-gui
```

### Web Dashboard

Once running, open browser to:
```
http://localhost:8080
```

## Install as Windows Service

To run Envy as a background service:

### 1. Install NSSM

Download NSSM from [nssm.cc](https://nssm.cc/download)

Extract `nssm.exe` to a folder in your PATH (e.g., `C:\Windows\System32`)

### 2. Install Service

Run as Administrator:

```cmd
scripts\install_service_windows.bat
```

### 3. Manage Service

**Using Command Prompt (Admin):**
```cmd
net start Envy
net stop Envy
sc query Envy
```

**Using Services Manager:**
1. Press Win+R
2. Type `services.msc`
3. Find "Envy Personal AI Assistant"
4. Right-click to start/stop

## Verification

Run tests to verify installation:

```cmd
call venv\Scripts\activate.bat
python tests\test_acceptance.py
```

Check results in `artifacts\tests\`.

## Troubleshooting

### Python Not Found

Make sure Python is in PATH:
1. Search "Environment Variables"
2. Edit System PATH
3. Add Python installation directory

### "Microsoft Visual C++ 14.0 required"

Install Visual C++ Build Tools (see step 2 above).

### "Could not find VOSK model"

Download and extract VOSK model to `models\` directory.

### Audio Permission Issues

Grant microphone access:
1. Settings → Privacy → Microphone
2. Enable microphone access
3. Allow desktop apps to access microphone

### GPU Not Detected

```cmd
# Check GPU
nvidia-smi

# Reinstall CUDA support
call venv\Scripts\activate.bat
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

### Port 8080 Already in Use

Change port in `config\envy.yaml`:
```yaml
web:
  port: 8081
```

### High CPU Usage

Reduce in config:
```yaml
system:
  profile: "low"

resources:
  max_cpu_percent: 30

llm:
  local:
    threads: 2
```

### Firewall Blocking

Windows Firewall may block the web dashboard:
1. Allow Python through Windows Firewall
2. Or add exception for port 8080

## Performance Tips

### For Intel i3 + GTX 1070

1. **Use Balanced Profile** - Good performance without overload
2. **Enable GPU** - Offload LLM to GPU (20 layers recommended)
3. **Limit CPU** - Keep max_cpu_percent at 50% to prevent freezing
4. **Use Quantized Models** - Q4_0 models are fast and fit in 8GB VRAM

### To Reduce Memory Usage

```yaml
llm:
  local:
    context_size: 1024  # Reduce from 2048
    gpu_layers: 15      # Reduce GPU layers
```

### To Increase Speed

```yaml
system:
  profile: "power"

llm:
  local:
    gpu_layers: 25
    threads: 6
```

## Uninstallation

1. Stop service (if installed):
   ```cmd
   sc stop Envy
   sc delete Envy
   ```

2. Delete Envy folder

3. (Optional) Uninstall Python packages:
   ```cmd
   rmdir /s venv
   ```

## Next Steps

- Read [Security Documentation](security.md)
- Learn about [Custom Skills](custom-skills.md)
- Check [Troubleshooting Guide](troubleshooting.md)

---

Need help? Check logs at `artifacts\logs\envy.log`
