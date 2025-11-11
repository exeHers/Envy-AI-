param(
    [switch]$Vosk = $false,
    [switch]$TinyLlama = $false,
    [switch]$All = $false
)

$Root = Split-Path -Parent $PSScriptRoot
$ModelsDir = Join-Path $Root "models"
New-Item -ItemType Directory -Force -Path $ModelsDir | Out-Null

if (-not ($Vosk -or $TinyLlama -or $All)) {
    Write-Output "Usage: download_models.ps1 [-Vosk] [-TinyLlama] [-All]"
    exit 1
}

if ($All) {
    $Vosk = $true
    $TinyLlama = $true
}

if ($Vosk) {
    $voskZip = Join-Path $ModelsDir "vosk-model-small-en-us-0.15.zip"
    $voskUrl = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    $voskDir = Join-Path $ModelsDir "vosk-model-small-en-us-0.15"

    if (-Not (Test-Path $voskDir)) {
        Write-Output "[download] $voskUrl"
        Invoke-WebRequest -Uri $voskUrl -OutFile $voskZip
        Expand-Archive -Path $voskZip -DestinationPath $ModelsDir -Force
        Remove-Item $voskZip
    } else {
        Write-Output "[skip] Vosk model already present."
    }
}

if ($TinyLlama) {
    $tinyPath = Join-Path $ModelsDir "tinyllama-1.1b-chat.Q4_K_M.gguf"
    if (-Not (Test-Path $tinyPath)) {
        $tinyUrl = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-GGUF/resolve/main/tinyllama-1.1b-chat.Q4_K_M.gguf?download=1"
        Write-Output "[download] $tinyUrl"
        Invoke-WebRequest -Uri $tinyUrl -OutFile $tinyPath
    } else {
        Write-Output "[skip] TinyLlama model already present."
    }
}
