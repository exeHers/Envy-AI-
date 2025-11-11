# Envy Personal Assistant

Envy is a Jarvis-style assistant engineered to run 24/7 on a modest desktop (Intel i3 + GTX 1070 + 16 GB RAM). It listens for the wake word **“Envy”**, transcribes voice commands locally with VOSK, routes requests to modular Python skills, speaks responses with offline TTS, and serves a FastAPI dashboard for confirmations and monitoring.

## Quickstart

```bash
git clone https://example.com/envy.git
cd envy
./install_envy.sh --local-demo       # create venv, install deps, download VOSK (~50 MB)
./run_envy_local.sh --profile balanced --no-gui
```

> The default balanced profile uses the TinyLlama GGUF model if present. To download it (~600 MB) during installation, add `--with-llm`.

### Demo The Pipeline

```bash
source .venv/bin/activate
python -m envy.main demo
```

This feeds the bundled audio samples through the entire stack (wake → STT → skill → LLM → TTS) and saves the result to `artifacts/demo_result.json`.

## Automated Tests

```bash
source .venv/bin/activate
pytest
```

Tests exercise the wake-word detector, STT pipeline, CodeSkill (creates `test.py` containing `print("hello from envy")`), and the TTS output. Logs are written to `artifacts/tests/`.

## Packaging

```bash
./scripts/package_envy.sh
```

Creates `envy-ready.zip` containing the runtime scripts, configs, audio samples, skills, and (if available) the downloaded VOSK model.

## Configuration

- `config/envy.yaml` holds wake word, profiles, resource limits, security policies, and skill settings.
- Profiles (`low`, `balanced`, `power`) manage model paths and concurrency limits.
- Set `remote_endpoints.enabled` to `true` only if you opt into free external inference services.

## Web Dashboard

`python -m envy.main start` launches the FastAPI dashboard on `http://localhost:8420`. It lists pending confirmations and allows approvals/rejections of destructive actions. Disable the dashboard with `--no-gui` for headless environments.

## Services & Installers

- `install_envy.sh` and `install_envy.bat` create virtual environments, install dependencies, and download required models.
- `start-envy.sh` / `start-envy.bat` boot the assistant.
- `packaging/systemd/envy.service` provides a template systemd unit.
- `packaging/windows/envy_service_wrapper.py` integrates with Windows service wrappers (e.g., NSSM).

## Performance Reporting

Run `artifacts/perf-report-gen.sh` after a session to produce `artifacts/perf-report.txt` with CPU, RAM, and GPU utilization snapshots.

## Security Notes

- Destructive skills (e.g., `SysControlSkill`) require both voice and dashboard confirmations by default.
- A command whitelist in `config/envy.yaml` ensures only safe shell calls execute out of the box.
- Optional web authentication can be enabled under `web.auth`.

## License

MIT © 2025 Envy
