@echo off
setlocal enabledelayedexpansion

set PROFILE=balanced
set EXTRA=

:parse
if "%1"=="" goto run
if "%1"=="--profile" (
  set PROFILE=%2
  shift
  shift
  goto parse
)
if "%1"=="--no-gui" (
  set EXTRA=!EXTRA! --no-dashboard
  shift
  goto parse
)
set EXTRA=!EXTRA! %1
shift
goto parse

:run
call "%~dp0start-envy.bat" --profile %PROFILE% %EXTRA%
endlocal
