# Linux Installation Guide

Complete installation guide for Envy on Linux systems, optimized for Intel i3 + GTX 1070.

## Prerequisites

### System Requirements
- OS: Ubuntu 20.04+, Debian 11+, or similar
- CPU: Intel i3 or equivalent (4 cores recommended)
- RAM: 8GB minimum, 16GB recommended
- GPU: GTX 1070 (8GB) or similar (optional but recommended)
- Storage: 10GB free space
- Audio: Working microphone and speakers

### Software Requirements
```bash
# Update package list
sudo apt update

# Install Python 3.10+
sudo apt install python3 python3-pip python3-venv

# Install audio dependencies
sudo apt install portaudio19-dev python3-pyaudio

# Install CUDA (if using GPU)
# For GTX 1070, use CUDA 11.x
# Follow: https://developer.nvidia.com/cuda-downloads
```

## Installation Steps

### 1. Clone or Extract Envy

```bash
cd /workspace
# If you have a zip file:
unzip envy-ready.zip
cd envy
```

### 2. Run Installer

```bash
./installers/install_envy.sh
```

The installer will:
- Check Python version
- Create virtual environment
- Install dependencies
- Download models (optional)
- Create run scripts
- Optionally install systemd service

### 3. Download Models

If you skipped model download during installation:

```bash
./installers/download_models.sh
```

This downloads:
- VOSK wake word model (~40MB)
- Whisper models (auto-downloaded on first use)
- Llama-2-7B-Chat GGUF (~4GB, optional)

### 4. Configure for Your Hardware

Edit `config/envy.yaml`:

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

```bash
./run_envy_local.sh --profile balanced
```

Or simply:
```bash
./start-envy.sh
```

### As a Service (systemd)

```bash
# Start service
sudo systemctl start envy

# Enable on boot
sudo systemctl enable envy

# Check status
sudo systemctl status envy

# View logs
sudo journalctl -u envy -f
```

## GPU Setup (GTX 1070)

### Install CUDA Toolkit

```bash
# Add NVIDIA repositories
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/3bf863cc.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"

# Install CUDA 11.8
sudo apt update
sudo apt install cuda-11-8

# Add to PATH
echo 'export PATH=/usr/local/cuda-11.8/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Verify
nvidia-smi
nvcc --version
```

### Install GPU-Accelerated Dependencies

```bash
source venv/bin/activate

# Reinstall llama-cpp-python with CUDA
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir

# Install ONNX Runtime GPU (optional)
pip install onnxruntime-gpu
```

## Troubleshooting

### Audio Issues

```bash
# List audio devices
python3 -c "import sounddevice; print(sounddevice.query_devices())"

# Test microphone
arecord -d 5 test.wav
aplay test.wav
```

### VOSK Model Issues

```bash
# Re-download VOSK model
cd models
rm -rf vosk-model-small-en-us-0.15
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

### GPU Not Detected

```bash
# Check CUDA
nvidia-smi

# Check CUDA in Python
python3 -c "import torch; print(torch.cuda.is_available())"

# Reinstall with CUDA support
source venv/bin/activate
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall
```

### Permission Issues

```bash
# Audio permissions
sudo usermod -a -G audio $USER

# Restart
sudo reboot
```

## Performance Tuning

### For i3 + GTX 1070

Optimal settings in `config/envy.yaml`:

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

```bash
# Generate performance report
./artifacts/perf-report-gen.sh

# Watch GPU usage
watch -n 1 nvidia-smi

# Watch CPU/RAM
htop
```

## Uninstallation

```bash
# Stop service
sudo systemctl stop envy
sudo systemctl disable envy

# Remove service file
sudo rm /etc/systemd/system/envy.service
sudo systemctl daemon-reload

# Remove Envy
rm -rf /workspace/envy
```

## Next Steps

- Read [Configuration Reference](configuration.md)
- Learn about [Security](security.md)
- Create [Custom Skills](custom-skills.md)
- Access dashboard at http://127.0.0.1:8080
