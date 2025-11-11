@echo off
setlocal

set REPO_ROOT=%~dp0
call "%REPO_ROOT%\run_envy_local.bat" --no-dashboard %*

endlocal
