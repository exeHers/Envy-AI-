# Installing Envy on Windows

This guide covers installation on Windows systems, optimized for Intel i3 processors with GTX 1070 GPUs.

## Prerequisites

- Windows 10 or later
- Python 3.10 or higher
- 16GB RAM minimum
- GTX 1070 (8GB VRAM) - optional but recommended
- Internet connection for initial setup

## Step 1: Install Python

1. Download Python 3.10+ from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Verify installation:
```cmd
python --version
```

## Step 2: Install System Dependencies

### Audio Support:
- Windows should have audio drivers pre-installed
- Ensure microphone is connected and working
- Test microphone in Windows Sound Settings

### For GPU Support (CUDA):
1. Download CUDA Toolkit from [NVIDIA](https://developer.nvidia.com/cuda-downloads)
2. Install following NVIDIA's instructions
3. Verify installation:
```cmd
nvcc --version
```

## Step 3: Run Installer

Open Command Prompt or PowerShell in the envy directory:

```cmd
cd envy
install_envy.bat
```

The installer will:
- Create a Python virtual environment
- Install all Python dependencies
- Download the VOSK model (if not present)
- Create necessary directories

## Step 4: Configure (Optional)

Edit `config/envy.yaml` to customize:

- **Profile**: Set to `low`, `balanced`, or `power`
- **GPU**: Enable GPU acceleration if CUDA is installed
- **Wake Word**: Adjust sensitivity if needed

## Step 5: Run Envy

### Manual Run:
```cmd
run_envy_local.bat
```

### With Profile:
Edit `run_envy_local.bat` and modify the PROFILE variable, or run:
```cmd
python main.py --profile balanced
```

### Headless (no web dashboard):
```cmd
python main.py --no-gui
```

## GPU Acceleration (Optional)

### For llama.cpp with GPU:
1. Install CUDA toolkit
2. Install llama-cpp-python with GPU support:
```cmd
venv\Scripts\activate.bat
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
pip install llama-cpp-python
```

3. Update `config/envy.yaml`:
```yaml
llm:
  local:
    n_gpu_layers: 20
```

### For ONNX Runtime with GPU:
```cmd
pip install onnxruntime-gpu
```

## Windows Service (Optional)

To run Envy as a Windows service, use NSSM (Non-Sucking Service Manager):

1. Download NSSM from [nssm.cc](https://nssm.cc/download)
2. Extract and run:
```cmd
nssm install EnvyAssistant
```
3. Configure:
   - Path: `C:\path\to\envy\venv\Scripts\python.exe`
   - Arguments: `C:\path\to\envy\main.py`
   - Working Directory: `C:\path\to\envy`

## Troubleshooting

### Audio Issues:
- Check Windows Sound Settings
- Ensure microphone is set as default input device
- Test microphone in Windows Voice Recorder

### Python Not Found:
- Reinstall Python with "Add to PATH" checked
- Or manually add Python to PATH environment variable

### VOSK Model Not Found:
Manually download:
1. Download from: https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
2. Extract to `models\vosk-model-small-en-us-0.15\`

### GPU Not Detected:
```cmd
# Check NVIDIA driver
nvidia-smi

# Verify CUDA
nvcc --version
```

### Permission Issues:
- Run Command Prompt as Administrator if needed
- Check Windows Defender/Firewall settings

## Performance Tuning

### Low Resource Profile:
- Set `profile: low` in config
- Suitable for CPU-only operation
- Reduces resource usage

### Balanced Profile (Default):
- Optimal for GTX 1070
- Uses GPU when available
- Balanced resource usage

### Power Profile:
- Maximum performance
- Uses all available resources
- For high-end systems

## Next Steps

- See `README.md` for usage instructions
- See `docs/security.md` for security configuration
- Run tests manually using Python test scripts
