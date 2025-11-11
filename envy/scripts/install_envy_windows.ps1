param(
    [switch]$LocalDemo,
    [switch]$FullModels,
    [switch]$SkipModelDownload
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$LogDir = Join-Path $RootDir "artifacts"
$LogFile = Join-Path $LogDir "install-log.txt"
$VenvDir = Join-Path $RootDir ".venv"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Start-Transcript -Path $LogFile -Append

Write-Host "[install] Starting Envy installation at $(Get-Date -Format o)"

$Python = if ($env:PYTHON) { $env:PYTHON } else { "python" }

if (-not (Test-Path (Join-Path $VenvDir "Scripts\Activate.ps1"))) {
    Write-Host "[install] Creating virtual environment at $VenvDir"
    & $Python -m venv $VenvDir
}

Write-Host "[install] Activating virtual environment"
& (Join-Path $VenvDir "Scripts\Activate.ps1")

Write-Host "[install] Upgrading pip"
pip install --upgrade pip wheel

Write-Host "[install] Installing Envy dependencies"
pip install -e ".[dev]"

if (-not $SkipModelDownload) {
    $mode = "demo"
    if ($FullModels) {
        $mode = "full"
    }
    elseif ($LocalDemo) {
        $mode = "demo"
    }
    Write-Host "[install] Downloading models (mode=$mode)"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $ScriptDir "download_models.ps1") -Mode $mode -SkipLlm:$SkipModelDownload
} else {
    Write-Host "[install] Skipping model downloads as requested."
}

Write-Host "[install] Installation completed."
Write-Host "[install] Virtual environment: $VenvDir"
Write-Host "[install] To start Envy, run: start-envy.bat --dashboard"

Stop-Transcript
