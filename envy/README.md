# Envy — Local-First Personal Assistant

Envy is a Jarvis-style assistant that runs end-to-end on your own hardware. It listens for the wake word **“Envy”**, transcribes commands, routes work to modular skills, speaks responses, and exposes a confirmation-first dashboard for sensitive actions.

## Quickstart

```bash
git clone <this repo> envy
cd envy
./install_envy.sh --local-demo
./run_envy_local.sh --audio-file tests/data/wake_command.wav --profile balanced --no-dashboard
```

## Features

- Wake-word listener (Vosk) that keeps CPU usage low until “Envy” is heard.
- Streaming STT / TTS pipeline with pyttsx3 fallback to tone synthesis.
- Modular skill system (`skills/`) — includes Code, Research, SysControl (with confirmations), and Reminder skills.
- Lightweight LLM adapter with pluggable backends (simple heuristics by default, optional llama.cpp or remote endpoints).
- FastAPI dashboard (HTMX-style refresh) for logs, state, and destructive-action confirmations.
- Service wrappers: systemd unit, Windows NSSM script, Docker-ready scripts.
- Automated tests validate wake detection, STT→Skill→TTS, and LLM fallback.
- Performance capture script writes CPU/GPU/memory stats to `artifacts/perf-report.txt`.

## Repository Layout

- `envy/` — Python package with services, skills, and CLI (`envy.cli`).
- `config/envy.yaml` — Profiles (low/balanced/power), resource caps, security policy.
- `scripts/` — Model downloads, helper tooling.
- `templates/`, `static/` — Web dashboard assets.
- `tests/` — Pytest suite including audio fixtures.
- `artifacts/` — Runtime logs, perf reports, generated outputs.
- `deploy/` — systemd unit, Windows NSSM helper.

## Install & Run

### Linux / WSL

```bash
./install_envy.sh            # creates .venv, installs deps, downloads models
source .venv/bin/activate
python -m envy.cli run --profile balanced --audio-file tests/data/wake_command.wav
```

### Windows (PowerShell)

```powershell
.\install_envy.bat
.\run_envy_local.bat --audio-file tests\data\wake_command.wav --profile balanced
```

### Service Mode

- Systemd: copy `deploy/systemd/envy.service` to `/etc/systemd/system`, edit `WorkingDirectory` and `ExecStart`, then `sudo systemctl enable --now envy`.
- Windows: install [NSSM](https://nssm.cc/) and run `powershell -ExecutionPolicy Bypass -File deploy/windows/envy_service_wrapper.ps1 -InstallPath C:\Envy`.

## Config Profiles

- `low`: CPU-only, lowest power draw.
- `balanced`: default, GPU optional, optimized for i3 + GTX 1070.
- `power`: upgrades to Whisper + llama.cpp; downloads triggered via `scripts/download_models.py --profile power`.

Tune persona, resource caps, confirm policies, and skill whitelist in `config/envy.yaml`. Toggle remote LLM/backends via the `optional_remote` block (disabled by default).

## Skills

Drop-in Python modules under `skills/`. Each exposes `can_handle()` and `execute()`. Built-ins:

- `CodeSkill`: creates/edits code files (e.g., “Envy, create test.py ...”).
- `ResearchSkill`: writes quick summaries to `artifacts/research/`.
- `SysControlSkill`: executes whitelisted commands after **voice + dashboard** confirmation.
- `ReminderSkill`: logs reminders to `artifacts/reminders/reminders.json`.

## Testing & Verification

Run automated checks (creates artifacts under `artifacts/tests/`):

```bash
source .venv/bin/activate
./scripts/run_tests.sh            # captures logs under artifacts/tests/
./artifacts/perf-report-gen.sh    # generates artifacts/perf-report.txt
```

Pass criteria captured in `cursor-build-log.txt` include:
- Wake-word detection logged from sample audio.
- CodeSkill generates `workspace/test.py` with `print("hello from envy")`.
- TTS writes `artifacts/tts-output.wav`.
- Router triggers LLM fallback test.
- `envy-ready.zip` packaging.

## Packaging & Deployment

Use `./scripts/package_envy.sh` (created during build) to assemble `envy-ready.zip` containing binaries, configs, and lightweight models. The archive includes `run_envy_local.sh`, installers, configs, dashboard assets, and acceptance test logs.

## Security Posture

- Skills run in controlled workspace (`config.security.sandbox_workdir`).
- Destructive actions require both voice and dashboard confirmation by default.
- Remote endpoints are opt-in; none are enabled out of the box.
- All code is MIT-licensed and generated within this repository.

## Troubleshooting

- **Models missing**: rerun `scripts/download_models.py --profile balanced`.
- **Audio device issues**: update `audio.input_device` / `audio.output_device` in `config/envy.yaml`.
- **pyttsx3 errors**: ensure `espeak` (Linux) or SAPI voices (Windows) are installed; fallback tone synthesis will still produce `artifacts/tts-output.wav`.
- **Dashboard fails**: confirm `uvicorn` installed and port not in use.

## Extending

- Add new skills by creating modules in `skills/` and listing them in `config/envy.yaml`.
- Implement new LLM connectors by subclassing or modifying `envy/services/llm_adapter.py`.
- Build custom front-end components by editing `templates/index.html` and `static/style.css`.
