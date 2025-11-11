Model files are downloaded on demand by `scripts/download_models.sh` (Linux/macOS) or `scripts/download_models.ps1` (Windows).

Default demo bundle:

- `models/vosk-model-small-en-us-0.15/` – Wake word + STT
- `models/llama/README.md` – Placeholder for optional llama.cpp models

Run:

```bash
./scripts/download_models.sh --demo   # lightweight default
./scripts/download_models.sh --full   # includes optional llama.cpp
```

On Windows:

```powershell
.\scripts\download_models.ps1 -Mode demo
```
