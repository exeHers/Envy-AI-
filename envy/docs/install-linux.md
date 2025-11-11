## Envy Installation — Linux (Intel i3 + GTX 1070)

These steps target Ubuntu/Debian-like distributions running on modest CPUs (Intel i3) with an NVIDIA GTX 1070 (8 GB) and 16 GB RAM.

### 1. System Packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git \
  build-essential libportaudio2 ffmpeg curl unzip
```

`libportaudio2` enables microphone access for the wake listener; `ffmpeg` helps with audio conversion.

### 2. NVIDIA / CUDA (Optional)

1. Install proprietary NVIDIA drivers appropriate for your GPU (>= 470).
2. Install CUDA toolkit if you want GPU-accelerated llama.cpp or Whisper:

```bash
sudo apt install -y nvidia-cuda-toolkit
```

Envy defaults to CPU-friendly settings. Edit `config/envy.yaml` to enable GPU acceleration (`enable_gpu_acceleration: true`) and set `gpu_layers` for llama.cpp models.

### 3. Clone & Install

```bash
git clone https://github.com/you/envy.git
cd envy
./install_envy.sh --local-demo
```

The installer creates a virtual environment in `.venv`, installs Python dependencies, and prepares placeholder models. View `artifacts/install-log.txt` for details.

### 4. (Optional) Download Full Models

For better accuracy:

```bash
./scripts/download_models.sh --full              # Vosk small English (~50 MB)
# llama.cpp GGUF example (TinyLlama, ~700 MB):
curl -L -o models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

Update `config/envy.yaml` to point `profile.llm.model_path` at the downloaded GGUF.

### 5. Run Envy

```bash
./run_envy_local.sh --profile balanced
# or headless, no dashboard:
./run_envy_local.sh --profile balanced --no-gui
```

Wake listener (port 7001), STT (7002), TTS (7003), skills (7004), LLM adapter (7005), router (7000), and dashboard (7010) start automatically.

Visit `http://127.0.0.1:7010` for the control panel, confirmations, and logs.

### 6. Systemd Service

```bash
sudo useradd -r -d /opt/envy envy
sudo mkdir -p /opt/envy
sudo cp -r . /opt/envy
sudo chown -R envy:envy /opt/envy
sudo cp scripts/systemd/envy.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now envy.service
```

Check logs with `journalctl -u envy -f`.

### 7. Troubleshooting

- No audio input: verify `arecord -l`; ensure the user is in the `audio` group.
- High CPU: switch to `--profile low`.
- TTS silent: check `artifacts/tts-output.wav` to confirm synthesis; install `espeak` as fallback if desired.
- GPU errors: reduce `gpu_layers` in config or disable acceleration.
