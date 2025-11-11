@echo off
REM Envy AI Assistant - Windows Installer
REM Installs dependencies and sets up the environment

echo ======================================================================
echo Envy AI Assistant - Installation Script (Windows)
echo ======================================================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

echo Installation directory: %SCRIPT_DIR%
echo.

REM Step 1: Check Python version
echo Step 1: Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%
echo [OK] Python version OK
echo.

REM Step 2: Create virtual environment
echo Step 2: Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

call venv\Scripts\activate.bat
echo [OK] Virtual environment activated
echo.

REM Step 3: Upgrade pip
echo Step 3: Upgrading pip...
python -m pip install --upgrade pip
echo [OK] Pip upgraded
echo.

REM Step 4: Install Python dependencies
echo Step 4: Installing Python dependencies...
echo This may take several minutes...
pip install -r requirements.txt
echo [OK] Python dependencies installed
echo.

REM Step 5: Create directories
echo Step 5: Creating directories...
if not exist "models" mkdir models
if not exist "data" mkdir data
if not exist "workspace" mkdir workspace
if not exist "artifacts" mkdir artifacts
if not exist "artifacts\tests" mkdir artifacts\tests
if not exist "artifacts\logs" mkdir artifacts\logs
if not exist "artifacts\research" mkdir artifacts\research
echo [OK] Directories created
echo.

REM Step 6: Download models
echo Step 6: Setting up AI models...
echo Models will be downloaded on first run if not present
echo.

REM Check for VOSK model
if not exist "models\vosk-model-small-en-us-0.15" (
    echo VOSK model not found - will download on first run
) else (
    echo [OK] VOSK model present
)

REM Check for LLM model
if not exist "models\tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" (
    echo LLM model not found - will download on first run
    echo Note: This is a 670MB download
) else (
    echo [OK] LLM model present
)
echo.

REM Step 7: Create run scripts
echo Step 7: Creating run scripts...

REM Create run script
echo @echo off > run_envy_local.bat
echo REM Run Envy AI Assistant locally >> run_envy_local.bat
echo. >> run_envy_local.bat
echo set SCRIPT_DIR=%%~dp0 >> run_envy_local.bat
echo cd /d "%%SCRIPT_DIR%%" >> run_envy_local.bat
echo. >> run_envy_local.bat
echo REM Activate venv >> run_envy_local.bat
echo if exist "venv\Scripts\activate.bat" call venv\Scripts\activate.bat >> run_envy_local.bat
echo. >> run_envy_local.bat
echo REM Parse profile argument >> run_envy_local.bat
echo set PROFILE=balanced >> run_envy_local.bat
echo if not "%%1"=="" set PROFILE=%%1 >> run_envy_local.bat
echo. >> run_envy_local.bat
echo echo Starting Envy AI Assistant (profile: %%PROFILE%%)... >> run_envy_local.bat
echo python envy_main.py --config config\envy.yaml --profile %%PROFILE%% >> run_envy_local.bat
echo. >> run_envy_local.bat
echo pause >> run_envy_local.bat

echo [OK] Run script created: run_envy_local.bat
echo.

REM Step 8: Create service wrapper (optional)
echo Step 8: Creating Windows service wrapper...
echo Note: Service installation requires administrator privileges
echo Use 'sc create' or NSSM to install as service
echo.

REM Installation complete
echo ======================================================================
echo [OK] Installation Complete!
echo ======================================================================
echo.
echo To start Envy AI Assistant:
echo   run_envy_local.bat
echo.
echo To run tests:
echo   cd tests
echo   python test_code_skill.py
echo.
echo To access the web dashboard (after starting):
echo   http://localhost:8080
echo.
echo Configuration file:
echo   config\envy.yaml
echo.
echo ======================================================================

REM Save installation log
set LOG_FILE=artifacts\install-log.txt
echo Installation completed at %date% %time% > "%LOG_FILE%"
echo Python version: %PYTHON_VERSION% >> "%LOG_FILE%"
echo Installation directory: %SCRIPT_DIR% >> "%LOG_FILE%"
echo [OK] Installation log saved: %LOG_FILE%

echo.
pause
