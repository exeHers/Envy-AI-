@echo off
setlocal enabledelayedexpansion

set ROOT_DIR=%~dp0
if "%ROOT_DIR:~-1%"=="\" set ROOT_DIR=%ROOT_DIR:~0,-1%
set VENV_DIR=%ROOT_DIR%\.venv
set ARTIFACTS_DIR=%ROOT_DIR%\artifacts
set LOG_FILE=%ARTIFACTS_DIR%\install-log.txt

if not exist "%ARTIFACTS_DIR%" mkdir "%ARTIFACTS_DIR%"
echo [install] Starting Envy installation on %date% %time% > "%LOG_FILE%"

py -3 -m venv "%VENV_DIR%"
call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1
python -m pip install ".[dev]" >> "%LOG_FILE%" 2>&1

if "%1"=="--with-llm" (
    bash scripts/download_models.sh --with-llm >> "%LOG_FILE%" 2>&1
) else (
    bash scripts/download_models.sh >> "%LOG_FILE%" 2>&1
)

echo [install] Installation complete. >> "%LOG_FILE%"
type "%LOG_FILE%"
endlocal
