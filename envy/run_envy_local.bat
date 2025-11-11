@echo off
setlocal ENABLEDELAYEDEXPANSION

set "SCRIPT_DIR=%~dp0"
set "PROFILE=balanced"
set "DASHBOARD=1"

:parse
if "%~1"=="" goto done
if /I "%~1"=="--profile" (
    set "PROFILE=%~2"
    shift
    shift
    goto parse
)
if /I "%~1"=="--no-gui" (
    set "DASHBOARD=0"
    shift
    goto parse
)
if /I "%~1"=="--no-dashboard" (
    set "DASHBOARD=0"
    shift
    goto parse
)
set "EXTRA_ARGS=%EXTRA_ARGS% %~1"
shift
goto parse

:done

set "CMD_ARGS=--profile %PROFILE%%EXTRA_ARGS%"
if "%DASHBOARD%"=="0" (
    set "CMD_ARGS=%CMD_ARGS% --no-dashboard"
)

call "%SCRIPT_DIR%start-envy.bat" %CMD_ARGS%

endlocal
