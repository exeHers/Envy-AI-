## Windows Installation Guide

Target hardware: Intel i3 CPU, GTX 1070 (8 GB VRAM), 16 GB RAM. Tested on Windows 11 Pro.

### 1. Prerequisites

- [Python 3.11](https://www.python.org/downloads/windows/) (install with “Add python.exe to PATH”)
- [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) (Desktop C++ workload) for wheels that need compilation
- [Git for Windows](https://git-scm.com/download/win)
- Optional: [NSSM](https://nssm.cc/download) for Windows services

### 2. Clone & Install

Open **Windows Terminal (PowerShell)**:

```powershell
git clone https://github.com/your-org/envy.git
cd envy
.\install_envy.bat -LocalDemo
```

The installer creates `.venv\`, installs dependencies, and downloads the small Vosk model. Logs are written to `artifacts\install-log.txt`.

To grab heavier models later:

```powershell
.\scripts\download_models.ps1 -Mode full
```

### 3. Running Locally

```powershell
.\run_envy_local.bat --profile balanced --no-gui
```

To include the dashboard (`http://localhost:8300`):

```powershell
.\run_envy_local.bat --profile balanced
```

Default dashboard credentials: `envy` / `envy` (change via `config/envy.yaml`).

### 4. Windows Service (Optional)

1. Install [NSSM](https://nssm.cc/download) and add it to `PATH`.
2. Copy Envy to a permanent location, e.g. `C:\Envy`.
3. Register the service:

```powershell
cd C:\Envy
.\packaging\windows\install-envy-service.ps1 -Action install -InstallPath C:\Envy -Profile balanced
```

4. Start the service:

```powershell
nssm start EnvyAssistant
```

To remove:

```powershell
.\packaging\windows\install-envy-service.ps1 -Action remove
```

### 5. Audio & Permissions

- Ensure a microphone is available (Settings → System → Sound → Input).
- If audio capture fails, allow microphone access under Settings → Privacy → Microphone.
- Adjust `wake_listener.energy_threshold` in `config/envy.yaml` if the wake word misfires.

### 6. GPU (Optional)

- Install latest NVIDIA drivers.
- The default profile will attempt GPU acceleration where supported. Toggle via `config/envy.yaml` (`stt.enable_gpu`, `llm.llama_cpp.gpu_layers`).

### 7. Logs & Data

- Runtime logs: `artifacts\logs\envy.log`
- Session artifacts: `artifacts\sessions\`
- Test output: `artifacts\tests\`

### 8. Updating

```powershell
git pull
.\.venv\Scripts\activate
pip install -e .
```

Run `.\scripts\download_models.ps1 -Mode demo` again if you removed downloaded models.
