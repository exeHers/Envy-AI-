# Installation Guide - Linux

Complete installation instructions for Envy on Linux systems.

## System Requirements

### Hardware
- **CPU**: Intel i3 or better (4+ cores recommended)
- **RAM**: 16GB minimum
- **GPU**: NVIDIA GTX 1070 (8GB VRAM) - optional but recommended
- **Storage**: 10GB free space
- **Audio**: Working microphone and speakers

### Software
- Ubuntu 20.04+, Debian 11+, or compatible distribution
- Python 3.10 or higher
- pip3
- git

## Quick Installation

```bash
# Clone or download Envy
cd /path/to/envy

# Run installer
chmod +x install_envy.sh
./install_envy.sh
```

The installer will:
1. Check Python version
2. Create virtual environment
3. Install Python dependencies
4. Download required models (optional)
5. Set up directories

## Manual Installation

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y portaudio19-dev python3-pyaudio
sudo apt install -y ffmpeg
sudo apt install -y alsa-utils pulseaudio
```

**Fedora/RHEL:**
```bash
sudo dnf install -y python3 python3-pip
sudo dnf install -y portaudio-devel python3-pyaudio
sudo dnf install -y ffmpeg
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt
```

### 3. Install NVIDIA GPU Support (Optional)

For GPU acceleration with NVIDIA GPUs:

```bash
# Check GPU
nvidia-smi

# Install CUDA Toolkit (if not already installed)
# For Ubuntu 20.04/22.04:
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt update
sudo apt install -y cuda

# Install CUDA-enabled packages
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

### 4. Download Models

```bash
# Make script executable
chmod +x scripts/download_models.sh

# Download models
./scripts/download_models.sh
```

This downloads:
- VOSK model (~40MB) - Required for wake word detection
- Whisper models - Auto-downloaded on first use
- Llama-2 model (~3.8GB) - Optional, for local LLM

### 5. Configure Audio

Test your audio setup:

```bash
# List input devices
arecord -l

# Test microphone (Ctrl+C to stop)
arecord -f cd -d 5 test.wav
aplay test.wav

# List output devices
aplay -l

# Test speakers
speaker-test -t wav -c 2
```

If you have issues:

```bash
# Install PulseAudio
sudo apt install pulseaudio pavucontrol

# Restart audio
pulseaudio -k
pulseaudio --start
```

## Configuration

### 1. Edit Configuration

```bash
nano config/envy.yaml
```

Key settings for Intel i3 + GTX 1070:

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
    gpu_layers: 20  # Adjust based on VRAM
```

### 2. Performance Tuning

For Intel i3 + GTX 1070 setup:

**CPU-Only Mode** (if no GPU or troubleshooting):
```yaml
resources:
  gpu_enabled: false

llm:
  local:
    threads: 4
    gpu_layers: 0
```

**Balanced Mode** (recommended):
```yaml
system:
  profile: "balanced"
  
resources:
  gpu_enabled: true
  gpu_memory_fraction: 0.7

llm:
  local:
    gpu_layers: 20
    context_size: 2048
```

**Power Mode** (maximum performance):
```yaml
system:
  profile: "power"
  
resources:
  max_cpu_percent: 80
  gpu_enabled: true
  gpu_memory_fraction: 0.9

llm:
  local:
    gpu_layers: 32
    context_size: 4096
```

## Running Envy

### Basic Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Start Envy
python main.py
```

### Using Quick-Start Script

```bash
./run_envy_local.sh
```

With options:
```bash
./run_envy_local.sh --profile balanced
./run_envy_local.sh --no-gui
```

### Web Dashboard

Once running, access the dashboard at:
```
http://localhost:8080
```

## Install as System Service

To run Envy as a background service:

```bash
# Install service (requires sudo)
sudo ./scripts/install_service_linux.sh

# Enable and start
sudo systemctl enable envy
sudo systemctl start envy

# Check status
sudo systemctl status envy

# View logs
sudo journalctl -u envy -f
```

## Verification

Run acceptance tests to verify installation:

```bash
./tests/run_tests.sh
```

All tests should pass. Check output in `artifacts/tests/`.

## Troubleshooting

### "No module named 'vosk'"

```bash
source venv/bin/activate
pip install vosk
```

### "Could not find VOSK model"

```bash
./scripts/download_models.sh
```

### "ALSA lib errors"

These are usually harmless warnings. To suppress:

```bash
# Create ALSA config
cat > ~/.asoundrc << EOF
pcm.!default {
    type pulse
}
ctl.!default {
    type pulse
}
EOF
```

### GPU Not Detected

```bash
# Check GPU
nvidia-smi

# Check CUDA
nvcc --version

# Reinstall llama-cpp-python with CUDA support
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
```

### Microphone Permission Denied

```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Log out and back in
```

### High CPU Usage

Reduce resource usage in config:

```yaml
system:
  profile: "low"

resources:
  max_cpu_percent: 30

llm:
  local:
    threads: 2
```

## Uninstallation

```bash
# Stop service (if installed)
sudo systemctl stop envy
sudo systemctl disable envy
sudo rm /etc/systemd/system/envy.service

# Remove Envy directory
cd ..
rm -rf envy/
```

## Next Steps

- Read [Security Documentation](security.md)
- Learn about [Custom Skills](custom-skills.md)
- Check [Troubleshooting Guide](troubleshooting.md)

---

Need help? Check the logs at `artifacts/logs/envy.log`
