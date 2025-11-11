@echo off
setlocal enabledelayedexpansion

set ROOT_DIR=%~dp0
set ARTIFACTS_DIR=%ROOT_DIR%artifacts
set LOG_FILE=%ARTIFACTS_DIR%\install-log.txt
set VENV_DIR=%ROOT_DIR%\.venv

if not exist "%ARTIFACTS_DIR%" mkdir "%ARTIFACTS_DIR%"
if not exist "%LOG_FILE%" type NUL > "%LOG_FILE%"

set PROFILE=balanced
set SKIP_LLM=false

:parse_args
if "%~1"=="" goto end_parse
if /I "%~1"=="--local-demo" (
  set PROFILE=balanced
  set SKIP_LLM=true
  shift
  goto parse_args
)
if /I "%~1"=="--skip-llm" (
  set SKIP_LLM=true
  shift
  goto parse_args
)
if /I "%~1"=="--profile" (
  set PROFILE=%~2
  shift & shift
  goto parse_args
)
echo Unknown argument: %~1 >> "%LOG_FILE%"
exit /b 1
:end_parse

echo [install] Starting installation at %date% %time% >> "%LOG_FILE%"

if not exist "%VENV_DIR%" (
  echo [install] Creating virtual environment. >> "%LOG_FILE%"
  python -m venv "%VENV_DIR%" >> "%LOG_FILE%" 2>&1
)

call "%VENV_DIR%\Scripts\activate.bat"

echo [install] Upgrading pip. >> "%LOG_FILE%"
pip install --upgrade pip wheel setuptools >> "%LOG_FILE%" 2>&1

echo [install] Installing project dependencies. >> "%LOG_FILE%"
pip install -e ".[dev]" >> "%LOG_FILE%" 2>&1

if /I "%SKIP_LLM%"=="true" (
  set SKIP_LLM_DOWNLOAD=1
  echo [install] Downloading audio models only. >> "%LOG_FILE%"
) else (
  set SKIP_LLM_DOWNLOAD=
  echo [install] Downloading models (including LLM). >> "%LOG_FILE%"
)

python "%ROOT_DIR%scripts\download_models.py" >> "%LOG_FILE%" 2>&1

if not exist "%ROOT_DIR%data" mkdir "%ROOT_DIR%data"
if not exist "%ARTIFACTS_DIR%\tests" mkdir "%ARTIFACTS_DIR%\tests"
if not exist "%ARTIFACTS_DIR%\logs" mkdir "%ARTIFACTS_DIR%\logs"

(
  echo VIRTUAL_ENV=%VENV_DIR%
  echo PROFILE=%PROFILE%
  echo PATH=%VENV_DIR%\Scripts;%%PATH%%
) > "%ROOT_DIR%envy.env"

echo [install] Installation complete. >> "%LOG_FILE%"

endlocal
exit /b 0
