# Security Documentation for Envy

## Overview

Envy is designed with security as a priority. All potentially dangerous operations require explicit confirmation, and system commands are sandboxed by default.

## Security Features

### 1. Sandboxed Execution

By default, Envy runs in a sandboxed environment:
- File operations are restricted to allowed paths (default: `workspace/`)
- System commands are disabled by default
- Dangerous operations require confirmation

### 2. Confirmation Flow

Sensitive actions require two-step confirmation:
1. **Voice Confirmation**: User must verbally confirm
2. **Dashboard Confirmation**: User must confirm via web dashboard

This applies to:
- System control commands (SysControlSkill)
- File operations outside workspace
- Any action marked as requiring confirmation

### 3. Skill Sandboxing

Each skill runs with restricted permissions:
- **CodeSkill**: Can only create files in `workspace/`
- **SysControlSkill**: Requires explicit enablement in config
- **ResearchSkill**: File operations limited to workspace
- **ReminderSkill**: Only creates reminder files

### 4. Configuration Security

Edit `config/envy.yaml` to customize security:

```yaml
skills:
  sandbox:
    enabled: true  # Enable sandboxing
    allowed_commands: []  # Empty = no system commands
    allowed_paths: ["workspace"]  # Allowed file paths
```

### 5. Disabling System Control

To completely disable system control:

1. Edit `config/envy.yaml`
2. Set `skills.sandbox.allowed_commands: []` (empty list)
3. Remove `SysControlSkill` from `skills.enabled`

### 6. Enabling Safe System Commands

To allow specific safe commands:

```yaml
skills:
  sandbox:
    allowed_commands:
      - "echo"
      - "date"
      - "whoami"
      - "pwd"
```

**Warning**: Only add commands you trust. System commands can be dangerous.

### 7. Network Security

- Web dashboard runs on `127.0.0.1` by default (localhost only)
- No external network access required for core functionality
- Remote LLM endpoints are opt-in and disabled by default

### 8. File Size Limits

Large file operations are restricted:
- Default max file size: 10MB
- Configurable in `config/envy.yaml`:
  ```yaml
  security:
    max_file_size_mb: 10
  ```

### 9. Resource Limits

Prevent resource exhaustion:
- CPU usage capped (default: 50%)
- Memory limits enforced
- GPU memory limits for safety

### 10. Logging

All actions are logged to `artifacts/envy.log`:
- User commands
- Skill executions
- Errors and warnings
- Security events

## Best Practices

1. **Review Logs Regularly**: Check `artifacts/envy.log` for suspicious activity
2. **Keep Workspace Clean**: Regularly clean `workspace/` directory
3. **Use Low Profile**: For untrusted environments, use `--profile low`
4. **Monitor Resources**: Watch CPU/GPU usage via dashboard
5. **Update Regularly**: Keep dependencies updated for security patches

## Threat Model

Envy is designed for:
- ✅ Personal use on trusted machines
- ✅ Local development assistance
- ✅ Voice-controlled automation

Not designed for:
- ❌ Multi-user environments without isolation
- ❌ Production servers without additional hardening
- ❌ Untrusted network environments

## Reporting Security Issues

If you discover a security vulnerability:
1. Do not open a public issue
2. Review the code and suggest a fix
3. Test your fix in a safe environment
4. Submit a pull request with security improvements

## Additional Hardening

For production or high-security environments:

1. **Run as Non-Root User**: Never run Envy as root/admin
2. **Use Firewall**: Block external access to dashboard port
3. **Enable HTTPS**: Use reverse proxy with SSL for dashboard
4. **Audit Logs**: Set up log rotation and monitoring
5. **Isolate Network**: Run in isolated network segment
6. **Regular Updates**: Keep all dependencies updated

## Default Security Posture

Out of the box, Envy:
- ✅ Sandboxes all file operations
- ✅ Disables system commands
- ✅ Requires confirmations for dangerous actions
- ✅ Limits resource usage
- ✅ Logs all activities
- ✅ Runs dashboard on localhost only

This provides a secure default while allowing customization for trusted environments.
