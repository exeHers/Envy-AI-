param(
    [ValidateSet("demo", "full")]
    [string]$Mode = "demo",
    [switch]$SkipLlm
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir
$DownloadDir = Join-Path $RootDir "downloads"
$ModelDir = Join-Path $RootDir "models"

New-Item -ItemType Directory -Force -Path $DownloadDir | Out-Null
New-Item -ItemType Directory -Force -Path $ModelDir | Out-Null

function Download-AndExpandZip {
    param(
        [string]$Url,
        [string]$ArchiveName
    )
    $ArchivePath = Join-Path $DownloadDir $ArchiveName
    if (-not (Test-Path $ArchivePath)) {
        Write-Host "[models] Downloading $ArchiveName"
        Invoke-WebRequest -Uri $Url -OutFile $ArchivePath
    } else {
        Write-Host "[models] Using cached $ArchiveName"
    }
    Expand-Archive -LiteralPath $ArchivePath -DestinationPath $ModelDir -Force
}

function Ensure-Vosk {
    $ModelTag = "vosk-model-small-en-us-0.15"
    $Target = Join-Path $ModelDir $ModelTag
    if (Test-Path $Target) {
        Write-Host "[models] Vosk model already present."
        return
    }
    Download-AndExpandZip -Url "https://alphacephei.com/vosk/models/$ModelTag.zip" -ArchiveName "$ModelTag.zip"
}

function Ensure-DemoAssets {
    Ensure-Vosk
    $llamaDir = Join-Path $ModelDir "llama"
    New-Item -ItemType Directory -Force -Path $llamaDir | Out-Null
    $readme = Join-Path $llamaDir "README.md"
    if (-not (Test-Path $readme)) {
        @"Local LLM placeholder.

To install an optional llama.cpp model:

  scripts\download_models.ps1 -Mode full

Then enable `llm.llama_cpp.enabled` in `config/envy.yaml`.
"@ | Out-File -FilePath $readme -Encoding UTF8
    }
}

function Ensure-Llama {
    $llamaDir = Join-Path $ModelDir "llama"
    New-Item -ItemType Directory -Force -Path $llamaDir | Out-Null
    $Target = Join-Path $llamaDir "ggml-alpaca-7b-q4.bin"
    if (Test-Path $Target) {
        Write-Host "[models] llama.cpp model already present."
        return
    }
    Write-Host "[models] Downloading optional llama.cpp model (~4GB). Press Ctrl+C to abort."
    Start-Sleep -Seconds 3
    Invoke-WebRequest -Uri "https://huggingface.co/ggml-org/ggml-alpaca-7b-q4/resolve/main/ggml-alpaca-7b-q4.bin" -OutFile $Target
}

if ($Mode -eq "demo") {
    Ensure-DemoAssets
} else {
    Ensure-DemoAssets
    if (-not $SkipLlm) {
        Ensure-Llama
    } else {
        Write-Host "[models] Skipping llama.cpp download."
    }
}

Write-Host "[models] Downloads complete."
