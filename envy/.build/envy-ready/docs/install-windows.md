## Windows Installation Guide

### Prerequisites

- Windows 10/11 (64-bit)
- Python 3.10+ from the Microsoft Store or python.org (ensure “Add to PATH” is enabled)
- Git Bash or WSL for running shell scripts (recommended)
- Optional: NVIDIA driver + CUDA toolkit for GPU acceleration

### Installation Steps

1. **Clone the repository**

   ```powershell
   git clone https://example.com/envy.git
   cd envy
   ```

2. **Run the installer**

   ```powershell
   install_envy.bat
   ```

   Add `--with-llm` to download the TinyLlama GGUF model. The script creates `.venv`, installs dependencies, and downloads the VOSK speech model via `scripts/download_models.sh` (requires Git Bash or WSL).

3. **Start Envy**

   ```powershell
   start-envy.bat --profile balanced --no-gui
   ```

   Remove `--no-gui` to enable the FastAPI dashboard at `http://localhost:8420`.

4. **Register as a Service (Optional)**

   Use [NSSM](https://nssm.cc/) to wrap `packaging/windows/envy_service_wrapper.py`:

   ```powershell
   nssm install EnvyService "C:\Python310\python.exe" "C:\path\to\envy\packaging\windows\envy_service_wrapper.py"
   nssm set EnvyService Start SERVICE_AUTO_START
   nssm start EnvyService
   ```

5. **Run Tests**

   ```powershell
   .\.venv\Scripts\activate
   pytest
   python -m envy.main demo
   ```

### Troubleshooting

- **VOSK model missing:** run `bash scripts/download_models.sh` from Git Bash.
- **No audio playback:** ensure a default playback device is selected and accessible.
- **Permission issues:** run PowerShell as Administrator when installing a service or writing into protected directories.
