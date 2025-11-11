# Envy AI Assistant - Linux Installation Guide

Complete installation guide for running Envy on Linux systems, optimized for Intel i3 + GTX 1070.

---

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04+, Debian 11+, Fedora 35+, or Arch Linux
- **CPU**: Intel i3 or equivalent (2+ cores)
- **RAM**: 4GB minimum (8GB+ recommended)
- **GPU**: NVIDIA GTX 1070 (optional, for GPU acceleration)
- **Storage**: 5GB free space
- **Audio**: Working microphone and speakers

### Software Requirements

- Python 3.8+ (3.10+ recommended)
- Git (for cloning repository)
- sudo privileges (for system package installation)

---

## Step-by-Step Installation

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# OR
sudo dnf update -y  # Fedora
# OR
sudo pacman -Syu  # Arch
```

### 2. Install Python and Dependencies

#### Ubuntu/Debian

```bash
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    espeak \
    alsa-utils \
    libsndfile1 \
    git \
    wget \
    unzip
```

#### Fedora

```bash
sudo dnf install -y \
    python3 \
    python3-pip \
    portaudio-devel \
    python3-pyaudio \
    ffmpeg \
    espeak \
    alsa-utils \
    libsndfile \
    git \
    wget \
    unzip
```

#### Arch Linux

```bash
sudo pacman -S --noconfirm \
    python \
    python-pip \
    portaudio \
    python-pyaudio \
    ffmpeg \
    espeak \
    alsa-utils \
    libsndfile \
    git \
    wget \
    unzip
```

### 3. Set Up Envy

```bash
# Navigate to envy directory
cd envy

# Make installer executable
chmod +x install_envy.sh

# Run installer
./install_envy.sh --local-demo
```

The installer will:
1. Verify Python version
2. Create virtual environment
3. Install Python dependencies
4. Download AI models (VOSK, TinyLlama)
5. Create run scripts
6. Set up directory structure

---

## GPU Acceleration (Optional)

If you have an NVIDIA GTX 1070 or similar GPU:

### 1. Install NVIDIA Drivers

```bash
# Ubuntu/Debian
sudo apt install nvidia-driver-525  # Or latest version

# Check installation
nvidia-smi
```

### 2. Install CUDA Toolkit

```bash
# Ubuntu 22.04
wget https://developer.download.nvidia.com/compute/cuda/12.2.0/local_installers/cuda_12.2.0_535.54.03_linux.run
sudo sh cuda_12.2.0_535.54.03_linux.run
```

### 3. Reinstall llama-cpp-python with CUDA

```bash
source venv/bin/activate
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install --force-reinstall llama-cpp-python
```

### 4. Update Configuration

Edit `config/envy.yaml`:

```yaml
resource_profile: "balanced"  # or "power"

profiles:
  balanced:
    use_gpu: true
    gpu_layers: 32  # Adjust based on VRAM

llm:
  local:
    gpu_layers: 32  # Load more layers on GPU
```

---

## Audio Configuration

### Test Audio Devices

```bash
# List audio devices
aplay -l   # Playback devices
arecord -l # Recording devices

# Test microphone
arecord -d 5 test.wav
aplay test.wav
```

### Fix Audio Permissions

```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Restart (logout/login or reboot)
```

### PulseAudio Configuration

If using PulseAudio:

```bash
# Check PulseAudio status
pulseaudio --check

# Restart PulseAudio
pulseaudio -k
pulseaudio --start
```

### ALSA Configuration

Create `~/.asoundrc` if needed:

```
pcm.!default {
    type hw
    card 0
}

ctl.!default {
    type hw
    card 0
}
```

---

## Running Envy

### Start Envy

```bash
# Default (balanced profile)
./run_envy_local.sh

# Specific profile
./run_envy_local.sh --profile low
./run_envy_local.sh --profile power
```

### Test Installation

```bash
# Run all tests
bash tests/run_all_tests.sh

# Run individual test
python3 tests/test_code_skill.py
```

### Access Web Dashboard

Open browser: **http://localhost:8080**

---

## 24/7 Service Installation

To run Envy as a system service:

### 1. Copy Service Files

```bash
cd installers
sudo bash install_service_linux.sh
```

### 2. Enable Service

```bash
sudo systemctl enable envy@$USER
```

### 3. Start Service

```bash
sudo systemctl start envy@$USER
```

### 4. Check Status

```bash
sudo systemctl status envy@$USER
```

### 5. View Logs

```bash
# Live logs
sudo journalctl -u envy@$USER -f

# Recent logs
sudo journalctl -u envy@$USER -n 100
```

### 6. Stop Service

```bash
sudo systemctl stop envy@$USER
```

### 7. Disable Service

```bash
sudo systemctl disable envy@$USER
```

---

## Firewall Configuration

If running web dashboard and accessing from other devices:

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 8080/tcp
sudo ufw reload

# firewalld (Fedora)
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

---

## Performance Tuning (Intel i3 + GTX 1070)

### Recommended Configuration

Edit `config/envy.yaml`:

```yaml
resource_profile: "balanced"

profiles:
  balanced:
    max_cpu_percent: 60
    max_memory_mb: 4096
    use_gpu: true
    stt_model: "faster-whisper-small"
    llm_model: "tinyllama-1.1b-q4"
    tts_engine: "pyttsx3"

llm:
  local:
    gpu_layers: 32  # With GTX 1070
    context_length: 2048
    max_tokens: 256
```

### CPU Affinity (Optional)

Pin Envy to specific CPU cores:

```bash
# Run on cores 0-1
taskset -c 0,1 ./run_envy_local.sh
```

### GPU Memory Monitoring

```bash
# Watch GPU usage
watch -n 1 nvidia-smi
```

---

## Troubleshooting

### ImportError: No module named 'X'

```bash
source venv/bin/activate
pip install --force-reinstall -r requirements.txt
```

### ALSA lib errors

```bash
# Suppress ALSA warnings (optional)
export ALSA_CARD=0
```

### Model download fails

```bash
# Manual VOSK download
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip

# Manual LLM download
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

### Microphone not detected

```bash
# Check permissions
ls -l /dev/snd/*

# Test with arecord
arecord -l
arecord -d 3 -f cd test.wav
```

### Service fails to start

```bash
# Check logs
sudo journalctl -u envy@$USER -n 50

# Check permissions
ls -la /opt/envy

# Run manually to debug
cd /opt/envy
source venv/bin/activate
python3 envy_main.py
```

---

## Upgrading Models

### Upgrade to Larger LLM

```bash
# Download Mistral 7B (quantized)
cd models
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

Update `config/envy.yaml`:

```yaml
llm:
  local:
    model_path: "./models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
```

### Upgrade STT Model

```bash
# Larger VOSK model
cd models
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip
```

---

## Uninstallation

```bash
# Stop service (if running)
sudo systemctl stop envy@$USER
sudo systemctl disable envy@$USER
sudo rm /etc/systemd/system/envy@.service

# Remove files
cd ..
rm -rf envy/

# Remove dependencies (optional)
sudo apt remove python3-pyaudio ffmpeg espeak
sudo apt autoremove
```

---

## Next Steps

- Customize `config/envy.yaml` for your needs
- Add custom skills in `skills/` directory
- Explore the web dashboard at http://localhost:8080
- Check out [Security Documentation](security.md)

---

**Questions? Check the [main README](../README.md) or create an issue.**
