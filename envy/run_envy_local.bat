@echo off
setlocal enabledelayedexpansion

set ROOT_DIR=%~dp0
set VENV_DIR=%ROOT_DIR%\.venv

if not exist "%VENV_DIR%" (
  echo Virtual environment not found. Run install_envy.bat first.
  exit /b 1
)

set PROFILE=balanced
set HEADLESS=

:parse
if "%~1"=="" goto run
if /I "%~1"=="--profile" (
  set PROFILE=%~2
  shift & shift
  goto parse
)
if /I "%~1"=="--no-gui" (
  set HEADLESS=--headless
  shift
  goto parse
)
if /I "%~1"=="--headless" (
  set HEADLESS=--headless
  shift
  goto parse
)
echo Unknown argument: %~1
exit /b 1

:run
call "%VENV_DIR%\Scripts\activate.bat"
python -m envy.cli start --profile "%PROFILE%" %HEADLESS%
