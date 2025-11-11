param(
    [string]$ServiceName = "EnvyAssistant",
    [string]$Profile = "balanced",
    [string]$RootPath = ""
)

if (-not $RootPath) {
    $RootPath = (Split-Path -Parent $MyInvocation.MyCommand.Path)
    $RootPath = Join-Path $RootPath "..\\.."
    $RootPath = (Resolve-Path $RootPath).Path
}

$startScript = Join-Path $RootPath "start-envy.bat"
if (-not (Test-Path $startScript)) {
    Write-Error "start-envy.bat not found at $startScript. Run install_envy.bat first."
    exit 1
}

$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Service $ServiceName already exists. Updating configuration..."
    sc.exe config $ServiceName binPath= "`"$startScript`" --profile $Profile" | Out-Null
} else {
    New-Service -Name $ServiceName `
        -BinaryPathName "`"$startScript`" --profile $Profile" `
        -DisplayName "Envy Assistant" `
        -Description "Jarvis-style voice assistant." `
        -StartupType Automatic
}

Write-Host "Service $ServiceName configured. To start: Start-Service $ServiceName"
