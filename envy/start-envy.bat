@echo off
set ROOT_DIR=%~dp0
set ROOT_DIR=%ROOT_DIR:~0,-1%
set VENV_DIR=%ROOT_DIR%\.venv

if not exist "%VENV_DIR%" (
  echo Virtual environment missing at %VENV_DIR%. Run install_envy.bat first.
  exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
python -m envy %*
