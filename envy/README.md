# Envy — Local Jarvis-Style Assistant

Envy is a 24/7 voice-first personal assistant that runs completely on your own hardware. It combines wake-word listening, streaming STT/TTS, modular skills, and a web dashboard for confirmations and monitoring. The default configuration targets an Intel i3 with a GTX 1070 (8 GB) and 16 GB RAM while keeping CPU/GPU usage modest.

## Quickstart

```bash
git clone <repo> envy
cd envy
./install_envy.sh --local-demo
./run_envy_local.sh --profile balanced --no-gui
```

The `--local-demo` flag installs everything except the large LLM. Remove the flag to fetch the TinyLlama Q4 model for fully offline responses.

## Features

- Always-listening wake word “Envy” powered by VOSK (keyword spotting & STT).
- Streaming STT with configurable backends (VOSK by default).
- pyttsx3-based TTS with streaming playback stubs and artifact logging.
- Modular skill framework (`skills/`) with built-in Code, Research, Reminder, and SysControl skills.
- Rule-based intent classifier with LLM fallback via llama.cpp or optional remote endpoints.
- Security guardrails: destructive actions require voice and dashboard confirmation, command whitelist sandbox.
- FastAPI dashboard with status, logs, and confirmation workflow.
- Systemd unit, Windows service wrapper, Docker image, and start scripts.

## Repository Layout

```
envy/
├── config/                # Default configuration (envy.yaml)
├── src/envy/              # Python package with services, skills, CLI
├── skills/                # Built-in skill modules
├── scripts/               # Installers, tests, perf utilities, model downloads
├── tests/                 # Pytest acceptance suite
├── artifacts/             # Logs, test outputs, perf reports
├── docs/                  # Detailed OS-specific guides and security notes
├── systemd/, windows/     # Service deployment assets
└── workspace/             # Sandbox directory for generated files
```

## Running Envy

### Profiles

- `low`: CPU-friendly, STT/LLM fall back to rule-based responses.
- `balanced` (default): mixes VOSK STT and llama.cpp (if model downloaded).
- `power`: uses higher resource caps for faster responses.

Switch profiles via `./run_envy_local.sh --profile power`.

### Headless Mode

By default the dashboard listens on `http://localhost:8190`. To run without the UI:

```bash
./run_envy_local.sh --profile balanced --headless
```

### Docker

```bash
docker build -t envy-assistant .
docker run --net=host --device /dev/snd --gpus all envy-assistant
```

The Docker build skips the large LLM model to keep the image light; run `python scripts/download_models.py` inside the container if you want it.

## Skills

Built-in skills live under `src/envy/skills/`:

- `CodeSkill`: creates or edits files within `workspace/`.
- `ResearchSkill`: collects summaries into `artifacts/research/`.
- `ReminderSkill`: stores reminders in `data/reminders.json`.
- `SysControlSkill`: executes whitelisted commands with double confirmation.

Drop new skills in `skills/` and they will be auto-discovered.

## Tests & Verification

```bash
source .venv/bin/activate
./scripts/run_tests.sh
```

Logs are stored in `artifacts/tests/pytest.log`. Performance metrics can be generated with:

```bash
./artifacts/perf-report-gen.sh
cat artifacts/perf-report.txt
```

## Packaging

`envy-ready.zip` (generated during release packaging) contains:

- Scripts: `run_envy_local.sh`, `install_envy.sh`, `start-envy.sh`
- Configs: `config/envy.yaml`, service definitions, docs
- Models (if downloaded) or the loader scripts
- Skills and example assets

Use `scripts/package_ready.sh` (see below) to refresh the archive.

## Optional Remote LLMs

Set the following in `config/envy.yaml` to enable a free HTTP endpoint:

```yaml
llm:
  default_backend: remote
  remote_endpoint: https://your-free-endpoint/v1/chat/completions
  remote_api_key_env: ENVY_REMOTE_API_KEY
```

Keep the API key in an environment variable; remote usage is opt-in and disabled by default.

## Security

- All system commands must appear in `security.command_whitelist` to execute.
- Destructive skills require both voice confirmation (“Envy confirm …”) and dashboard approval.
- Dashboard can be locked down with a token (set `ENVY_DASHBOARD_TOKEN`).
- See `docs/security.md` for a full walkthrough.

## Documentation

- `docs/install-linux.md`: distro-specific setup for Intel i3 + GTX 1070.
- `docs/install-windows.md`: step-by-step with `nssm`.
- `docs/security.md`: sandboxing, confirmation loops, extending the whitelist.

## Packaging Helper

After running tests and collecting artifacts:

```bash
./scripts/package_ready.sh
```

This creates `envy-ready.zip` at the repository root with the runtime bundle.
