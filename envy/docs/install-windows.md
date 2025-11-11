# Envy Windows Installation Guide

Minimum target: Windows 10/11 with Intel i3 CPU, GTX 1070 (8 GB), 16 GB RAM.

## 1. Prerequisites

- [Python 3.10+](https://www.python.org/downloads/windows/) (enable “Add python.exe to PATH”).
- [Git for Windows](https://git-scm.com/download/win).
- Optional: [NSSM](https://nssm.cc/download) if you plan to run Envy as a Windows service.

## 2. Clone and Install

Open PowerShell:

```powershell
git clone https://example.com/envy.git
cd envy
.\install_envy.bat --local-demo
```

`--local-demo` skips the TinyLlama model (recommended while you test). Omit it to download the full offline bundle.

## 3. Audio Devices

Determine the microphone device ID:

```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```

Edit `config\envy.yaml` and set `audio.device` to the desired index (or leave empty to auto-select).

## 4. Running Envy

```powershell
.\run_envy_local.bat --profile balanced
```

Dashboard: <http://localhost:8190>. Headless mode:

```powershell
.\run_envy_local.bat --profile balanced --headless
```

## 5. Windows Service

1. Download and extract NSSM (e.g., to `C:\nssm\nssm.exe`).
2. Install the service from PowerShell:

   ```powershell
   cd envy\windows
   .\install_service.ps1 -InstallPath "C:\Envy" -NssmPath "C:\nssm\nssm.exe"
   ```

3. Start the service:

   ```powershell
   nssm start EnvyAssistant
   ```

Logs appear under `C:\Envy\artifacts\envy-service.log`.

## 6. GPU Acceleration (Optional)

- Install the latest NVIDIA drivers.
- Install CUDA (if you plan to rebuild llama.cpp with GPU support). By default Envy uses CPU inference unless `llama-cpp-python` detects CUDA.

## 7. Troubleshooting

- **pyttsx3 voices missing**: install the Microsoft Speech Platform or ensure the English voices are available in Windows settings.
- **Wake word not triggered**: verify microphone privacy settings permit desktop apps to access audio input.
- **Port 8190 in use**: change `dashboard.port` in `config\envy.yaml`.
- **Service fails to start**: inspect the log at `C:\Envy\artifacts\envy-service.log` and confirm the virtual environment exists (`C:\Envy\.venv`).

## 8. Updating

```powershell
cd envy
git pull
call .\.venv\Scripts\activate.bat
pip install -e .
```

Re-run `python scripts\download_models.py` if models were updated upstream.
