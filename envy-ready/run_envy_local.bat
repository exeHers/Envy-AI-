@echo off
cd /d "%~dp0"

if not exist "venv" (
    echo Virtual environment not found. Running installer...
    call scripts\install_envy.bat --local-demo
)

call venv\Scripts\activate.bat
python main.py %*
