# Envy Security Model

Envy is designed for local-first operation with explicit guardrails. This document summarises the security posture and configurable safety controls.

## 1. Sandboxed Skills

- All skills execute within the repository root by default.
- `skills.CodeSkill` writes to `skills.workspace_root` (default `./workspace`).
- `skills.SysControlSkill` only runs commands listed in `skills.sandbox.allowed_commands` (`ls`, `pwd`, `cat` out of the box). Any other command is blocked even after confirmation.
- `skills.ReminderSkill` and `skills.ResearchSkill` write to dedicated subdirectories under `runtime/` and `workspace/research/`.

## 2. Confirmation Workflow

Destructive intents follow a dual-confirmation flow:

1. **Voice Recognition:** Router detects phrases like “delete”, “shutdown”, etc., and requests confirmation.
2. **Voice Confirmation:** User must reply with “confirm”, “yes”, etc. Router logs a `security.voice_confirmed` event.
3. **Dashboard Approval:** Admin approves via the web dashboard (`/api/confirmations/{id}/approve`). Only then is the skill re-run with `force=True`.
4. **Final Execution:** Even with `force=True`, the skill checks the command against the whitelist; destructive commands remain blocked by default (`status=blocked`).

Pending confirmations are visible in the dashboard with timestamps and require explicit action. Rejections trigger a `skill.result` event with `status=denied`.

## 3. Configuration Hardening

- `config/envy.yaml` exposes:
  - `security.require_dashboard_confirmation` — set to `true` (recommended).
  - `security.confirmation_timeout_sec` — controls expiration of pending actions.
  - `skills.sandbox.allowed_commands` — extend cautiously; prefer specific absolute paths.
  - `skills.enabled` — disable entire skills by removing them from the enabled list.
- Environment variables (e.g., `ENVY_PROFILE`, `ENVY_DISABLE_WAKE`) can be set in systemd or Windows service definitions to customise behaviour.

## 4. Logging & Audit

- Unified logging is written to `logs/envy.log` with timestamps and severity.
- Sensitive actions (confirmations, blocked commands) are tagged with `security.*` events.
- The dashboard displays a live event feed via Server-Sent Events (SSE) — suppressing logs requires editing the dashboard service.
- All automated tests and performance runs write results to `artifacts/tests/` and `artifacts/perf-report*.{txt,json}` for audit trails.

## 5. Network Exposure

- Dashboard binds to `0.0.0.0:8080` by default. Use a reverse proxy, firewall, or change `web.host` to `127.0.0.1` for local-only access.
- Envy does not call remote LLMs unless `llm.strategies.remote.enabled` is set to `true` and an endpoint is configured.
- If you enable remote connectors, ensure HTTPS endpoints and rotate API keys stored in environment variables.

## 6. Deployment Recommendations

- Run the assistant under a non-root user with restricted filesystem permissions.
- Isolate the workspace directory if skills are allowed to manipulate files.
- Regularly review `logs/`, `artifacts/tests/`, and dashboard confirmations for anomalies.
- Consider enabling host-level sandboxing (e.g., `systemd` `ProtectSystem=strict`, AppArmor, or Windows AppLocker) for added assurance.
