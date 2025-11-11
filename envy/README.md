# Envy – Local Jarvis-Style Assistant

Envy is a 24/7 personal assistant that runs entirely on your hardware. It combines an always-on wake word listener, streaming speech pipelines, modular skills, and a confirmation-aware dashboard to stay safe and responsive on modest rigs (Intel i3 + GTX 1070).

## Quickstart

```bash
git clone <this repo>
cd envy
./install_envy.sh --local-demo
./run_envy_local.sh --profile balanced --no-gui
```

The `--local-demo` flag downloads the lightweight Vosk model required for automated tests and uses the built-in rule-based LLM fallback. To add larger local models later, run `./scripts/download_models.sh --full` and enable `llm.llama_cpp.enabled` in `config/envy.yaml`.

### Windows

```powershell
git clone <repo>
cd envy
.\install_envy.bat -LocalDemo
.\run_envy_local.bat --profile balanced --no-gui
```

## Features

- **Wake listener** – Vosk-based keyword spotter idling at low CPU load until you say “Envy”.
- **Streaming STT + TTS** – Vosk STT with partial emission, pyttsx3 (or tone fallback) for TTS, both exposed as microservices.
- **Router + Skills** – FastAPI router orchestrates sessions, intent classification, and the skill manager. Skills ship as drop-in Python modules under `src/envy/skills/`.
- **Secure execution** – Destructive intents require double confirmation (voice + dashboard). System control commands are sandboxed with a whitelist.
- **Web dashboard** – Minimal HTMX-free UI for monitoring, confirmations, logs, and manual commands (`http://localhost:8300`).
- **Service tooling** – `start-envy.sh`, `run_envy_local.sh`, systemd unit, Windows NSSM wrapper, Dockerfile, packaging helpers.
- **Automated tests** – Pytest-based acceptance suite plus scripts for wake-word, STT→skill, TTS, LLM fallback, and performance sampling.

## Repository Layout

```
config/                # YAML configuration profiles and tunables
src/envy/              # All Python services, skills, and shared utilities
scripts/               # Helper scripts (model downloads, installers)
start-envy.sh/.bat     # Launch all services via the process manager
run_envy_local.sh/.bat # Convenience wrapper for local demos or CI
packaging/             # systemd unit, Windows NSSM helper
tests/                 # Automated acceptance tests & fixtures
artifacts/             # Logs, test outputs, performance reports
```

## Running the Services

- **Process manager**: `envy-process-manager start --profile balanced --dashboard`
- **Wake listener**: `uvicorn envy.services.wake_listener.main:app --port 8201`
- **Dashboard**: `http://localhost:8300` (default credentials `envy/envy`, configurable in `config/envy.yaml`)

Profiles (`low`, `balanced`, `power`) adjust sampling rates, skill concurrency, and GPU usage caps. Set `ENVY_PROFILE` before launching or pass `--profile`.

## Skills

Included skills live in `src/envy/skills/`:

- `CodeSkill` – Handles “create test.py …” style requests.
- `ResearchSkill` – Generates offline summaries and saves them under `workspace/research/`.
- `SysControlSkill` – Queues whitelisted system commands pending confirmation.
- `ReminderSkill` – Stores reminders in `artifacts/reminders.json`.

Drop a new module implementing `BaseSkill` into the folder and add it to `skills.enabled` in `config/envy.yaml` to activate.

## Configuration

All tunables reside in `config/envy.yaml`:

- **Profiles** – `profiles.{low,balanced,power}` entries merged during load.
- **Wake listener/STT/TTS** – Model paths, chunk sizes, thresholds.
- **LLM** – Rule-based fallback by default, optional llama.cpp or remote endpoints.
- **Skills** – Sandbox root, command whitelist, destructive keywords.
- **Security** – Confirmation requirements, timeouts, dashboard auth.

Set `ENVY_CONFIG_PATH` to point to a custom config file if needed.

## Services & Packaging

- **Systemd**: copy `packaging/systemd/envy.service` to `/etc/systemd/system/`, adjust `WorkingDirectory`, then `systemctl enable --now envy`.
- **Windows**: install [NSSM](https://nssm.cc/) and run `packaging/windows/install-envy-service.ps1 -InstallPath C:\Envy -Profile balanced`.
- **Docker**: `docker build -t envy . && docker run --rm -p 8300:8300 envy`.

## Tests & Reports

- Run automated acceptance tests: `pytest -q` (virtualenv required).
- Performance script (todo5) writes `artifacts/perf-report.txt`.
- Artifact logs (tests, installs) accumulate under `artifacts/`.

## Security Notes

- Destructive intents require dashboard confirmation and voiced affirmation.
- System commands run only from an allowlist and are queued by default.
- Dashboard auth defaults to `envy/envy`. Change it in `config/envy.yaml`.
- Optional remote LLM endpoints are opt-in and disabled by default.

## License

MIT License © 2025 Cursor Build Agent.
