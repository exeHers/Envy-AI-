@echo off
if "%1"=="" (
  echo Usage: install_envy_service.bat ^<path_to_nssm.exe^>
  exit /b 1
)

set NSSM=%1
set ROOT_DIR=%~dp0
set ROOT_DIR=%ROOT_DIR:~0,-1%
set ENVY_DIR=%ROOT_DIR%\..
set SERVICE_NAME=EnvyAssistant

%NSSM% install %SERVICE_NAME% "%ENVY_DIR%\start-envy.bat" --profile balanced --no-dashboard
%NSSM% set %SERVICE_NAME% AppDirectory "%ENVY_DIR%"
%NSSM% set %SERVICE_NAME% DisplayName "Envy Personal Assistant"
%NSSM% set %SERVICE_NAME% Start SERVICE_AUTO_START
echo Envy service installed. Use 'nssm start %SERVICE_NAME%' to run.
