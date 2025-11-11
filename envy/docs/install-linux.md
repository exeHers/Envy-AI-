# Linux Installation Guide (Intel i3 + GTX 1070)

This guide walks through installing Envy on a mid-range Linux laptop/desktop (Ubuntu 22.04 or similar) with an Intel i3 CPU, NVIDIA GTX 1070 (8 GB VRAM), and 16 GB RAM.

## 1. Prerequisites

- Python 3.10+ (`sudo apt install python3 python3-venv python3-pip`)
- PortAudio for microphone access (`sudo apt install portaudio19-dev`)
- Build tools (`sudo apt install build-essential`)
- Optional NVIDIA drivers + CUDA toolkit for GPU inference
- Git (for repo management)

## 2. Clone & Enter Repo

```bash
git clone https://github.com/your-org/envy.git
cd envy
```

## 3. Run Installer

```bash
./install_envy.sh --local-demo
```

What happens:
- Creates `.envy-venv` virtualenv.
- Installs Python dependencies (FastAPI, Vosk, pyttsx3, psutil, etc.).
- Downloads Vosk small English model into `artifacts/models/`.
- Logs to `artifacts/install-log.txt`.

### Optional Flags

- `--llm` – download TinyLlama GGUF (≈1.1 GB) for local LLM responses.
- `--profile power` – set active profile to “power” (higher resource usage).
- `--register-systemd` – install `envy.service` under `/etc/systemd/system` (requires sudo).
- `--force-models` – re-download models even if cached.

## 4. Audio Configuration

- Verify microphone with `arecord -l`.
- Update `config/envy.yaml` if custom input device needed.
- For pulse-based systems, ensure `pavucontrol` shows the correct default device.

## 5. GPU Enablement (Optional)

To leverage CUDA for llama.cpp or Whisper acceleration:

```bash
sudo apt install nvidia-driver-535 nvidia-cuda-toolkit
./install_envy.sh --profile power --llm
```

Then edit `config/envy.yaml`:

```yaml
llm:
  local:
    enabled: true
    model_path: artifacts/models/tinyllama-1.1b-chat.gguf
    gpu_layers: 20    # adjust based on VRAM
```

## 6. Running Envy

```bash
./run_envy_local.sh --profile balanced
```

Headless mode:

```bash
./run_envy_local.sh --profile low --no-gui
```

## 7. Systemd Service (Optional)

```bash
sudo ./install_envy.sh --register-systemd
sudo systemctl start envy@$(whoami).service
```

The unit assumes Envy lives under `/home/<user>/envy/`; adjust `installers/systemd/envy.service` if needed.

## 8. Verification

```bash
source .envy-venv/bin/activate
pytest
./scripts/perf-report-gen.sh
```

Artifacts appear in `artifacts/tests/` and `artifacts/perf-report.txt`.
