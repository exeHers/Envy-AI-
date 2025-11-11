# Linux Installation Guide

## System Requirements

- Linux distribution (Ubuntu 20.04+, Debian 11+, or similar)
- Python 3.10 or higher
- Intel i3 processor or better
- 8GB+ RAM (16GB recommended)
- NVIDIA GPU (optional, for GPU acceleration)
- Microphone and speakers

## Step-by-Step Installation

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git wget curl
sudo apt-get install -y portaudio19-dev python3-pyaudio
sudo apt-get install -y build-essential cmake
```

**For GPU support (NVIDIA):**
```bash
# Install CUDA toolkit (if not already installed)
# Follow NVIDIA's CUDA installation guide for your distribution
```

### 2. Clone or Extract Envy

If you have the source:
```bash
cd /opt  # or your preferred location
sudo mkdir -p envy
sudo chown $USER:$USER envy
cd envy
# Extract or copy Envy files here
```

### 3. Run Installer

```bash
cd /path/to/envy
bash scripts/install_envy.sh --local-demo
```

This will:
- Create a Python virtual environment
- Install all Python dependencies
- Download required models (VOSK, Whisper)
- Create necessary directories
- Set up run scripts

### 4. Download LLM Models (Optional)

For local LLM operation, download a quantized model:

```bash
# Recommended for 8GB VRAM: Llama-2-7B Q4_0
cd models
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_0.gguf \
  -O llama-7b-q4_0.gguf
```

Update `config/envy.yaml`:
```yaml
llm:
  local:
    model_path: "models/llama-7b-q4_0.gguf"
```

### 5. Configure Audio

Test microphone:
```bash
# List audio devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Test recording
python3 -c "import sounddevice as sd; import numpy as np; 
data = sd.rec(int(3 * 16000), samplerate=16000, channels=1); 
sd.wait(); print('Recording complete')"
```

### 6. Start Envy

**Development mode:**
```bash
./run_envy_local.sh --profile balanced
```

**Production mode (systemd service):**
```bash
# Install service (requires root)
sudo cp scripts/envy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable envy
sudo systemctl start envy

# Check status
sudo systemctl status envy

# View logs
sudo journalctl -u envy -f
```

### 7. Access Web Dashboard

Open browser to: `http://localhost:8080`

## CUDA/GPU Setup (Optional)

If you have an NVIDIA GPU:

1. **Install CUDA Toolkit:**
   ```bash
   # Follow NVIDIA's official CUDA installation guide
   # Verify installation:
   nvidia-smi
   ```

2. **Install GPU-enabled packages:**
   ```bash
   source venv/bin/activate
   pip install onnxruntime-gpu
   ```

3. **Configure for GPU:**
   Edit `config/envy.yaml`:
   ```yaml
   stt:
     device: "cuda"
   llm:
     local:
       gpu_layers: 20  # Adjust based on VRAM
   ```

## Troubleshooting

### Audio Issues

**No microphone detected:**
```bash
# Check audio devices
arecord -l
# Test microphone
arecord -d 5 test.wav && aplay test.wav
```

**Permission denied:**
```bash
# Add user to audio group
sudo usermod -a -G audio $USER
# Log out and back in
```

### Model Download Issues

If models fail to download automatically:
```bash
# Manual VOSK download
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 vosk-wake
```

### Performance Tuning

For Intel i3 systems, use "low" profile:
```bash
./run_envy_local.sh --profile low
```

Edit `config/envy.yaml` limits section to adjust resource usage.

### Service Won't Start

Check logs:
```bash
sudo journalctl -u envy -n 50
```

Common issues:
- Missing dependencies: Re-run installer
- Permission issues: Check file ownership
- Port conflicts: Change web port in config

## Next Steps

- Run acceptance tests: `./scripts/run_tests.sh`
- Generate performance report: `./scripts/perf-report-gen.sh`
- Review security settings: See `docs/security.md`
- Customize skills: Add to `skills/` directory
