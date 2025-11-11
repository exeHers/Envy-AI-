# Envy Installation — Linux (Intel i3 + GTX 1070)

These steps assume Ubuntu 22.04+ on an Intel i3 with an NVIDIA GTX 1070 (8 GB) and 16 GB RAM. Commands are executed from the repository root (`envy/`).

## 1. System Packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential \
    portaudio19-dev libasound2-dev ffmpeg curl unzip git
```

If you plan to leverage the GPU, install the NVIDIA driver + CUDA toolkit that matches your card, and ensure `nvidia-smi` works.

## 2. Clone & Install

```bash
git clone https://github.com/your-org/envy.git
cd envy
./install_envy.sh --local-demo
```

The installer will:

1. Create `.venv/` with Python dependencies
2. Download the Vosk wake/STT model to `models/`
3. Generate demo audio fixtures used by automated tests
4. Render `deploy/systemd/envy.generated.service` with your paths

Logs are emitted to `artifacts/install-log.txt`.

## 3. Run the Assistant

```bash
./run_envy_local.sh --profile balanced --no-gui
```

The assistant listens for pre-recorded sample audio (or a live mic if configured) and logs to `logs/envy.log`. Visit the dashboard at http://localhost:8080 for live status and confirmation prompts.

## 4. Systemd Service (Optional)

```bash
sudo cp deploy/systemd/envy.generated.service /etc/systemd/system/envy.service
sudo systemctl daemon-reload
sudo systemctl enable --now envy
sudo systemctl status envy
```

Logs rotate under `logs/` and `journalctl -u envy`. Use `systemctl edit envy` to customise environment variables (e.g., `ENVY_PROFILE=power` for GPU-assisted mode).

## 5. GPU-Accelerated LLM (Optional)

```bash
./scripts/download_models.sh --tinyllama
```

Edit `config/envy.yaml` → `llm.strategies.local`/`gpu` to point to the new GGUF model. Install [llama.cpp](https://github.com/ggerganov/llama.cpp) or compatible runtime if you intend to run full LLM inference instead of the default stub.

## 6. Verification

```bash
python3 -m pytest
./artifacts/perf-report-gen.sh
```

Artifacts from tests live in `artifacts/tests/`; performance metrics are stored in `artifacts/perf-report.txt` and `.json`.

## 7. Uninstall / Cleanup

```bash
sudo systemctl disable --now envy  # if installed
rm -rf .venv models runtime logs artifacts/tests workspace/test.py
```

Keep `models/` if you plan to reuse downloaded assets later.
