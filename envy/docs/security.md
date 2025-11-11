# Envy Security Model

Envy is designed to run on personal hardware while limiting the blast radius of voice commands. This document summarises the safeguards in place and how to extend them.

## 1. Command Sandbox

The `SysControlSkill` executes shell commands only if:

1. The command appears in `security.command_whitelist` within `config/envy.yaml`.
2. The whitelist value is `true`.
3. The caller supplies both voice and dashboard confirmations.

By default all whitelist entries are set to `false`. To allow a command:

```yaml
security:
  command_whitelist:
    "systemctl restart nginx": true
```

The skill still requires confirmation before execution.

## 2. Confirmation Flow

1. **Voice Request** — e.g., “Envy, restart nginx”. The router flags the skill as destructive and prompts for confirmation.
2. **Voice Confirmation** — “Envy, confirm restart” marks the request as voice-confirmed.
3. **Dashboard Confirmation** — the dashboard at `/api/confirm` (or UI button) must be triggered to complete the action.

Only after both confirmation steps succeed does the skill execute.

## 3. Dashboard Protection

- Set a token via `export ENVY_DASHBOARD_TOKEN=<random>` before starting Envy. The dashboard requires the `Authorization: Bearer <token>` header for POST routes.
- Change the dashboard port or bind address in `config/envy.yaml` if you need remote access. For public exposure, place Envy behind a reverse proxy with TLS.

## 4. Filesystem Boundaries

- Generated code is written under the repository-local `workspace/` directory.
- Research summaries live under `artifacts/research/`.
- Reminders store JSON inside `data/reminders.json`.

The `CodeSkill` prevents path traversal by resolving the destination against the workspace root.

## 5. Optional Remote Services

Remote LLM endpoints are opt-in. To enable one:

```yaml
llm:
  default_backend: remote
  remote_endpoint: https://your-endpoint
  remote_api_key_env: ENVY_REMOTE_KEY
```

Keep API keys in environment variables (never in the repo). If remote access is disabled, Envy falls back to the built-in rule-based responses or local llama.cpp.

## 6. Service Accounts

When running as a systemd service, create an `envy` user without shell access:

```bash
sudo useradd --system --home /opt/envy --shell /usr/sbin/nologin envy
```

This minimises privileges. Adjust file ownership accordingly.

On Windows, run the NSSM service under a dedicated local user with limited rights if possible.

## 7. Logs & Auditing

- Voice and skill events are recorded in `artifacts/logs/envy.log`.
- Tests and acceptance runs log to `artifacts/tests/`.
- Performance profiles are stored in `artifacts/perf-report.txt`.

Review these logs regularly when running Envy unattended.
