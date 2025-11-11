param(
    [ValidateSet("install", "remove")]
    [string]$Action = "install",
    [string]$InstallPath = "C:\Envy",
    [string]$Profile = "balanced",
    [string]$ServiceName = "EnvyAssistant"
)

function Require-Tool($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Error "$name not found in PATH. Please install NSSM from https://nssm.cc/."
        exit 1
    }
}

Require-Tool -name "nssm"

if ($Action -eq "remove") {
    Write-Host "[service] Removing service $ServiceName"
    nssm remove $ServiceName confirm
    exit 0
}

$startScript = Join-Path $InstallPath "start-envy.bat"
if (-not (Test-Path $startScript)) {
    Write-Error "[service] start-envy.bat not found at $startScript"
    exit 1
}

Write-Host "[service] Installing service $ServiceName targeting $startScript"
nssm install $ServiceName $startScript "--profile" $Profile "--no-dashboard"
nssm set $ServiceName AppDirectory $InstallPath
nssm set $ServiceName Start SERVICE_AUTO_START
nssm set $ServiceName AppEnvironmentExtra "ENVY_PROFILE=$Profile"
nssm set $ServiceName AppEnvironmentExtra "ENVY_CONFIG_PATH=$InstallPath\config\envy.yaml"
Write-Host "[service] Service $ServiceName installed. Use 'nssm start $ServiceName' to launch."
