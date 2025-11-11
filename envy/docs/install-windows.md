## Envy Installation — Windows 10/11 (Intel i3 + GTX 1070)

### 1. Prerequisites

- Windows 10/11 64-bit
- Python 3.11 (install from python.org; add to PATH)
- Git for Windows
- Optional: [NSSM](https://nssm.cc/download) for Windows service integration

### 2. GPU Drivers (Optional)

Install the latest NVIDIA Game Ready or Studio driver for the GTX 1070. CUDA is optional; llama.cpp can run on CPU. If you plan to enable GPU layers, install CUDA Toolkit 12.x and ensure `nvml.dll` is in PATH.

### 3. Clone & Install

Open “Developer Command Prompt” or PowerShell:

```powershell
git clone https://github.com/you/envy.git
cd envy
.\install_envy.bat --local-demo
```

The installer creates `.venv\`, installs dependencies, and writes logs to `artifacts\install-log.txt`.

### 4. Optional Model Downloads

Minimal mode creates placeholders. To fetch the real Vosk model:

```powershell
.\scripts\download_models.bat --full
```

Download a GGUF LLM (TinyLlama example):

```powershell
Invoke-WebRequest `
  -Uri https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf `
  -OutFile .\models\tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

Update `config/envy.yaml` to point the `balanced` profile to the GGUF path.

### 5. Run Envy

```powershell
.\run_envy_local.bat --profile balanced
# Headless mode
.\run_envy_local.bat --profile balanced --no-gui
```

Browse to `http://127.0.0.1:7010` for the dashboard (unless `--no-gui`).

### 6. Windows Service (Optional)

1. Download NSSM (32/64-bit matching your OS) and unzip it.
2. Install Envy as a service:

```powershell
.\scripts\windows\install_envy_service.bat C:\path\to\nssm.exe
```

This registers `EnvyAssistant`. Start it via Services.msc or:

```powershell
nssm start EnvyAssistant
```

### 7. Troubleshooting

- Missing `portaudio` DLL: install Microsoft Visual C++ Redistributable 2015-2022.
- Microphone access: allow the Envy process to access the microphone (Windows Settings → Privacy → Microphone).
- Firewall prompts: allow Python to listen on local ports 7000-7010.
- CUDA errors: reduce `gpu_layers` or switch provider to `stub` in `config/envy.yaml`.
