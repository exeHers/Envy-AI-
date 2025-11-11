# Security Overview

Envy is built to run autonomously on personal hardware without escalating into unsafe actions. This document summarises the built-in safeguards and how to customise them.

## 1. Confirmation Workflow

- **Voice confirmation**: For flagged intents, the router requests an explicit “Yes” or “Confirm” response via microphone before proceeding.
- **Dashboard confirmation**: A matching action must be confirmed through the web dashboard (`/api/confirm`). The form expects the `action_id` announced by Envy.
- **Timeout**: Pending confirmations expire after the number of seconds defined in `security.confirmation_timeout_seconds` (default 45 s). Expired actions are discarded and logged.

You can disable either layer in `config/envy.yaml`:

```yaml
security:
  voice_confirmation: false
  dashboard_confirmation: true
```

## 2. Intent Classification & Skills

- The `IntentClassifier` biases towards explicit, high-confidence matches (code, research, reminders).
- Unrecognised requests fall back to the local rule-based LLM responder instead of executing free-form commands.
- Skills must subclass `BaseSkill` and are invoked via the `skill_manager` service, which enforces timeouts (`skill_manager.timeout_seconds`) and isolates execution.

## 3. Sandbox & Command Whitelist

`config/envy.yaml` controls filesystem and command access:

```yaml
skills:
  sandbox_root: "."
  command_whitelist:
    - ls
    - pwd
    - cat
  destructive_keywords:
    - delete
    - shutdown
```

- File operations in `CodeSkill` are confined under `sandbox_root`.
- `SysControlSkill` only queues commands present in `command_whitelist`; execution after double-confirmation is left to operators.
- `destructive_keywords` automatically force double confirmation even if the intent would otherwise be safe.

## 4. Dashboard Authentication

Basic auth is enabled by default:

```yaml
dashboard:
  auth:
    enabled: true
    username: envy
    password: envy
```

Change the credentials immediately in production deployments. If running behind a reverse proxy with its own auth, you may disable the built-in prompt by setting `dashboard.auth.enabled` to `false`.

## 5. Messaging Security

- Internal services authenticate with a shared secret header (`x-envy-secret`). The value is defined at `messaging.shared_secret`. Change it before exposing any service on the network.
- External ports (8201–8205, 8300) should be firewalled or bound to localhost unless you explicitly need remote access.

## 6. Remote LLMs & Connectors

Remote endpoints are **disabled by default**. To enable a free remote model, update:

```yaml
llm:
  remote:
    enabled: true
    endpoint: https://example.com/v1/chat/completions
    headers:
      Authorization: Bearer <token>
```

Provide your own API keys, understand rate limits, and inspect responses before allowing autonomous execution.

## 7. Logs & Auditing

- Every session is recorded under `artifacts/sessions/{session_id}/session.json`.
- `artifacts/logs/envy.log` aggregates service logs for audit trails.
- Dashboard displays the last entries via `/api/logs`.

## 8. Hardening Checklist

1. Rotate `messaging.shared_secret` and dashboard credentials.
2. Restrict network access (bind to `127.0.0.1`, use SSH tunnels or reverse proxies for remote access).
3. Run services as a dedicated non-root user (`envy`).
4. Back up `artifacts/` and consider tmpfs for transient data if privacy sensitive.
5. Keep system packages and Python dependencies up to date (`pip install -U`).
6. Review new skills or model downloads before enabling them in production.

Envy is designed for transparent, auditable operation. Review tests (`tests/acceptance/`) and expand them to cover new skills or connectors you deploy.
