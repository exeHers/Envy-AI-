# Envy Linux Installation Guide

This guide targets Ubuntu 22.04 (or similar) running on an Intel i3 CPU with a GTX 1070 (8 GB VRAM) and 16 GB RAM. The steps also apply to other Debian-based distributions with minor adjustments.

## 1. System Packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git \
  build-essential portaudio19-dev libffi-dev libnss3 \
  curl unzip
```

- `portaudio19-dev` enables microphone capture through `sounddevice`.
- `libffi` ensures `pyttsx3` voices work correctly.

Optional (for GPU acceleration with llama.cpp):

```bash
sudo apt install -y nvidia-driver-535 nvidia-cuda-toolkit
```

## 2. Clone and Install

```bash
git clone https://example.com/envy.git
cd envy
./install_envy.sh --local-demo
```

`--local-demo` skips the ~600 MB TinyLlama model. Omit it if you want full offline LLM support immediately.

If you choose the full install, ensure ~4 GB free disk space for the VOSK models and GGUF file.

## 3. Audio Configuration

Check your microphone index:

```bash
python -m sounddevice
```

Set the chosen device in `config/envy.yaml` under `audio.device`. Leave it blank for default auto-detection.

## 4. Running Envy

Headless mode (no dashboard):

```bash
./run_envy_local.sh --profile balanced --headless
```

With dashboard (http://localhost:8190):

```bash
./run_envy_local.sh --profile balanced
```

## 5. Installing as a Service

1. Copy the project to `/opt/envy`.
2. Adjust ownership:

   ```bash
   sudo chown -R envy:envy /opt/envy
   ```

3. Link the systemd unit:

   ```bash
   sudo ln -s /opt/envy/systemd/envy.service /etc/systemd/system/envy@envy.service
   sudo systemctl daemon-reload
   sudo systemctl enable envy@envy
   sudo systemctl start envy@envy
   ```

4. Logs are written to `/opt/envy/artifacts/logs/envy.log`.

## 6. Profiles & Hardware Tuning

- `low`: STT/LLM remains CPU-only; recommended when the machine is doing other tasks.
- `balanced`: enables llama.cpp if the model is present; uses up to ~4 threads.
- `power`: increases sensitivity and threads (set `llm.temperature` higher for creativity).

Edit `config/envy.yaml` and adjust `profile` or use `run_envy_local.sh --profile power`.

## 7. Troubleshooting

- **No wake detection**: verify the VOSK model downloaded correctly (`models/vosk-wake`) and the microphone works (`arecord -l`).
- **pyttsx3 voice errors**: install `espeak` (`sudo apt install espeak`) or change voice ID in `config/envy.yaml`.
- **GPU not detected**: ensure `nvidia-smi` runs without error; otherwise the assistant falls back to CPU automatically.
- **Port conflicts**: change `dashboard.port` in `config/envy.yaml` and restart the service.

## 8. Updating

```bash
git pull
source .venv/bin/activate
pip install -e .
```

Re-run `scripts/download_models.py` if models were updated upstream.
