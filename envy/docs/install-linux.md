# Envy Installation Guide - Linux

This guide covers installing Envy on Linux systems, specifically optimized for Intel i3 processors with GTX 1070 GPUs.

## Prerequisites

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, or similar)
- **CPU**: Intel i3 or better
- **GPU**: NVIDIA GTX 1070 (8GB VRAM) - Optional but recommended
- **RAM**: 16GB minimum
- **Python**: 3.10 or higher
- **CUDA**: 11.0+ (optional, for GPU acceleration)

## Step 1: Install System Dependencies

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git wget curl
sudo apt install -y portaudio19-dev python3-pyaudio  # For audio
sudo apt install -y build-essential cmake  # For compiling dependencies
```

### NVIDIA CUDA (Optional, for GPU acceleration)
```bash
# Check if CUDA is installed
nvidia-smi

# If not installed, follow NVIDIA's CUDA installation guide:
# https://developer.nvidia.com/cuda-downloads
```

## Step 2: Install Envy

```bash
cd /path/to/envy
chmod +x install_envy.sh
./install_envy.sh --local-demo
```

The installer will:
- Create a Python virtual environment
- Install all Python dependencies
- Download required models (VOSK, Whisper)
- Set up the configuration

## Step 3: Configure Envy

Edit `config/envy.yaml` to match your hardware:

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

## Step 4: Run Envy

### Manual Run
```bash
cd /path/to/envy
source venv/bin/activate
./run_envy_local.sh --profile balanced
```

### As a System Service (Optional)

```bash
# Install as systemd service
sudo ./install_envy.sh --systemd

# Start the service
sudo systemctl start envy

# Enable auto-start on boot
sudo systemctl enable envy

# Check status
sudo systemctl status envy

# View logs
journalctl -u envy -f
```

## Step 5: Access Web Dashboard

Open your browser and navigate to:
```
http://localhost:8080
```

## Troubleshooting

### Audio Issues
```bash
# Check microphone permissions
arecord -l

# Test microphone
arecord -d 5 test.wav
aplay test.wav
```

### GPU Not Detected
```bash
# Check NVIDIA driver
nvidia-smi

# If not working, edit config/envy.yaml:
# Set use_gpu: false and device: "cpu"
```

### High CPU Usage
- Switch to "low" profile: `--profile low`
- Reduce model size in config
- Disable GPU acceleration

### Model Download Issues
```bash
# Manually download VOSK model
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

### Permission Errors
```bash
# Make scripts executable
chmod +x install_envy.sh run_envy_local.sh

# Check file permissions
ls -la
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
- Check `artifacts/envy.log` for detailed logs
- Run tests: `python tests/test_envy.py`
