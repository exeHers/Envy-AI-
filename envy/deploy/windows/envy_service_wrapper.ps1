param(
    [string]$InstallPath = "C:\Envy",
    [string]$ServiceName = "EnvyAssistant"
)

$startScript = Join-Path $InstallPath "start-envy.bat"
if (-not (Test-Path $startScript)) {
    Write-Error "start-envy.bat not found at $startScript. Install Envy before registering the service."
    exit 1
}

$nssm = Get-Command "nssm.exe" -ErrorAction SilentlyContinue
if (-not $nssm) {
    Write-Warning "nssm.exe not found on PATH. Install NSSM (https://nssm.cc/) and re-run this script."
    exit 1
}

& $nssm.Path install $ServiceName $startScript
& $nssm.Path set $ServiceName AppDirectory $InstallPath
& $nssm.Path set $ServiceName AppStdout (Join-Path $InstallPath "logs\envy-service.log")
& $nssm.Path set $ServiceName AppStderr (Join-Path $InstallPath "logs\envy-service.log")
& $nssm.Path set $ServiceName Start SERVICE_AUTO_START

Write-Host "Service '$ServiceName' registered. Start it with: nssm start $ServiceName"
