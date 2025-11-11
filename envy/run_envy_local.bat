@echo off
set SCRIPT_DIR=%~dp0
if "%~1"=="" (
  call "%SCRIPT_DIR%start-envy.bat" --profile balanced
) else (
  call "%SCRIPT_DIR%start-envy.bat" %*
)
