@echo off
setlocal enabledelayedexpansion

set ROOT_DIR=%~dp0
set ROOT_DIR=%ROOT_DIR:~0,-1%
set ARTIFACTS_DIR=%ROOT_DIR%\artifacts
set LOG_FILE=%ARTIFACTS_DIR%\install-log.txt
set VENV_DIR=%ROOT_DIR%\.venv
set PYTHON_EXE=%PYTHON%
if "%PYTHON_EXE%"=="" set PYTHON_EXE=python
set MODELS_MODE=--minimal

if not exist "%ARTIFACTS_DIR%" mkdir "%ARTIFACTS_DIR%"

echo [%date% %time%] Starting Envy installation...>>"%LOG_FILE%"

for %%A in (%*) do (
  if "%%A"=="--full-models" set MODELS_MODE=--full
)

if not exist "%VENV_DIR%" (
  echo Creating virtual environment at %VENV_DIR%>>"%LOG_FILE%"
  %PYTHON_EXE% -m venv "%VENV_DIR%" >>"%LOG_FILE%" 2>&1
  if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Standard venv failed; falling back to virtualenv>>"%LOG_FILE%"
    %PYTHON_EXE% -m pip install --upgrade virtualenv>>"%LOG_FILE%" 2>&1
    %PYTHON_EXE% -m virtualenv "%VENV_DIR%">>"%LOG_FILE%" 2>&1
  )
)

call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install --upgrade pip wheel>>"%LOG_FILE%" 2>&1
python -m pip install ".[tests]">>"%LOG_FILE%" 2>&1

call "%ROOT_DIR%\scripts\download_models.bat" %MODELS_MODE%>>"%LOG_FILE%" 2>&1

echo [%date% %time%] Installation complete.>>"%LOG_FILE%"

endlocal
