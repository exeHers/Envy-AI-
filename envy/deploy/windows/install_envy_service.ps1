param(
    [string]$EnvyHome = "$PSScriptRoot\..\..",
    [string]$PythonExe = "$PSScriptRoot\..\..\venv\Scripts\python.exe",
    [string]$Profile = "balanced"
)

$ServiceName = "EnvyAssistant"
$DisplayName = "Envy Personal Assistant"
$StartScript = Join-Path $EnvyHome "start-envy.bat"

if (-not (Test-Path $StartScript)) {
    Write-Error "start-envy.bat not found at $StartScript. Run install_envy.bat first."
    exit 1
}

$existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Output "Service $ServiceName already exists. Stopping and updating..."
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
}

$command = "`"$StartScript`" --profile $Profile --no-gui"
sc.exe create $ServiceName binPath= "$command" DisplayName= "$DisplayName" start= auto
sc.exe description $ServiceName "Always-on Envy personal assistant service."
Write-Output "Service $ServiceName installed. Start it with: Start-Service $ServiceName"
