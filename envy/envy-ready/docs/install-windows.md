# Envy Installation Guide - Windows

This guide covers installing Envy on Windows 10/11 systems, optimized for Intel i3 processors with GTX 1070 GPUs.

## Prerequisites

- **OS**: Windows 10 or Windows 11
- **CPU**: Intel i3 or better
- **GPU**: NVIDIA GTX 1070 (8GB VRAM) - Optional but recommended
- **RAM**: 16GB minimum
- **Python**: 3.10 or higher
- **CUDA**: 11.0+ (optional, for GPU acceleration)

## Step 1: Install Python

1. Download Python 3.10+ from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Verify installation:
   ```cmd
   python --version
   ```

## Step 2: Install NVIDIA CUDA (Optional)

1. Download CUDA Toolkit from https://developer.nvidia.com/cuda-downloads
2. Run the installer
3. Verify installation:
   ```cmd
   nvidia-smi
   ```

## Step 3: Install Envy

1. Open Command Prompt or PowerShell as Administrator
2. Navigate to the Envy directory:
   ```cmd
   cd C:\path\to\envy
   ```
3. Run the installer:
   ```cmd
   install_envy.bat
   ```

The installer will:
- Create a Python virtual environment
- Install all Python dependencies
- Set up the configuration

## Step 4: Configure Envy

Edit `config\envy.yaml` to match your hardware:

```yaml
# For GTX 1070 (8GB VRAM)
llm:
  local:
    n_gpu_layers: 20  # Use GPU layers
    n_threads: 4

resources:
  max_gpu_memory_mb: 6144  # Leave 2GB for system
  max_cpu_percent: 70
```

## Step 5: Run Envy

### Manual Run
```cmd
cd C:\path\to\envy
venv\Scripts\activate
run_envy_local.bat
```

### As a Windows Service (Optional)

Using NSSM (Non-Sucking Service Manager):

1. Download NSSM from https://nssm.cc/download
2. Extract and run:
   ```cmd
   nssm install Envy "C:\path\to\envy\venv\Scripts\python.exe" "C:\path\to\envy\src\main.py"
   nssm set Envy AppDirectory "C:\path\to\envy"
   nssm start Envy
   ```

## Step 6: Access Web Dashboard

Open your browser and navigate to:
```
http://localhost:8080
```

## Troubleshooting

### Audio Issues
1. Check microphone in Windows Settings > Privacy > Microphone
2. Test microphone:
   ```cmd
   # Use Windows Sound Recorder or test in Settings
   ```

### GPU Not Detected
```cmd
# Check NVIDIA driver
nvidia-smi

# If not working, edit config\envy.yaml:
# Set use_gpu: false and device: "cpu"
```

### High CPU Usage
- Switch to "low" profile: Edit `run_envy_local.bat` and add `--profile low`
- Reduce model size in config
- Disable GPU acceleration

### Permission Errors
- Run Command Prompt as Administrator
- Check antivirus isn't blocking Python scripts

### Python Path Issues
```cmd
# Verify Python is in PATH
where python

# If not, add Python to PATH manually or reinstall Python
```

## Performance Tuning

### Low Resource Profile
For systems with limited resources:
```yaml
profile: low
stt:
  model_size: "tiny"
llm:
  local:
    n_gpu_layers: 10
    n_threads: 2
```

### Power Profile
For maximum performance:
```yaml
profile: power
stt:
  model_size: "medium"
llm:
  local:
    n_gpu_layers: 35
    n_threads: 8
```

## Next Steps

- See [Security Documentation](security.md) for security settings
- Check `artifacts\envy.log` for detailed logs
- Run tests: `python tests\test_envy.py`
