# Installation instructions for Linux (Intel i3 + GTX 1070)

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Python 3.10+
- NVIDIA drivers (for GPU acceleration)
- CUDA toolkit (optional, for GPU acceleration)

## Step 1: Install System Dependencies

```bash
# Update package list
sudo apt update

# Install Python and build tools
sudo apt install -y python3 python3-pip python3-venv build-essential

# Install audio libraries
sudo apt install -y portaudio19-dev python3-pyaudio libasound2-dev

# Install NVIDIA drivers (if not already installed)
# Check: nvidia-smi
# If not installed:
sudo apt install -y nvidia-driver-470 nvidia-cuda-toolkit
```

## Step 2: Install Envy

```bash
# Clone or extract Envy
cd /opt
sudo mkdir -p envy
sudo chown $USER:$USER envy
cd envy

# Run installer
chmod +x install_envy.sh
./install_envy.sh --local-demo
```

## Step 3: Download Models

### VOSK Model (Wake Word)
The installer should download this automatically. If not:

```bash
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.22.zip
unzip vosk-model-small-en-us-0.22.zip
rm vosk-model-small-en-us-0.22.zip
```

### Whisper Model (STT)
Downloaded automatically on first use. For manual download:

```bash
python3 -c "import whisper; whisper.load_model('base')"
```

### LLM Model (Optional)
For local LLM, download a quantized model:

```bash
cd models
# Download llama-2-7b-chat-q4_0.gguf (or similar)
# Example URL (check Hugging Face for latest):
# wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_0.gguf -O llama-2-7b-chat-q4_0.gguf
```

## Step 4: Configure

Edit `config/envy.yaml`:

```yaml
llm:
  local:
    model_path: "models/llama-2-7b-chat-q4_0.gguf"
    n_gpu_layers: 20  # Adjust based on VRAM
```

## Step 5: Run Envy

### Manual Start
```bash
cd /opt/envy
source venv/bin/activate
python3 envy.py --profile balanced
```

### As System Service
```bash
sudo cp scripts/envy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable envy.service
sudo systemctl start envy.service
```

## Step 6: Access Dashboard

Open browser to: http://127.0.0.1:8080

## Troubleshooting

### GPU Not Detected
- Check: `nvidia-smi`
- Install NVIDIA drivers if missing
- Set `n_gpu_layers: 0` in config for CPU-only mode

### High CPU Usage
- Use `low` profile: `--profile low`
- Reduce model sizes in config
- Disable GPU acceleration

### Audio Issues
- Check microphone permissions
- Test: `python3 -c "import sounddevice; print(sounddevice.query_devices())"`
- Adjust audio device in config if needed

### Model Download Fails
- Check internet connection
- Download models manually and place in `models/` directory
- Use remote free endpoint as fallback

## Performance Tuning

For Intel i3 + GTX 1070 (8GB VRAM):

**Balanced Profile (Recommended):**
- STT: whisper-base
- LLM: q4_0 quantized model
- GPU layers: 20
- CPU threads: 4

**Low Profile (If resources constrained):**
- STT: whisper-tiny
- LLM: CPU-only or smaller model
- GPU layers: 0
- CPU threads: 2

**Power Profile (If you have headroom):**
- STT: whisper-small
- LLM: q4_1 or q5_0 quantized
- GPU layers: 35
- CPU threads: 8
