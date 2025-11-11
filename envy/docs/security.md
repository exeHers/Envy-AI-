# Envy Security Model

## Principles

- **Least privilege**: Skills run inside a sandbox workspace (`config.security.sandbox_workdir`), preventing modifications to system files by default.
- **Defense in depth**: Destructive actions require both voice and dashboard approval (`skills.destructive_requires_confirmation = true`).
- **Transparency**: The dashboard exposes the latest transcript, response, and pending confirmation message so operators can audit activity in real time.
- **Opt-in networking**: Remote LLM endpoints are disabled out of the box; operators must explicitly enable and configure them.

## Confirmations

1. **Voice** — Envy asks for explicit verbal confirmation before executing destructive commands (handled by the skill’s `requires_confirmation` flag).
2. **Dashboard** — Operators must confirm via the web UI (`/api/confirm`). Without approval, the task remains pending and is not executed.

Both confirmations are required by default for `SysControlSkill`; you can adjust this per skill by editing its module or toggling `destructive_requires_confirmation`.

## Sandboxing

- Skills operate inside `<repo>/workspace/` (configurable), ensuring generated code and executed commands stay in a controlled directory.
- System command whitelist (`skills.whitelist_commands`) restricts what `SysControlSkill` can execute. Expand cautiously and review each addition.

## Logging

- `logs/envy.log` (configurable) captures runtime logs.
- `artifacts/tests/` contains automated test logs with timestamps.
- `artifacts/commands/syscontrol.log` records every command executed through `SysControlSkill`.
- `artifacts/perf-report.txt` stores performance metrics for audit purposes.

## Remote Integrations

- To enable a remote LLM endpoint, edit `config/envy.yaml` → `optional_remote` and set `enabled: true` plus an HTTPS endpoint.
- Clearly label any remote endpoints in `cursor-build-log.txt` or README updates; remote usage is opt-in and should disclose any data sharing.

## Hardening Tips

- Run Envy under a dedicated OS user (see `deploy/systemd/envy.service`).
- Use TLS termination (e.g., Caddy or Nginx) if exposing the dashboard externally. Alternatively, set `web.enable_remote_access: false` (default) to bind to localhost only.
- Rotate logs or integrate with a SIEM by tailing `logs/envy.log`.
- Validate new skills before deployment; follow the template in `skills/base.py` to preserve safety checks.

## Incident Response

- Review `logs/envy.log` and `artifacts/commands/syscontrol.log` for suspicious entries.
- Clear pending confirmation via dashboard reject or restart the service to reset state.
- Revoke remote endpoints by setting `optional_remote.enabled: false`.
- Reinstall from a clean git clone and re-run `install_envy.sh` if compromise is suspected.
