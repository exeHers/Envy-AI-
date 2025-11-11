@echo off
REM download_models.bat - Windows model downloader
setlocal

set MODELS_DIR=%~dp0..\models
if not exist "%MODELS_DIR%" mkdir "%MODELS_DIR%"

echo Downloading models for Envy...

REM Download VOSK model
set VOSK_MODEL_URL=https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
set VOSK_MODEL_DIR=%MODELS_DIR%\vosk-wake

if not exist "%VOSK_MODEL_DIR%" (
    echo Downloading VOSK model...
    curl -L -o "%TEMP%\vosk-model.zip" "%VOSK_MODEL_URL%"
    powershell -Command "Expand-Archive -Path '%TEMP%\vosk-model.zip' -DestinationPath '%MODELS_DIR%' -Force"
    move "%MODELS_DIR%\vosk-model-small-en-us-0.15" "%VOSK_MODEL_DIR%"
    del "%TEMP%\vosk-model.zip"
    echo VOSK model downloaded
) else (
    echo VOSK model already exists
)

echo.
echo Model download complete!
