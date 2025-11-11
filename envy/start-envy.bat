@echo off
setlocal
set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%venv
if exist "%SCRIPT_DIR%.venv" (
  set VENV_DIR=%SCRIPT_DIR%.venv
)

if exist "%VENV_DIR%\Scripts\activate.bat" (
  call "%VENV_DIR%\Scripts\activate.bat"
)

set PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%
python -m envy.main %*
endlocal
