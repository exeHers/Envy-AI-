@echo off
REM Download required models

if not exist "models" mkdir models
cd models

if not exist "vosk-model-small-en-us-0.15" (
    echo Downloading VOSK model...
    powershell -Command "Invoke-WebRequest -Uri 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip' -OutFile 'vosk-model.zip'"
    powershell -Command "Expand-Archive -Path 'vosk-model.zip' -DestinationPath '.'"
    del vosk-model.zip
    echo VOSK model downloaded
) else (
    echo VOSK model already exists
)

echo Models ready. Whisper models will be downloaded on first use.
