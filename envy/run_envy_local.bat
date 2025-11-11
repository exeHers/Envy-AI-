@echo off
REM Quick start script for Envy (Windows)
REM MIT License

REM Check if venv exists
if not exist "venv" (
    echo Virtual environment not found. Running installer...
    call install_envy.bat
)

REM Activate venv
call venv\Scripts\activate.bat

REM Start Envy
echo 🤖 Starting Envy...
python main.py --profile balanced
