# Windows Installation Guide

## System Requirements

- Windows 10 or 11 (64-bit)
- Python 3.10 or higher
- Intel i3 processor or better
- 8GB+ RAM (16GB recommended)
- NVIDIA GPU (optional, for GPU acceleration)
- Microphone and speakers

## Step-by-Step Installation

### 1. Install Python

1. Download Python 3.10+ from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

### 2. Install Visual C++ Build Tools

Required for some Python packages:

1. Download [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)
2. Install "C++ build tools" workload
3. Restart computer

### 3. Extract Envy

1. Extract Envy to a folder (e.g., `C:\Envy`)
2. Open Command Prompt or PowerShell as Administrator
3. Navigate to Envy directory:
   ```cmd
   cd C:\Envy
   ```

### 4. Run Installer

```cmd
scripts\install_envy.bat --local-demo
```

This will:
- Create a Python virtual environment
- Install all Python dependencies
- Download required models
- Create necessary directories
- Set up run scripts

### 5. Download LLM Models (Optional)

For local LLM operation:

1. Download a quantized model (recommended: Llama-2-7B Q4_0)
2. Place in `models\` directory
3. Update `config\envy.yaml`:
   ```yaml
   llm:
     local:
       model_path: "models/llama-7b-q4_0.gguf"
   ```

### 6. Configure Audio

Test microphone:
```cmd
# In Python
python -c "import sounddevice as sd; print(sd.query_devices())"
```

Windows audio should work automatically. If issues occur:
- Check microphone permissions in Windows Settings
- Ensure microphone is set as default recording device

### 7. Start Envy

**Development mode:**
```cmd
run_envy_local.bat
```

**As Windows Service (optional):**

Using NSSM (Non-Sucking Service Manager):

1. Download NSSM from [nssm.cc](https://nssm.cc/download)
2. Extract and run:
   ```cmd
   nssm install EnvyAssistant "C:\Envy\venv\Scripts\python.exe" "C:\Envy\main.py"
   nssm set EnvyAssistant AppDirectory "C:\Envy"
   nssm start EnvyAssistant
   ```

### 8. Access Web Dashboard

Open browser to: `http://localhost:8080`

## GPU Setup (Optional)

If you have an NVIDIA GPU:

1. **Install CUDA Toolkit:**
   - Download from [NVIDIA Developer](https://developer.nvidia.com/cuda-downloads)
   - Install CUDA Toolkit
   - Verify: `nvidia-smi` in Command Prompt

2. **Install GPU packages:**
   ```cmd
   venv\Scripts\activate
   pip install onnxruntime-gpu
   ```

3. **Configure for GPU:**
   Edit `config\envy.yaml`:
   ```yaml
   stt:
     device: "cuda"
   llm:
     local:
       gpu_layers: 20
   ```

## Troubleshooting

### Python Not Found

- Ensure Python is added to PATH
- Reinstall Python with "Add to PATH" checked
- Restart Command Prompt

### pip Install Fails

**Error: Microsoft Visual C++ 14.0 required:**
- Install Visual C++ Build Tools (see step 2)

**Error: Permission denied:**
- Run Command Prompt as Administrator
- Or use: `pip install --user <package>`

### Audio Issues

**No microphone detected:**
- Check Windows microphone permissions
- Settings > Privacy > Microphone > Allow apps to access microphone
- Test microphone in Windows Sound settings

**PyAudio installation fails:**
```cmd
# Try pre-built wheel
pip install pipwin
pipwin install pyaudio
```

### Model Download Issues

If automatic download fails:
1. Manually download VOSK model
2. Extract to `models\vosk-wake\`
3. Download Whisper models will happen automatically on first use

### Performance Tuning

For slower systems, use "low" profile:
```cmd
run_envy_local.bat --profile low
```

Edit `config\envy.yaml` to adjust resource limits.

### Service Won't Start

Check logs in `artifacts\envy.log`

Common issues:
- Missing dependencies: Re-run installer
- Port conflicts: Change web port in config
- Antivirus blocking: Add exception for Envy directory

## Next Steps

- Run acceptance tests: `scripts\run_tests.sh` (use Git Bash or WSL)
- Review security settings: See `docs\security.md`
- Customize skills: Add to `skills\` directory

## Notes

- Some scripts require Git Bash or WSL for bash compatibility
- Windows Defender may flag some Python packages; add exceptions if needed
- For best performance, disable Windows audio enhancements
