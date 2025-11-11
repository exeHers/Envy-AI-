@echo off
set "ROOT=%~dp0"
set "VENV=%ROOT%\.envy-venv"

if not exist "%VENV%" (
    echo [start] Virtualenv not found at %VENV%. Run install_envy.bat first.
    exit /b 1
)

call "%VENV%\Scripts\activate.bat"
python -m envy.core.service_launcher %*
