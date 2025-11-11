@echo off
REM Envy Personal Assistant Installer for Windows
setlocal enabledelayedexpansion

echo =========================================
echo    Envy Personal Assistant Installer
echo =========================================
echo.

REM Get base directory
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

REM Check Python
echo 1. Checking Python...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.10 or higher from python.org
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))"') do set PYTHON_VERSION=%%i
echo    Found Python %PYTHON_VERSION%

REM Create virtual environment
echo.
echo 2. Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo    [OK] Virtual environment created
) else (
    echo    [OK] Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo 3. Upgrading pip...
python -m pip install --quiet --upgrade pip

REM Install dependencies
echo.
echo 4. Installing Python dependencies...
pip install --quiet -r requirements.txt
echo    [OK] Dependencies installed

REM Download models
echo.
echo 5. Downloading AI models...
call scripts\download_models.bat

REM Create directories
echo.
echo 6. Creating directories...
if not exist "logs" mkdir logs
if not exist "workspace" mkdir workspace
if not exist "artifacts\tests" mkdir artifacts\tests
if not exist "config" mkdir config
echo    [OK] Directories created

REM Create run script
echo.
echo 7. Creating run script...
(
echo @echo off
echo REM Start Envy Personal Assistant
echo.
echo set "BASE_DIR=%%~dp0"
echo cd /d "%%BASE_DIR%%"
echo.
echo REM Activate virtual environment
echo call venv\Scripts\activate.bat
echo.
echo REM Parse arguments
echo set "PROFILE=balanced"
echo set "NO_GUI=false"
echo.
echo :parse_args
echo if "%%1"=="--profile" ^(
echo     set "PROFILE=%%2"
echo     shift
echo     shift
echo     goto parse_args
echo ^)
echo if "%%1"=="--no-gui" ^(
echo     set "NO_GUI=true"
echo     shift
echo     goto parse_args
echo ^)
echo if "%%1" NEQ "" goto parse_args
echo.
echo REM Run Envy
echo echo Starting Envy Assistant ^(profile: %%PROFILE%%^)...
echo if "%%NO_GUI%%"=="true" ^(
echo     python envy_main.py --profile %%PROFILE%% --no-gui
echo ^) else ^(
echo     python envy_main.py --profile %%PROFILE%%
echo ^)
echo.
echo pause
) > run_envy_local.bat
echo    [OK] Run script created

echo.
echo =========================================
echo    Installation Complete!
echo =========================================
echo.
echo To start Envy:
echo    run_envy_local.bat
echo.
echo To run tests:
echo    venv\Scripts\activate.bat
echo    python -m pytest tests\
echo.
echo To start web dashboard:
echo    venv\Scripts\activate.bat
echo    python web\dashboard.py
echo.
echo Configuration file: config\envy.yaml
echo.

REM Save install log
echo Installation completed at %date% %time% > artifacts\install-log.txt
echo Python version: %PYTHON_VERSION% >> artifacts\install-log.txt
echo Base directory: %BASE_DIR% >> artifacts\install-log.txt

pause
