@echo off
setlocal

set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%venv
set LOG_FILE=%SCRIPT_DIR%artifacts\install-log.txt

echo [install] Envy installation started at %DATE% %TIME% > "%LOG_FILE%"

if not exist "%VENV_DIR%" (
  echo [setup] Creating virtualenv at %VENV_DIR% >> "%LOG_FILE%"
  python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install --upgrade pip wheel >> "%LOG_FILE%" 2>&1
python -m pip install -e "%SCRIPT_DIR%" >> "%LOG_FILE%" 2>&1

echo [models] Downloading Vosk model >> "%LOG_FILE%"
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\download_models.ps1" -Vosk >> "%LOG_FILE%" 2>&1

echo [audio] Generating demo audio >> "%LOG_FILE%"
python "%SCRIPT_DIR%tests\generate_test_audio.py" >> "%LOG_FILE%" 2>&1

echo [install] Completed. Activate with: call %VENV_DIR%\Scripts\activate.bat && start-envy.bat --profile balanced >> "%LOG_FILE%"

endlocal
