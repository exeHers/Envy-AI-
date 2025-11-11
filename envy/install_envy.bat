@echo off
setlocal enabledelayedexpansion

set REPO_ROOT=%~dp0
set VENV_DIR=%REPO_ROOT%\.venv
set LOG_DIR=%REPO_ROOT%\artifacts
set LOG_FILE=%LOG_DIR%\install-log.txt

if not exist "%LOG_DIR%" (
    mkdir "%LOG_DIR%"
)

echo === Envy installer started %DATE% %TIME% === > "%LOG_FILE%"

echo [1/5] Creating virtual environment at %VENV_DIR% >> "%LOG_FILE%"
if not exist "%VENV_DIR%" (
    python -m venv "%VENV_DIR%" >> "%LOG_FILE%" 2>&1
)

call "%VENV_DIR%\Scripts\activate.bat"

echo [2/5] Upgrading pip >> "%LOG_FILE%"
pip install --upgrade pip >> "%LOG_FILE%" 2>&1

echo [3/5] Installing Envy package >> "%LOG_FILE%"
pip install -e "%REPO_ROOT%" >> "%LOG_FILE%" 2>&1

echo [4/5] Downloading models >> "%LOG_FILE%"
python "%REPO_ROOT%\scripts\download_models.py" --profile balanced --root "%REPO_ROOT%" >> "%LOG_FILE%" 2>&1

echo [5/5] Preparing runtime directories >> "%LOG_FILE%"
if not exist "%REPO_ROOT%\artifacts\tests" mkdir "%REPO_ROOT%\artifacts\tests"
if not exist "%REPO_ROOT%\artifacts\logs" mkdir "%REPO_ROOT%\artifacts\logs"
if not exist "%REPO_ROOT%\workspace" mkdir "%REPO_ROOT%\workspace"

echo Installer complete. >> "%LOG_FILE%"
echo Next steps:
echo   call "%VENV_DIR%\Scripts\activate.bat"
echo   python -m envy.cli run --audio-file tests\data\wake_command.wav --profile balanced

endlocal
