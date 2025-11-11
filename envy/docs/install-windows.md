# Envy Installation Guide - Windows

Detailed installation instructions for Windows systems, optimized for Intel i3 + GTX 1070.

## Prerequisites

### System Requirements

- **OS**: Windows 10 or Windows 11
- **CPU**: Intel i3 or equivalent (2+ cores)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 5GB free space
- **GPU**: Optional - NVIDIA GTX 1070 or similar (for GPU acceleration)

### Required Software

1. **Python 3.10 or higher**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Verify: Open Command Prompt and type `python --version`

2. **Visual C++ Redistributable**
   - Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - Install if you get DLL errors

3. **Git** (optional, for cloning repository)
   - Download from: https://git-scm.com/download/win

## Installation Steps

### 1. Download Envy

```batch
REM If you have a zip file
REM Extract envy-ready.zip to C:\envy

REM Or clone from repository
git clone <repository-url> C:\envy
cd C:\envy
```

### 2. Run Installer

```batch
REM Right-click install_envy.bat and "Run as Administrator"
REM Or from Command Prompt:
install_envy.bat

REM This will:
REM - Create virtual environment
REM - Install Python dependencies
REM - Download AI models (~2.5GB)
REM - Set up directory structure
REM - Create run scripts
```

**Note**: Model download may take 10-30 minutes depending on your internet speed.

### 3. Verify Installation

```batch
REM Check that models were downloaded
dir models

REM Should see:
REM - vosk-model-small-en-us-0.15\
REM - vosk-model-en-us-0.22\
REM - tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### 4. Test Run

```batch
REM Activate virtual environment
venv\Scripts\activate.bat

REM Run tests
python tests\run_tests.py

REM Start Envy
run_envy_local.bat
```

## Hardware-Specific Configuration

### For Intel i3 (No GPU)

Use the **low** or **balanced** profile:

```batch
run_envy_local.bat --profile balanced
```

Edit `config\envy.yaml`:
```yaml
profile: balanced

resources:
  profiles:
    balanced:
      max_cpu_percent: 60
      max_memory_mb: 3072
      gpu_enabled: false

llm:
  local_threads: 4  # Match your CPU cores
  local_gpu_layers: 0  # CPU-only
```

### For Intel i3 + GTX 1070 (8GB VRAM)

Use the **balanced** or **power** profile with GPU acceleration:

```batch
run_envy_local.bat --profile power
```

Edit `config\envy.yaml`:
```yaml
profile: power

resources:
  profiles:
    power:
      max_cpu_percent: 80
      max_memory_mb: 6144
      gpu_enabled: true
      max_gpu_memory_mb: 4096

llm:
  local_threads: 4
  local_gpu_layers: 20  # Use GPU for LLM
```

### Enabling GPU Acceleration

1. **Install NVIDIA Drivers** (if not already installed):
   - Download from: https://www.nvidia.com/download/index.aspx
   - Select GTX 1070 and your OS
   - Install and reboot

2. **Install CUDA Toolkit** (optional, for GPU acceleration):
   - Download from: https://developer.nvidia.com/cuda-downloads
   - Install CUDA 11.8 or 12.x
   - Reboot after installation

3. **Install GPU-enabled llama-cpp-python**:
   ```batch
   venv\Scripts\activate.bat
   
   REM Uninstall CPU version
   pip uninstall llama-cpp-python
   
   REM Install GPU version (requires Visual Studio Build Tools)
   set CMAKE_ARGS=-DLLAMA_CUBLAS=on
   pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir
   ```

4. **Test GPU**:
   ```batch
   python -c "from llama_cpp import Llama; print('GPU support available')"
   ```

5. **Update config** to use GPU layers:
   ```yaml
   llm:
     local_gpu_layers: 20  # Start with 20, increase if stable
   ```

## Audio Configuration

### Test Microphone

```batch
REM List audio devices
python -c "import sounddevice; print(sounddevice.query_devices())"

