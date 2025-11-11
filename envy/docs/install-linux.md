# Install Envy on Linux (Intel i3 + GTX 1070)

## 1. Prerequisites

- Ubuntu 20.04+ (tested on 24.04) or any modern Debian-based distro.
- Python 3.10 or newer (`sudo apt install python3 python3-venv python3-pip`).
- Audio stack: `sudo apt install portaudio19-dev pulseaudio-utils alsa-utils`.
- Optional GPU acceleration: NVIDIA proprietary driver + CUDA 11.8 or newer.

## 2. Clone and Install

```bash
git clone https://github.com/you/envy.git
cd envy
./install_envy.sh --local-demo   # low-usage profile, downloads Vosk model (~50 MB)
```

The installer writes progress to `artifacts/install-log.txt`, creates `.venv`, downloads models, and prepares `workspace/`.

## 3. Run a Demo

```bash
source .venv/bin/activate
python -m envy.cli run --audio-file tests/data/wake_command.wav --profile balanced --no-dashboard
```

Expected log snippets:

- `Wake word detected with confidence ...`
- `Created test.py with the requested changes.`
- `Synthesizing speech to artifacts/tts-output.wav`

Inspect `workspace/test.py` and `artifacts/tts-output.wav` afterwards.

## 4. Enable Balanced or Power Profiles

Balanced (default) is tuned for Intel i3 + GTX 1070:

```bash
./run_envy_local.sh --profile balanced --dashboard
```

Power profile switches STT → Whisper and LLM → llama.cpp, requiring more VRAM:

```bash
./scripts/download_models.py --profile power
./run_envy_local.sh --profile power --dashboard
```

## 5. Optional GPU Optimizations

- Install CUDA toolkit: `sudo apt install nvidia-cuda-toolkit`.
- Export `LLAMA_CUBLAS=1` before running the power profile to offload llama.cpp.
- Adjust `config/envy.yaml` (`profiles.power.gpu.max_vram_mb`) if you have more VRAM.

## 6. Run as a Service (systemd)

```bash
sudo cp deploy/systemd/envy.service /etc/systemd/system/envy.service
sudo nano /etc/systemd/system/envy.service   # update WorkingDirectory & ExecStart
sudo systemctl daemon-reload
sudo systemctl enable --now envy
```

Logs stream to `journalctl -u envy`.

## 7. Troubleshooting

- **Wake word not detected**: verify microphone input and `config/envy.yaml` → `audio.input_device`.
- **pyttsx3 failure**: ensure `espeak` and `ffmpeg` are installed (`sudo apt install espeak ffmpeg`).
- **GPU usage high**: switch to `--profile low` or raise `wake.sensitivity` for quicker gating.
- **Firewall**: dashboard listens on port 8765. Restrict to localhost if hosting publicly.

## 8. Updating

```bash
git pull
source .venv/bin/activate
pip install -e . --upgrade
./scripts/download_models.py --profile balanced
```
