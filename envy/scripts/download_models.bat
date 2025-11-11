@echo off
REM Download models for Envy (Windows)
setlocal enabledelayedexpansion

set "BASE_DIR=%~dp0.."
set "MODEL_DIR=%BASE_DIR%\models"

echo === Envy Model Downloader (Windows) ===
echo Base directory: %BASE_DIR%
echo Model directory: %MODEL_DIR%
echo.

REM Create model directory
if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"

REM Check for required tools
where curl >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: curl not found. Please install curl or download models manually.
    echo.
    echo Manual download URLs:
    echo 1. VOSK small: https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    echo 2. VOSK medium: https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
    echo 3. TinyLlama: https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
    pause
    exit /b 1
)

echo 1. Downloading VOSK models...
echo.

REM VOSK small model
if not exist "%MODEL_DIR%\vosk-model-small-en-us-0.15" (
    echo Downloading VOSK small model...
    curl -L -o "%MODEL_DIR%\vosk-small.zip" "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    echo Extracting...
    powershell -command "Expand-Archive -Path '%MODEL_DIR%\vosk-small.zip' -DestinationPath '%MODEL_DIR%' -Force"
    del "%MODEL_DIR%\vosk-small.zip"
    echo [OK] VOSK small model installed
) else (
    echo [OK] VOSK small model already exists
)

REM VOSK medium model
if not exist "%MODEL_DIR%\vosk-model-en-us-0.22" (
    echo.
    echo Downloading VOSK medium model (large file, may take a while)...
    curl -L -o "%MODEL_DIR%\vosk-medium.zip" "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
    echo Extracting...
    powershell -command "Expand-Archive -Path '%MODEL_DIR%\vosk-medium.zip' -DestinationPath '%MODEL_DIR%' -Force"
    del "%MODEL_DIR%\vosk-medium.zip"
    echo [OK] VOSK medium model installed
) else (
    echo [OK] VOSK medium model already exists
)

echo.
echo 2. Downloading TinyLlama model...
echo.

REM TinyLlama model
if not exist "%MODEL_DIR%\tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" (
    echo Downloading TinyLlama (quantized, ~700MB)...
    curl -L -o "%MODEL_DIR%\tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    echo [OK] TinyLlama model installed
) else (
    echo [OK] TinyLlama model already exists
)

echo.
echo === Model Download Complete ===
echo.
echo Models are ready to use!
echo.
pause
