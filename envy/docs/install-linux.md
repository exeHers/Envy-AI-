## Linux Installation Guide (Intel i3 + GTX 1070)

### 1. Prerequisites

- Ubuntu 22.04+ (or compatible)
- Python 3.10 or newer
- 10 GB free disk space
- `curl`, `git`, `ffmpeg`, `espeak-ng` (installer installs missing packages automatically if run inside Docker or WSL)
- NVIDIA driver + CUDA toolkit (optional for GPU-accelerated llama.cpp)

### 2. Clone & Install

```bash
git clone https://example.com/envy.git
cd envy
./install_envy.sh --local-demo
```

Flags:
- `--local-demo` skips service registration and installs only the essentials.
- `--with-llm` additionally downloads the TinyLlama GGUF model for local LLM responses (~600 MB).

### 3. Run Assistant

```bash
./run_envy_local.sh --profile balanced
```

Use `--profile low` for CPU-only mode, or `--profile power` once larger GPU models are installed. Add `--no-gui` for headless operation.

### 4. Enable systemd Service (Optional)

```bash
sudo cp packaging/systemd/envy.service /etc/systemd/system/envy.service
sudo systemctl daemon-reload
sudo systemctl enable envy --now
```

The unit expects Envy to live in `~/envy`. Adjust `WorkingDirectory` and `ExecStart` paths if you deploy elsewhere.

### 5. Install Optional GPU Acceleration

```bash
./.venv/bin/pip install llama-cpp-python[gpu]
```

Ensure CUDA toolkit is installed. Update `config/envy.yaml` to point to a GPU-friendly GGUF model.

### 6. Verify

```bash
source .venv/bin/activate
pytest
python -m envy.main demo
```

### Troubleshooting

- **Wake model missing:** run `bash scripts/download_models.sh`.
- **Audio device errors:** check `arecord -l`; update ALSA device index in `config/envy.yaml`.
- **Dashboard inaccessible:** ensure port 8420 is open and the process wasn’t started with `--no-gui`.
