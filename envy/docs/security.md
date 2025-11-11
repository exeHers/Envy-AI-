## Security & Safety Posture

Envy is designed to operate locally with conservative defaults. Key safeguards include:

### 1. Least-Privilege Execution

- Python virtual environment isolates third-party packages.
- Systemd unit runs under a dedicated `envy` user (`/opt/envy`) instead of root.
- Windows NSSM configuration runs under the current user; create a dedicated low-privilege account for production.

### 2. Command Sandboxing

- `SysControlSkill` only executes commands from a whitelist (`config/envy.yaml` → `security.command_whitelist`).
- Any request containing destructive verbs (“delete”, “format”, “shutdown”) triggers a pending action requiring confirmation.
- Blocking patterns (e.g., `rm -rf`, fork bombs) are explicitly denied.

### 3. Dual Confirmation Flow

1. Voice confirmation: the router registers `voice_confirmed` only after an affirmative voice command (or automated test trigger).
2. Dashboard confirmation: an operator must approve the action at `http://127.0.0.1:7010`.

Until both steps succeed, the underlying skill is not executed. Pending actions persist across restarts in `artifacts/pending_actions.json`.

### 4. Network Boundaries

- All services bind to `127.0.0.1` by default; no public exposure without explicit reconfiguration.
- Dashboard is intended for local-only access; protect with SSH tunnels or reverse proxies if exposed.

### 5. Data Handling

- Speech transcripts, skill outputs, and research summaries are saved under `artifacts/`.
- Temporary audio files (`artifacts/tts-output.wav`) can be rotated or purged via scheduled tasks.
- No data leaves the machine unless remote endpoints are manually enabled (`remote_endpoints.enabled`).

### 6. Remote Providers (Opt-In)

- Remote LLM connectors are disabled by default.
- Each provider declares the environment variable needed for API credentials.
- Enable only after reviewing provider Terms of Service and logging policies.

### 7. Upgrades & Patching

- Keep dependencies up to date: `source .venv/bin/activate && pip install --upgrade .`.
- Monitor FastAPI, uvicorn, and sounddevice CVEs.
- Re-run `install_envy.sh` after pulling new releases to refresh the virtual environment.

### 8. Observability

- Application logs: `logs/envy.log`.
- Dashboard exposes action history + log tail.
- `artifacts/perf-report.txt` captures CPU/GPU peaks for capacity planning.

### 9. Future Hardening Ideas

- Add voice biometrics or PIN confirmation.
- Integrate with hardware button or NFC tap for destructive actions.
- Add TLS termination and authentication for the dashboard (e.g., via Traefik or Caddy).
