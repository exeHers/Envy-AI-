# Installing Envy on Linux

This guide covers installation on Linux systems, specifically optimized for Intel i3 processors with GTX 1070 GPUs.

## Prerequisites

- Linux distribution (Ubuntu 20.04+, Debian 11+, or similar)
- Python 3.10 or higher
- 16GB RAM minimum
- GTX 1070 (8GB VRAM) - optional but recommended
- Internet connection for initial setup

## Step 1: Install System Dependencies

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv build-essential portaudio19-dev python3-pyaudio
```

### For GPU support (CUDA):
```bash
# Install NVIDIA drivers and CUDA toolkit
# Follow NVIDIA's official installation guide for your distribution
```

## Step 2: Run Installer

```bash
cd envy
chmod +x install_envy.sh
./install_envy.sh
```

The installer will:
- Create a Python virtual environment
- Install all Python dependencies
- Download the VOSK model (if not present)
- Create necessary directories
- Set up permissions

## Step 3: Optional - Install as System Service

To run Envy as a systemd service:

```bash
sudo ./install_envy.sh --install-service
sudo systemctl start envy
sudo systemctl status envy
```

## Step 4: Configure (Optional)

Edit `config/envy.yaml` to customize:

- **Profile**: Set to `low`, `balanced`, or `power` based on your hardware
- **GPU**: Enable GPU acceleration if you have CUDA installed
- **Wake Word**: Adjust sensitivity if needed

## Step 5: Run Envy

### Manual Run:
```bash
./run_envy_local.sh
```

### With Profile:
```bash
./run_envy_local.sh --profile balanced
```

### Headless (no web dashboard):
```bash
./run_envy_local.sh --no-gui
```

## GPU Acceleration (Optional)

### For llama.cpp with GPU:
1. Install CUDA toolkit
2. Install llama-cpp-python with GPU support:
```bash
source venv/bin/activate
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
```

3. Update `config/envy.yaml`:
```yaml
llm:
  local:
    n_gpu_layers: 20  # Adjust based on VRAM
```

### For ONNX Runtime with GPU:
```bash
pip install onnxruntime-gpu
```

## Troubleshooting

### Audio Issues:
```bash
# Check audio devices
arecord -l

# Test microphone
arecord -d 5 test.wav
aplay test.wav
```

### Permission Issues:
```bash
# Add user to audio group
sudo usermod -a -G audio $USER
# Log out and back in
```

### VOSK Model Not Found:
```bash
# Manually download model
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

### GPU Not Detected:
```bash
# Check NVIDIA driver
nvidia-smi

# Verify CUDA
nvcc --version
```

## Performance Tuning

### Low Resource Profile:
- Set `profile: low` in config
- Reduces CPU/memory limits
- Suitable for CPU-only operation

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
- Run tests: `./scripts/run_tests.sh`
