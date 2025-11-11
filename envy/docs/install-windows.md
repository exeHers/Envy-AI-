# Envy Installation — Windows 10/11

These steps target Windows 10/11 with an Intel i3 and GTX 1070 (8 GB). Run PowerShell as Administrator unless noted otherwise.

## 1. Prerequisites

- [Python 3.10+](https://www.python.org/downloads/windows/) (ensure “Add to PATH” is enabled)
- Git for Windows
- Optional: [NVIDIA driver + CUDA toolkit](https://developer.nvidia.com/cuda-downloads) if you plan to run GPU-assisted LLMs

## 2. Clone & Install

```powershell
git clone https://github.com/your-org/envy.git
cd envy
.\install_envy.bat
```

The installer creates `venv\`, installs dependencies, downloads the Vosk model, and generates demo audio fixtures. Output is logged to `artifacts\install-log.txt`.

## 3. Run the Assistant

```powershell
.\run_envy_local.bat --profile balanced --no-gui
```

Visit http://localhost:8080 to open the dashboard. Logs are stored under `logs\envy.log` and TTS artifacts under `artifacts\tts-output.wav`.

## 4. Windows Service (Optional)

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\windows\install_envy_service.ps1
Start-Service EnvyAssistant
```

Use `Stop-Service EnvyAssistant` and `Remove-Service EnvyAssistant` (or rerun the PowerShell script) to manage or uninstall.

## 5. Optional LLM Download

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\download_models.ps1 -TinyLlama
```

Edit `config\envy.yaml` to point the local/gpu strategies at the downloaded GGUF file.

## 6. Verification

```powershell
python -m pytest
.\artifacts\perf-report-gen.sh    # Requires WSL/bash or run equivalent python module manually
```

Performance reports are written to `artifacts\perf-report.txt` (and `.json`). Consider installing WSL for the Bash helper scripts, or run `python -m envy.tools.perf_report --output artifacts\perf-report.txt` directly.

## 7. Troubleshooting

- If `pyttsx3` fails (missing SAPI voices), the assistant falls back to tone generation but still saves audio.
- Ensure microphone access is enabled under Windows privacy settings if you intend to use live audio.
- For GPU metrics, install the NVIDIA driver utilities (`nvidia-smi`) or rely on CPU-only statistics.

## 8. Cleanup

```powershell
Stop-Service EnvyAssistant
Remove-Service EnvyAssistant
Remove-Item -Recurse -Force .\venv .\models .\runtime .\logs .\artifacts\tests .\workspace\test.py
```

Keep `models\` if you plan to reuse downloaded assets.
