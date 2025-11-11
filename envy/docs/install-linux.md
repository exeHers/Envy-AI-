# Envy Installation Guide - Linux

Detailed installation instructions for Linux systems, optimized for Intel i3 + GTX 1070.

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04+ / Debian 10+ / Fedora 33+ or similar
- **CPU**: Intel i3 or equivalent (2+ cores)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 5GB free space
- **GPU**: Optional - NVIDIA GTX 1070 or similar (for GPU acceleration)

### Required Software

```bash
# Update package list
sudo apt update

# Install Python 3.10+
sudo apt install python3 python3-pip python3-venv

# Install audio dependencies
sudo apt install portaudio19-dev python3-pyaudio

# Install text-to-speech engine
sudo apt install espeak espeak-data libespeak-dev

# Optional: For GPU acceleration
sudo apt install nvidia-cuda-toolkit  # If you have NVIDIA GPU
```

## Installation Steps

### 1. Download Envy

```bash
# If you have a zip file
unzip envy-ready.zip
cd envy

# Or clone from repository
git clone <repository-url> envy
cd envy
```

### 2. Run Installer

```bash
# Make installer executable
chmod +x install_envy.sh

# Run installation
bash install_envy.sh

# This will:
# - Create virtual environment
# - Install Python dependencies
# - Download AI models (~2.5GB)
# - Set up directory structure
# - Create run scripts
```

### 3. Verify Installation

```bash
# Check that models were downloaded
ls -lh models/

# Should see:
# - vosk-model-small-en-us-0.15/
# - vosk-model-en-us-0.22/
# - tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### 4. Test Run

```bash
# Run tests
source venv/bin/activate
python tests/run_tests.py

# Start Envy
./run_envy_local.sh
```

## Hardware-Specific Configuration

### For Intel i3 (No GPU)

Use the **low** or **balanced** profile:

```bash
./run_envy_local.sh --profile balanced
```

Edit `config/envy.yaml`:
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

```bash
./run_envy_local.sh --profile power
```

Edit `config/envy.yaml`:
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

1. **Install CUDA** (if not already installed):
```bash
# Check NVIDIA driver
nvidia-smi

# Install CUDA toolkit
sudo apt install nvidia-cuda-toolkit

# Verify CUDA
nvcc --version
```

2. **Install GPU-enabled llama-cpp-python**:
```bash
source venv/bin/activate

# Uninstall CPU version
pip uninstall llama-cpp-python

# Install GPU version
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir
```

3. **Test GPU**:
```bash
python -c "from llama_cpp import Llama; print('GPU support available')"
```

4. **Update config** to use GPU layers:
```yaml
llm:
  local_gpu_layers: 20  # Start with 20, increase if stable
```

## Audio Configuration

### Test Microphone

```bash
# List audio devices
python -c "import sounddevice; print(sounddevice.query_devices())"

# Record test
python -c "import sounddevice as sd; import soundfile as sf; import numpy as np; rec = sd.rec(int(3*16000), samplerate=16000, channels=1); sd.wait(); sf.write('test.wav', rec, 16000); print('Saved test.wav')"

# Play test
aplay test.wav  # or: paplay test.wav
```

### Fix Audio Issues

```bash
# Install additional audio libraries
sudo apt install libasound2-dev alsa-utils

# Configure ALSA
sudo nano /etc/asound.conf
# Add:
# pcm.!default {
#     type hw
#     card 0
# }

# Test speaker
espeak "Test"

# Fix permissions
sudo usermod -a -G audio $USER
# Log out and back in
```

## Service Installation

### Install as systemd service

```bash
# Install service
sudo bash scripts/install_service.sh

# Start service
sudo systemctl start envy

# Check status
sudo systemctl status envy

# View logs
journalctl -u envy -f

# Enable auto-start on boot
sudo systemctl enable envy
```

### Service Configuration

Edit service file if needed:
```bash
sudo nano /etc/systemd/system/envy.service
```

Change profile or options:
```ini
ExecStart=/opt/envy/venv/bin/python3 /opt/envy/envy_main.py --profile power --no-gui
```

Reload after changes:
```bash
sudo systemctl daemon-reload
sudo systemctl restart envy
```

## Performance Tuning

### CPU Governor

For better performance:
```bash
# Check current governor
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Set to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Swap Configuration

If you have limited RAM:
```bash
# Check swap
swapon --show

# Create swap file (if needed)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Monitor Performance

```bash
# Generate performance report
source venv/bin/activate
python scripts/perf_report.py

# Monitor real-time
htop  # Install: sudo apt install htop

# GPU monitoring
watch -n 1 nvidia-smi  # If GPU available
```

## Troubleshooting

### Issue: Python version too old

```bash
# Install Python 3.10+
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev

# Use specific Python version
python3.10 -m venv venv
```

### Issue: Audio not working

```bash
# Check PulseAudio
pulseaudio --check
pulseaudio --start

# Check ALSA
aplay -l  # List devices
alsamixer  # Adjust levels

# Reinstall audio libs
sudo apt install --reinstall portaudio19-dev python3-pyaudio
```

### Issue: GPU not detected

```bash
# Check NVIDIA driver
nvidia-smi

# Install driver if needed
sudo apt install nvidia-driver-470  # Use latest available

# Reboot
sudo reboot
```

### Issue: Out of memory

```bash
# Use low profile
./run_envy_local.sh --profile low

# Close other applications
# Add swap space (see above)

# Use smaller models
# Edit config/envy.yaml to use smaller model paths
```

### Issue: Model download fails

```bash
# Manual download
cd models

# VOSK small
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip

# VOSK medium
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip

# TinyLlama
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

## Uninstallation

```bash
# Stop service (if installed)
sudo systemctl stop envy
sudo systemctl disable envy
sudo rm /etc/systemd/system/envy.service
sudo systemctl daemon-reload

# Remove files
cd ..
rm -rf envy

# Remove dependencies (optional)
sudo apt remove python3-pyaudio espeak
sudo apt autoremove
```

## Next Steps

1. **Test Envy**: Say "Envy" and give voice commands
2. **Access Dashboard**: Open http://localhost:8080
3. **Customize Config**: Edit `config/envy.yaml`
4. **Read Security Guide**: See `docs/security.md`
5. **Create Skills**: Add custom skills in `skills/`

---

For more help, see the main [README.md](../README.md) or check the logs in `logs/envy.log`.
