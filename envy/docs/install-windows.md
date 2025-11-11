# Install Envy on Windows 10/11 (Intel i3 + GTX 1070)

## 1. Prerequisites

- Windows 10/11 64-bit.
- Python 3.10+ from [python.org](https://www.python.org/downloads/) (enable “Add to PATH”).
- [Git for Windows](https://git-scm.com/download/win).
- Optional: [NSSM](https://nssm.cc/) for Windows services.
- Audio drivers: ensure microphone and speakers are enabled in system settings.

## 2. Clone and Install

Launch “Developer Command Prompt” or PowerShell:

```powershell
git clone https://github.com/you/envy.git
cd envy
.\install_envy.bat
```

The installer creates `.venv`, installs dependencies, downloads Vosk model, and writes progress to `artifacts\install-log.txt`.

## 3. Run a Demo Session

```powershell
.\run_envy_local.bat --audio-file tests\data\wake_command.wav --profile balanced --no-dashboard
```

Outputs:

- `wake word detected` log line.
- `workspace\test.py` containing `print("hello from envy")`.
- `artifacts\tts-output.wav` containing synthesized audio (uses SAPI5 voices).

## 4. Enable Dashboard

```powershell
.\run_envy_local.bat --profile balanced --dashboard
```

Open http://localhost:8765 to confirm or reject sensitive actions.

## 5. Optional Power Profile

Requires ≥8 GB VRAM and llama.cpp support:

```powershell
python scripts\download_models.py --profile power --root .
.\run_envy_local.bat --profile power --dashboard
```

Set `setx LLAMA_CUBLAS 1` to enable GPU acceleration before running.

## 6. Windows Service (NSSM)

```powershell
powershell -ExecutionPolicy Bypass -File deploy\windows\envy_service_wrapper.ps1 -InstallPath C:\Envy -ServiceName EnvyAssistant
nssm start EnvyAssistant
```

Logs stream to `C:\Envy\logs\envy-service.log`.

## 7. Troubleshooting

- **Vosk model missing**: rerun `python scripts\download_models.py --profile balanced`.
- **pyttsx3 errors**: ensure “Microsoft Speech Platform” voices installed; fallback tone synthesis keeps pipeline alive.
- **Port 8765 in use**: adjust `web.port` in `config\envy.yaml`.
- **Mic access denied**: grant microphone permissions in Windows Privacy settings.

## 8. Updates

```powershell
git pull
.\install_envy.bat
```
