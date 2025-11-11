# Windows Installation Guide

Complete installation guide for Envy on Windows 10/11, optimized for Intel i3 + GTX 1070.

## Prerequisites

### System Requirements
- OS: Windows 10 or Windows 11
- CPU: Intel i3 or equivalent (4 cores recommended)
- RAM: 8GB minimum, 16GB recommended
- GPU: GTX 1070 (8GB) or similar (optional but recommended)
- Storage: 10GB free space
- Audio: Working microphone and speakers

### Software Requirements

1. **Python 3.10+**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Microsoft Visual C++ Redistributable**
   - Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - Required for some Python packages

3. **CUDA Toolkit (for GPU acceleration)**
   - Download CUDA 11.8: https://developer.nvidia.com/cuda-11-8-0-download-archive
   - Select Windows > x86_64 > 11 > exe (local)
   - Install with default options

## Installation Steps

### 1. Extract Envy

```cmd
cd C:\workspace
unzip envy-ready.zip
cd envy
```

### 2. Run Installer

```cmd
installers\install_envy.bat
```

The installer will:
- Check Python version
- Create virtual environment
- Install dependencies
- Create run scripts

### 3. Download Models

Download models manually (Windows doesn't have wget/curl by default):

**VOSK Wake Word Model:**
1. Download: https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
2. Extract to: `C:\workspace\envy\models\vosk-model-small-en-us-0.15`

**LLM Model (Optional):**
1. Download from Hugging Face: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF
2. Download file: `llama-2-7b-chat.Q4_K_M.gguf` (~4GB)
3. Place in: `C:\workspace\envy\models\`

Or use PowerShell:
```powershell
# VOSK model
Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" -OutFile "models\vosk.zip"
Expand-Archive models\vosk.zip -DestinationPath models\
Remove-Item models\vosk.zip
```

### 4. Configure for Your Hardware

Edit `config\envy.yaml`:

#### For i3 + GTX 1070 (Recommended)

```yaml
profile: balanced

stt:
  device: "cuda"
  compute_type: "int8"
  model_size: "base"

llm:
  local:
    enabled: true
    n_threads: 4
    n_gpu_layers: 35  # Use GPU
```

#### For CPU-Only

```yaml
profile: low

stt:
  device: "cpu"
  compute_type: "int8"
  model_size: "tiny"

llm:
  local:
    enabled: true
    n_threads: 4
    n_gpu_layers: 0  # Disable GPU
```

## Running Envy

### Interactive Mode

Double-click `start-envy.bat` or run from command prompt:

```cmd
run_envy_local.bat --profile balanced
```

### As a Windows Service

Using NSSM (Non-Sucking Service Manager):

1. **Download NSSM:**
   - https://nssm.cc/download
   - Extract nssm.exe to a folder (e.g., `C:\nssm\`)

2. **Install Service:**
```cmd
cd C:\nssm
nssm install Envy "C:\workspace\envy\venv\Scripts\python.exe" "C:\workspace\envy\envy_main.py --profile balanced"
nssm set Envy AppDirectory "C:\workspace\envy"
nssm set Envy DisplayName "Envy Personal Assistant"
nssm set Envy Description "Jarvis-style personal assistant"
nssm set Envy Start SERVICE_AUTO_START
```

3. **Start Service:**
```cmd
nssm start Envy
```

4. **Check Status:**
```cmd
nssm status Envy
```

## GPU Setup (GTX 1070)

### Install CUDA Toolkit

1. Download CUDA 11.8: https://developer.nvidia.com/cuda-11-8-0-download-archive
2. Run installer, select:
   - CUDA Toolkit
   - Visual Studio Integration (if you have VS)
3. Verify installation:

```cmd
nvcc --version
nvidia-smi
```

### Install GPU-Accelerated Dependencies

Open Command Prompt as Administrator:

```cmd
cd C:\workspace\envy
venv\Scripts\activate

REM Reinstall llama-cpp-python with CUDA
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

## Troubleshooting

### Audio Issues

**Microphone not working:**
1. Settings > Privacy > Microphone
2. Enable "Allow apps to access your microphone"
3. Enable for Python

**Test audio:**
```python
import sounddevice
print(sounddevice.query_devices())
```

### Python Package Errors

```cmd
REM Upgrade pip
python -m pip install --upgrade pip

REM Install Visual C++ tools if needed
pip install --upgrade setuptools wheel
```

### VOSK Model Not Found

Ensure the model is extracted to:
```
C:\workspace\envy\models\vosk-model-small-en-us-0.15\
```

Should contain files like:
- am/final.mdl
- graph/Gr.fst
- conf/model.conf

### GPU Not Detected

```cmd
REM Check CUDA
nvidia-smi

REM Check in Python
python -c "import torch; print(torch.cuda.is_available())"

REM Verify CUDA environment variables
echo %CUDA_PATH%
REM Should be: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8
```

### Port 8080 Already in Use

Edit `config\envy.yaml`:
```yaml
web:
  port: 8081  # Change to different port
```

## Performance Tuning

### For i3 + GTX 1070

Optimal settings in `config\envy.yaml`:

```yaml
profile: balanced

resources:
  balanced:
    max_cpu_percent: 60
    max_memory_mb: 4096
    stt_model: "base"
    llm_threads: 4
    llm_gpu_layers: 35

llm:
  local:
    n_ctx: 2048
    n_threads: 4
    n_gpu_layers: 35  # Offload to GPU
    max_tokens: 512
```

Expected performance:
- Wake word: <300ms
- STT (5s audio): 500-1500ms
- LLM inference: 1-2s
- Total response: 2-4s

### Monitor Performance

**GPU:**
```cmd
nvidia-smi -l 1
```

**CPU/RAM:**
- Task Manager > Performance

## Firewall Configuration

Allow Python through Windows Firewall for web dashboard:

1. Control Panel > Windows Defender Firewall
2. Advanced Settings > Inbound Rules > New Rule
3. Program: `C:\workspace\envy\venv\Scripts\python.exe`
4. Allow the connection
5. Apply to all profiles

Or use command:
```cmd
netsh advfirewall firewall add rule name="Envy" dir=in action=allow program="C:\workspace\envy\venv\Scripts\python.exe" enable=yes
```

## Uninstallation

```cmd
REM Stop service (if installed)
nssm stop Envy
nssm remove Envy confirm

REM Delete Envy folder
rmdir /s /q C:\workspace\envy
```

## Next Steps

- Read [Configuration Reference](configuration.md)
- Learn about [Security](security.md)
- Create [Custom Skills](custom-skills.md)
- Access dashboard at http://127.0.0.1:8080
