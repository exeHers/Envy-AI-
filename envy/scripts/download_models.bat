@echo off
set MODE=%1
if "%MODE%"=="" set MODE=--minimal

set ROOT_DIR=%~dp0
set ROOT_DIR=%ROOT_DIR:~0,-1%
set MODELS_DIR=%ROOT_DIR%\models
set VOSK_DIR=%MODELS_DIR%\vosk-model-small-en-us

if not exist "%MODELS_DIR%" mkdir "%MODELS_DIR%"

if "%MODE%"=="--minimal" (
  if not exist "%VOSK_DIR%" mkdir "%VOSK_DIR%"
  >"%VOSK_DIR%\README.txt" echo Envy minimal model placeholder.^
For full wake-word quality, run download_models.bat --full
  echo Created placeholder Vosk directory at %VOSK_DIR%
  exit /b 0
)

if "%MODE%"=="--full" (
  set ZIP_PATH=%MODELS_DIR%\vosk-model-small-en-us-0.15.zip
  if not exist "%ZIP_PATH%" (
    echo Downloading Vosk small English model...
    powershell -Command "Invoke-WebRequest -Uri 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip' -OutFile '%ZIP_PATH%'"
  ) else (
    echo Vosk model archive already present.
  )
  rmdir /s /q "%VOSK_DIR%" 2>nul
  powershell -Command "Expand-Archive -Force '%ZIP_PATH%' '%MODELS_DIR%'"
  ren "%MODELS_DIR%\vosk-model-small-en-us-0.15" "vosk-model-small-en-us"
  echo Vosk model extracted to %VOSK_DIR%
  exit /b 0
)

echo Unknown option %MODE%
exit /b 1
