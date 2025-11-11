param(
    [string]$InstallPath = "C:\Envy",
    [string]$Profile = "balanced",
    [string]$ServiceName = "EnvyAssistant",
    [string]$NssmPath = "C:\nssm\nssm.exe"
)

if (-not (Test-Path $NssmPath)) {
    Write-Error "nssm.exe not found at $NssmPath. Download from https://nssm.cc/download and update the path."
    exit 1
}

if (-not (Test-Path $InstallPath)) {
    New-Item -ItemType Directory -Path $InstallPath | Out-Null
}

Copy-Item -Recurse -Force "$PSScriptRoot\..\*" $InstallPath

$runScript = Join-Path $InstallPath "run_envy_local.bat"

& $NssmPath install $ServiceName $runScript "--profile" $Profile "--headless"
& $NssmPath set $ServiceName AppDirectory $InstallPath
& $NssmPath set $ServiceName AppStdout "$InstallPath\artifacts\envy-service.log"
& $NssmPath set $ServiceName AppStderr "$InstallPath\artifacts\envy-service.log"
& $NssmPath set $ServiceName Start SERVICE_AUTO_START

Write-Host "Service $ServiceName installed. Use 'nssm start $ServiceName' to launch."
