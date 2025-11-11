## Envy — Local-First Personal Assistant

Envy is a Jarvis-style assistant that runs entirely on your own machine. It provides wake-word listening, speech-to-text, skill routing, text-to-speech, a web dashboard, and modular skills — all without paid APIs.

### Quickstart

```bash
cd envy
./install_envy.sh --local-demo
./run_envy_local.sh --profile balanced --no-gui
```

The assistant will start its microservices (wake listener, STT, router, skills, TTS, LLM adapter). Visit the dashboard at `http://127.0.0.1:7010` unless you pass `--no-gui`.

### Scripts & Services

- `install_envy.sh` / `install_envy.bat`: create a virtualenv, install dependencies, set up placeholder models.
- `run_envy_local.sh` / `.bat`: launch Envy with selectable profiles (`low`, `balanced`, `power`).
- `start-envy.sh` / `.bat`: internal launcher used by services and systemd/NSSM.
- `scripts/systemd/envy.service`: sample unit file (installs under `/opt/envy`).
- `scripts/windows/install_envy_service.bat`: wrap Envy with NSSM for Windows services.
- `scripts/download_models.sh` / `.bat`: fetch placeholder (“minimal”) models or download the full Vosk package with `--full`.

### Configuration

Runtime settings (profiles, resource caps, model paths, confirmation flows) live in `config/envy.yaml`. Choose among:

- `low`: CPU-first, stub LLM, minimal resource use.
- `balanced`: Vosk STT, optional llama.cpp model (download separately), GPU acceleration enabled.
- `power`: Higher-end defaults, whisper + larger LLM placeholders.

Override values with environment variables like `ENVY_PROFILE__LLM__PROVIDER=stub` or edit the YAML directly.

### Skills

Drop new Python modules into `skills/`. Included skills:

- `CodeSkill`: create/edit small files, used for the acceptance test (`test.py`).
- `ResearchSkill`: generate local research summaries and save to `artifacts/research/`.
- `SysControlSkill`: sandboxed command execution (whitelisted commands) with mandatory voice plus dashboard confirmation.
- `ReminderSkill`: schedule reminders stored in `artifacts/reminders.json`.

### Security & Confirmations

Potentially destructive skills (system control) do not execute until:

1. A voice confirmation is registered.
2. The dashboard confirmation button is pressed.

Pending actions are stored in `artifacts/pending_actions.json` and surfaced in the dashboard.

### Models

Minimal install uses lightweight placeholders. For better accuracy:

```bash
./scripts/download_models.sh --full          # grabs Vosk small EN model
./scripts/download_llm.sh --tinyllama        # (provide your own script or manual download)
```

Update `config/envy.yaml` with the downloaded paths. All models must be freely licensed.

### Tests & Reports

Automated tests live in `tests/`. Acceptance tests feed prerecorded audio, verify wake detection, code generation, TTS output, and LLM fallback. Results and logs are written under `artifacts/tests/`. Generate performance summaries (CPU/GPU/memory) with `artifacts/perf-report-gen.sh` once the services are running.

### Packaging

`scripts/package_ready.sh` (provided later) builds `envy-ready.zip`, including runtime scripts, config, placeholders, and artifacts needed to run Envy offline.

### Troubleshooting

- Missing audio devices: install PortAudio (`libportaudio2`) and ensure microphone permissions.
- Vosk model errors: re-run `download_models.sh --full` and update config paths.
- LLM slow or unavailable: keep provider set to `stub` or enable remote endpoints in `config/envy.yaml` (disabled by default).
- Dashboard offline: ensure you didn’t pass `--no-gui`. Access runs on port 7010.

Envy ships under the MIT License. Contributions and new skills are welcome.
