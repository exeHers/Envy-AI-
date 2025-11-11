@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
set "VENV=%ROOT%\.envy-venv"
set "PROFILE=balanced"
set DOWNLOAD_LLM=0

:parse_args
if "%~1"=="" goto done_args
if "%~1"=="--venv" (
    set "VENV=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="--profile" (
    set "PROFILE=%~2"
    shift
    shift
    goto parse_args
)
if "%~1"=="--llm" (
    set DOWNLOAD_LLM=1
    shift
    goto parse_args
)
if "%~1"=="--local-demo" (
    rem default option, no action needed
    shift
    goto parse_args
)
if "%~1"=="--help" (
    echo Usage: install_envy.bat [--venv PATH] [--profile NAME] [--llm]
    exit /b 0
)
echo Unknown option: %~1
exit /b 1

:done_args

echo [install] Creating virtual environment at %VENV%
python -m venv "%VENV%"
call "%VENV%\Scripts\activate.bat"

python -m pip install --upgrade pip build wheel
python -m pip install "%ROOT%[dev]"

set "MODEL_ARGS="
if %DOWNLOAD_LLM%==1 set MODEL_ARGS=--llm
python "%ROOT%\scripts\download_models.py" %MODEL_ARGS%

python - <<PY
import yaml
from pathlib import Path

config_path = Path(r"%ROOT%\config\envy.yaml")
data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
data["active_profile"] = r"%PROFILE%"
config_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
PY

echo [install] Done.
exit /b 0
