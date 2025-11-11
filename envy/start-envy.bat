@echo off
set ROOT_DIR=%~dp0
set ARTIFACTS_DIR=%ROOT_DIR%artifacts
if not exist "%ARTIFACTS_DIR%" mkdir "%ARTIFACTS_DIR%"

set PROFILE=%~1
if "%PROFILE%"=="" set PROFILE=balanced

start /B "" "%ROOT_DIR%run_envy_local.bat" --profile %PROFILE% --headless > "%ARTIFACTS_DIR%\envy-service.log" 2>&1
echo Started Envy service in background.
