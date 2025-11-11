# Security Model & Hardening Guide

Envy prioritises safe-by-default behaviour while enabling automation. This document summarises the built-in guardrails and options for stricter deployments.

## Trust Boundaries

- **Local host only**: all microservices bind to loopback (`127.0.0.1`) by default. Exposing externally requires reverse proxy configuration.
- **Sandboxed actions**: file writes and commands are limited to `workspace/` and `artifacts/` unless explicitly expanded.
- **Skills**: loaded from `skills/` — review third-party skills before enabling.

## Confirmation Workflow

1. **Voice intent** — SysControlSkill and other high-risk actions demand a follow-up confirmation phrase.
2. **Dashboard approval** — pending confirmations appear on the dashboard; users must approve/reject.
3. **Whitelist** — `config/envy.yaml` lists allowed shell commands (`ls`, `pwd`, `cat`, `echo` by default).

If either voice or dashboard confirmation is missing, the router keeps the action in `pending_confirmations` and refuses execution.

## Configuration Tips

- Adjust `config/envy.yaml`:
  - `safety.sandbox_paths` — extend only if necessary.
  - `safety.command_whitelist` — keep minimal and audited.
  - `llm.remote.enabled` — remains `false` by default; ensure HTTPS endpoints and tokens stored securely.
- Rotate or encrypt any secrets (example template: `config/secrets.example.yaml`).

## Service Isolation

- Run each service under dedicated OS accounts if hosting multi-user environments.
- Use systemd hardening features (e.g., `ProtectSystem=strict`, `ProtectHome=yes`) by editing `installers/systemd/envy.service`.
- Containerisation (Docker) isolates dependencies but still requires microphone pass-through.

## Logging & Auditing

- Logs write to `artifacts/logs/` per service; rotate regularly.
- Test logs stored in `artifacts/tests/`.
- Performance metrics logged to `artifacts/perf-report.txt`.

## Network Security

- Web dashboard uses HTTP; when exposed beyond localhost, place behind an HTTPS reverse proxy (Caddy/Nginx) with auth.
- Router-to-service communication is HTTP over localhost; for multi-host setups consider VPN tunnels or mTLS.

## Model Safety

- Vosk models are downloaded from trusted source (alphacephei.com) with SHA256 verification.
- Optional TinyLlama is downloaded from Hugging Face; checksum validated.
- Larger or remote models should be vetted for licensing and prompt injection vulnerabilities.

## Windows Considerations

- Services run under the account configured in `install_service.ps1`; leverage Windows Service isolation and `sc.exe` security descriptors for production.
- Ensure `start-envy.bat` resides on NTFS with appropriate ACLs.

## Incident Response

- Stop services via `systemctl stop envy@user` (Linux) or `Stop-Service EnvyAssistant` (Windows).
- Review `artifacts/logs/` and `artifacts/tests/acceptance.log` for audit trail.
- Remove suspicious skills from `skills/` and restart services.

