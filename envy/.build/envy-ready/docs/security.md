## Security Posture

### Principle of Least Privilege

- Skills run inside Python worker processes with explicit whitelists.
- `SysControlSkill` executes only commands listed in `config/envy.yaml.security.command_whitelist`.
- Code generation is constrained to the local workspace and prevents overwrite by default.

### Confirmation Workflow

1. **Voice confirmation** – the assistant asks “Are you sure?” for flagged actions and awaits an affirmative utterance.
2. **Dashboard confirmation** – the web dashboard displays pending actions in `dashboard_state.json`. Operators must approve or reject requests explicitly.

Without both confirmations, destructive actions stop at “Awaiting confirmations.”

### Sandbox Recommendations

- Run Envy under a dedicated user account with limited filesystem permissions.
- Use Linux namespaces (systemd `ProtectSystem`, `ProtectHome`) or containerization for additional isolation.
- On Windows, pair with controlled folders or Sandbox to limit write access.

### Network Policy

- Remote LLM endpoints are disabled by default. Enable only if you trust the provider and your network egress policy allows it.
- The dashboard binds to `0.0.0.0` but authentication is disabled by default. Enable `web.auth` credentials or reverse-proxy behind a TLS terminator.

### Audit Trail

- Logs reside in `artifacts/logs/envy.log` with timestamps and event details (wake detections, skill dispatches, confirmations).
- Test runs emit JSON markers into `artifacts/tests/` for reproducibility.
- The performance report script writes to `artifacts/perf-report.txt` with timestamps to correlate resource spikes.

### Hardening Checklist

- [ ] Rotate dashboard credentials regularly.
- [ ] Restrict execution of shell commands to necessary binaries only.
- [ ] Monitor `artifacts/logs/envy.log` for repeated failed wake detections or denied actions.
- [ ] Update dependencies (`pip list --outdated`) monthly.
- [ ] Review `skills/` directory for untrusted plugins before enabling them.
