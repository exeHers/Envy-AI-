#!/usr/bin/env bash
set -euo pipefail

MODE="${1:---minimal}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="${ROOT_DIR}/models"
VOSK_DIR="${MODELS_DIR}/vosk-model-small-en-us"

mkdir -p "${MODELS_DIR}"

if [[ "${MODE}" == "--minimal" || "${MODE}" == "--local-demo" ]]; then
  mkdir -p "${VOSK_DIR}"
  cat > "${VOSK_DIR}/README.txt" <<'EOF'
Envy minimal model placeholder.

For full wake-word and transcription quality, run:
  ./scripts/download_models.sh --full
EOF
  echo "Created placeholder Vosk model directory at ${VOSK_DIR}"
  exit 0
fi

if [[ "${MODE}" == "--full" ]]; then
  ZIP_PATH="${MODELS_DIR}/vosk-model-small-en-us-0.15.zip"
  if [[ ! -f "${ZIP_PATH}" ]]; then
    echo "Downloading Vosk small English model..."
    curl -L -o "${ZIP_PATH}" "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
  else
    echo "Vosk model archive already present."
  fi
  rm -rf "${VOSK_DIR}"
  mkdir -p "${VOSK_DIR}"
  unzip -o "${ZIP_PATH}" -d "${MODELS_DIR}" >/dev/null
  mv "${MODELS_DIR}/vosk-model-small-en-us-0.15" "${VOSK_DIR}"
  echo "Vosk model extracted to ${VOSK_DIR}"
  exit 0
fi

echo "Unknown mode ${MODE}. Use --minimal or --full." >&2
exit 1
