# Windows Installation Guide (Intel i3 + GTX 1070)

Instructions for installing Envy on Windows 11 (or 10) with Intel i3 CPU, NVIDIA GTX 1070 (8 GB VRAM), and 16 GB RAM.

## 1. Prerequisites

- Python 3.10+ (from python.org; enable “Add to PATH”).
- Visual Studio Build Tools (for `vosk`/`pyttsx3` wheels, often optional).
- Git for Windows.
- Optional: NVIDIA drivers + CUDA toolkit for GPU acceleration.

## 2. Clone & Enter Repo (PowerShell)

```powershell
git clone https://github.com/your-org/envy.git
cd envy
```

## 3. Install Dependencies

```powershell
.\install_envy.bat           # optional: --profile power --llm
```

This script:
- Creates `.envy-venv` under the repo.
- Installs Python dependencies.
- Downloads Vosk small English model to `artifacts\models`.
- Optionally downloads TinyLlama with `--llm`.
- Sets the active profile in `config\envy.yaml`.

## 4. Microphone & Audio

- Ensure microphone works (Settings → System → Sound → Input).
- Update `config\envy.yaml` if you need a specific device index (advanced).

## 5. Running Envy

```powershell
.\run_envy_local.bat --profile balanced
```

Headless mode:

```powershell
.\run_envy_local.bat --profile low --no-gui
```

Dashboard: http://127.0.0.1:5030

## 6. Windows Service (Optional)

```powershell
pwsh installers/windows/install_service.ps1 -ServiceName EnvyAssistant -Profile balanced
Start-Service EnvyAssistant
```

The service runs `start-envy.bat` at boot with the chosen profile. Stop with:

```powershell
Stop-Service EnvyAssistant
```

Remove service:

```powershell
sc.exe delete EnvyAssistant
```

## 7. GPU Acceleration (Optional)

- Install CUDA toolkit and cuBLAS runtime to enable llama.cpp GPU layers.
- Edit `config\envy.yaml` to set:

```yaml
llm:
  local:
    enabled: true
    model_path: artifacts/models/tinyllama-1.1b-chat.gguf
    gpu_layers: 20
```

## 8. Verification

```powershell
.\.envy-venv\Scripts\activate
pytest
python scripts\perf_report.py
```

Logs and artifacts live in `artifacts\`.