REM Test recording
python -c "import sounddevice as sd; import soundfile as sf; rec = sd.rec(int(3*16000), samplerate=16000, channels=1); sd.wait(); sf.write('test.wav', rec, 16000); print('Saved test.wav')"
```

### Fix Audio Issues

1. **Check Windows Sound Settings**:
   - Right-click speaker icon in taskbar
   - Open "Sound settings"
   - Ensure correct microphone is selected
   - Set microphone level to 80-100%

2. **Install Audio Drivers**:
   - Update audio drivers via Device Manager
   - Or download from manufacturer website

3. **Fix Permissions**:
   - Settings → Privacy → Microphone
   - Enable "Allow apps to access your microphone"

## Service Installation

### Install as Windows service (using NSSM)

1. **Download NSSM**:
   - Download from: https://nssm.cc/download
   - Extract `nssm.exe` to `C:\Windows\System32\`

2. **Install service**:
   ```batch
   REM Run as Administrator
   install_service_windows.bat
   ```

3. **Manage service**:
   ```batch
   REM Start service
   nssm start Envy
   
   REM Stop service
   nssm stop Envy
   
   REM Check status
   nssm status Envy
   
   REM Remove service
   nssm remove Envy confirm
   ```

4. **View logs**:
   - Open Event Viewer
   - Windows Logs → Application
   - Filter by source "Envy"

### Alternative: Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
   - Name: "Envy Assistant"
   - Trigger: At system startup
   - Action: Start a program
   - Program: `C:\envy\venv\Scripts\python.exe`
   - Arguments: `C:\envy\envy_main.py --profile balanced --no-gui`
   - Start in: `C:\envy`
3. Properties → General → "Run whether user is logged on or not"

## Performance Tuning

### Power Options

For better performance:
1. Control Panel → Power Options
2. Select "High performance" plan
3. Or create custom plan with CPU at 100%

### Windows Defender

Add exclusions to improve performance:
1. Windows Security → Virus & threat protection
2. Manage settings → Add exclusion
3. Add folder: `C:\envy\`

### Monitor Performance

```batch
REM Generate performance report
venv\Scripts\activate.bat
python scripts\perf_report.py

REM Monitor real-time
REM Task Manager → Performance tab
REM GPU: Task Manager → Performance → GPU 0
```

## Troubleshooting

### Issue: Python not found

```batch
REM Check if Python is in PATH
python --version

REM If not found, add to PATH:
REM Control Panel → System → Advanced → Environment Variables
REM Edit PATH and add: C:\Users\<YourName>\AppData\Local\Programs\Python\Python310
```

### Issue: "ModuleNotFoundError"

```batch
REM Reinstall dependencies
venv\Scripts\activate.bat
pip install --upgrade -r requirements.txt
```

### Issue: Audio not working

```batch
REM Check microphone access
REM Settings → Privacy → Microphone → Allow

REM Reinstall audio library
pip uninstall sounddevice soundfile
pip install sounddevice soundfile pyaudio
```

### Issue: GPU not detected

```batch
REM Check NVIDIA driver
nvidia-smi

REM If command not found, install NVIDIA drivers
REM Download from: https://www.nvidia.com/download/index.aspx
```

### Issue: Out of memory

```batch
REM Use low profile
run_envy_local.bat --profile low

REM Close other applications
REM Increase virtual memory:
REM Control Panel → System → Advanced → Performance Settings → Advanced → Virtual Memory
```

### Issue: Model download fails

Manual download:
1. Create `models\` folder
2. Download files:
   - VOSK small: https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
   - VOSK medium: https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
   - TinyLlama: https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
3. Extract zip files to `models\` folder

### Issue: Firewall blocking

1. Windows Security → Firewall
2. Allow an app → Browse
3. Add: `C:\envy\venv\Scripts\python.exe`
4. Allow private and public networks

## Uninstallation

```batch
REM Stop service (if installed)
nssm stop Envy
nssm remove Envy confirm

REM Or remove from Task Scheduler

REM Delete folder
rmdir /s /q C:\envy
```

## Tips for Windows

1. **Run Command Prompt as Administrator** for installations
2. **Disable sleep mode** if running 24/7
3. **Use SSD** for better model loading performance
4. **Close browser** and other apps to free RAM
5. **Update Windows** for latest security patches

## Next Steps

1. **Test Envy**: Say "Envy" and give voice commands
2. **Access Dashboard**: Open http://localhost:8080
3. **Customize Config**: Edit `config\envy.yaml`
4. **Read Security Guide**: See `docs\security.md`
5. **Create Skills**: Add custom skills in `skills\`

## Useful Commands

```batch
REM Start Envy
run_envy_local.bat

REM Start with specific profile
run_envy_local.bat --profile power

REM Run tests
venv\Scripts\activate.bat
python tests\run_tests.py

REM Start web dashboard
venv\Scripts\activate.bat
python web\dashboard.py

REM Generate performance report
venv\Scripts\activate.bat
python scripts\perf_report.py

REM View logs
type logs\envy.log

REM Update Envy
git pull  # If using git
install_envy.bat  # Reinstall dependencies
```

---

For more help, see the main [README.md](../README.md) or check the logs in `logs\envy.log`.
