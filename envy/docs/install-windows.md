# Envy AI Assistant - Windows Installation Guide

Complete installation guide for running Envy on Windows 10/11, optimized for Intel i3 + GTX 1070.

---

## Prerequisites

### System Requirements

- **OS**: Windows 10 (build 1909+) or Windows 11
- **CPU**: Intel i3 or equivalent (2+ cores)
- **RAM**: 4GB minimum (8GB+ recommended)
- **GPU**: NVIDIA GTX 1070 (optional, for GPU acceleration)
- **Storage**: 5GB free space
- **Audio**: Working microphone and speakers

### Software Requirements

- Python 3.8+ (3.10+ recommended)
- Administrator privileges (for service installation)

---

## Step-by-Step Installation

### 1. Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run installer
3. **Important**: Check "Add Python to PATH"
4. Click "Install Now"
5. Verify installation:
   ```cmd
   python --version
   ```

### 2. Install Visual C++ Redistributable

Required for some Python packages:

Download and install: [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### 3. Run Envy Installer

1. Open Command Prompt or PowerShell
2. Navigate to envy directory:
   ```cmd
   cd C:\path\to\envy
   ```
3. Run installer:
   ```cmd
   install_envy.bat
   ```

The installer will:
- Verify Python installation
- Create virtual environment
- Install Python dependencies
- Download AI models
- Create run scripts

---

## GPU Acceleration (Optional)

If you have an NVIDIA GTX 1070 or similar GPU:

### 1. Install NVIDIA Drivers

1. Download from [NVIDIA website](https://www.nvidia.com/Download/index.aspx)
2. Install latest Game Ready or Studio driver
3. Verify installation:
   ```cmd
   nvidia-smi
   ```

### 2. Install CUDA Toolkit

1. Download [CUDA 12.2](https://developer.nvidia.com/cuda-downloads)
2. Run installer (custom installation)
3. Select CUDA toolkit components

### 3. Reinstall llama-cpp-python with CUDA

```cmd
cd envy
call venv\Scripts\activate.bat
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
pip install --force-reinstall llama-cpp-python
```

### 4. Update Configuration

Edit `config\envy.yaml`:

```yaml
resource_profile: "balanced"  # or "power"

profiles:
  balanced:
    use_gpu: true
    gpu_layers: 32

llm:
  local:
    gpu_layers: 32
```

---

## Audio Configuration

### Test Microphone

1. Right-click Speaker icon in taskbar
2. Select "Sound settings"
3. Test microphone under "Input"
4. Adjust volume and test

### Set Default Audio Device

1. Open Sound settings
2. Set default microphone under "Input"
3. Set default speakers under "Output"

### Fix Audio Issues

If audio doesn't work:

1. Update audio drivers from Device Manager
2. Check Privacy settings → Microphone
3. Allow apps to access microphone
4. Restart audio services:
   ```cmd
   net stop audiosrv
   net start audiosrv
   ```

---

## Running Envy

### Start Envy

Double-click `run_envy_local.bat` or run in Command Prompt:

```cmd
cd envy
run_envy_local.bat
```

To use specific profile:

```cmd
run_envy_local.bat balanced
run_envy_local.bat low
run_envy_local.bat power
```

### Test Installation

```cmd
cd envy
call venv\Scripts\activate.bat
python tests\test_code_skill.py
```

### Access Web Dashboard

Open browser: **http://localhost:8080**

---

## 24/7 Service Installation

To run Envy as a Windows service:

### 1. Download NSSM

1. Download NSSM from [nssm.cc](https://nssm.cc/download)
2. Extract `nssm.exe` to `C:\Windows\System32` or add to PATH

### 2. Install Service

```cmd
cd envy\installers
install_service_windows.bat
```

Run as Administrator.

### 3. Start Service

```cmd
net start Envy
```

Or use Services Manager:
1. Press Win+R
2. Type `services.msc`
3. Find "Envy AI Assistant"
4. Right-click → Start

### 4. Configure Service

Using NSSM GUI:

```cmd
nssm edit Envy
```

Set:
- Startup type: Automatic
- Log on: Your user account

### 5. Stop Service

```cmd
net stop Envy
```

### 6. Remove Service

```cmd
nssm remove Envy confirm
```

---

## Firewall Configuration

Allow web dashboard access:

### Windows Defender Firewall

1. Open Windows Defender Firewall
2. Click "Advanced settings"
3. Click "Inbound Rules" → "New Rule"
4. Select "Port" → Next
5. Enter port 8080 → Next
6. Allow the connection → Next
7. Apply to all profiles → Next
8. Name: "Envy Dashboard" → Finish

Or use Command Prompt (Admin):

```cmd
netsh advfirewall firewall add rule name="Envy Dashboard" dir=in action=allow protocol=TCP localport=8080
```

---

## Performance Tuning (Intel i3 + GTX 1070)

### Recommended Configuration

Edit `config\envy.yaml`:

```yaml
resource_profile: "balanced"

profiles:
  balanced:
    max_cpu_percent: 60
    max_memory_mb: 4096
    use_gpu: true
    stt_model: "faster-whisper-small"
    llm_model: "tinyllama-1.1b-q4"
    tts_engine: "pyttsx3"

llm:
  local:
    gpu_layers: 32  # With GTX 1070
    context_length: 2048
    max_tokens: 256
```

### Process Priority

Set high priority (optional):

```cmd
start /HIGH run_envy_local.bat
```

### Power Settings

1. Open Power Options
2. Select "High performance" plan
3. Ensure "USB selective suspend" is disabled

### GPU Monitoring

Monitor GPU usage:

```cmd
nvidia-smi -l 1
```

Or use NVIDIA Control Panel.

---

## Troubleshooting

### ImportError: DLL load failed

Install Visual C++ Redistributable:
- [VC++ 2015-2022 x64](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Python not found

1. Reinstall Python
2. Check "Add Python to PATH"
3. Or add manually:
   - Right-click "This PC" → Properties
   - Advanced system settings → Environment Variables
   - Add Python path to PATH

### pip command not found

```cmd
python -m pip install --upgrade pip
```

### Audio device not working

1. Check Device Manager for audio drivers
2. Update drivers
3. Check Windows Privacy settings
4. Allow apps to access microphone

### Models not downloading

Manual download:

```cmd
cd models

REM VOSK model
curl -L -o vosk-model.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
tar -xf vosk-model.zip

REM LLM model
curl -L -o tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### Port 8080 already in use

Edit `config\envy.yaml`:

```yaml
web_dashboard:
  port: 8081  # Or another port
```

### Service won't start

1. Check Event Viewer for errors
2. Run manually to debug:
   ```cmd
   cd C:\path\to\envy
   call venv\Scripts\activate.bat
   python envy_main.py
   ```

---

## Upgrading Models

### Upgrade to Larger LLM

```cmd
cd models
curl -L -o mistral-7b-instruct-v0.2.Q4_K_M.gguf https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

Update `config\envy.yaml`:

```yaml
llm:
  local:
    model_path: "./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
```

---

## Uninstallation

### 1. Stop Service (if installed)

```cmd
net stop Envy
nssm remove Envy confirm
```

### 2. Remove Files

Delete the envy folder.

### 3. Remove Python (optional)

1. Open "Apps & Features"
2. Find Python
3. Click Uninstall

---

## Security

### Windows Defender

Envy may trigger Windows Defender due to:
- Audio access
- System command execution
- File operations

Add exclusion:
1. Open Windows Security
2. Virus & threat protection → Manage settings
3. Add or remove exclusions → Add folder
4. Select envy folder

### User Account Control

Some operations may require UAC prompt:
- Service installation
- System settings changes

Always run installers as Administrator.

---

## Next Steps

- Customize `config\envy.yaml` for your needs
- Add custom skills in `skills\` directory
- Explore the web dashboard at http://localhost:8080
- Check out [Security Documentation](security.md)

---

**Questions? Check the [main README](../README.md) or create an issue.**
