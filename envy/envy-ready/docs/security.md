# Envy Security Documentation

Envy includes several security features to protect your system from unauthorized or destructive actions.

## Security Features

### 1. Sandboxing

All system commands are executed in a sandboxed environment with:
- **Whitelist**: Only allowed commands can be executed
- **Blacklist**: Dangerous commands are blocked
- **Confirmation Required**: Destructive actions require explicit confirmation

### 2. Confirmation Flow

Destructive actions require a two-step confirmation:
1. **Voice Confirmation**: Envy will ask for verbal confirmation
2. **Dashboard Confirmation**: You must confirm in the web dashboard

### 3. Command Whitelist

Default allowed commands (configurable in `config/envy.yaml`):
```yaml
skills:
  sandbox:
    allowed_commands:
      - "python"
      - "python3"
      - "echo"
      - "mkdir"
      - "touch"
      - "cat"
      - "ls"
      - "pwd"
```

### 4. Command Blacklist

Default blocked commands:
```yaml
skills:
  sandbox:
    blocked_commands:
      - "rm"
      - "rmdir"
      - "del"
      - "format"
      - "shutdown"
      - "reboot"
```

## Configuration

### Disable System Control

To completely disable system control:

```yaml
skills:
  enabled:
    - CodeSkill
    - ResearchSkill
    - ReminderSkill
    # Remove SysControlSkill from enabled list
```

### Customize Sandbox Rules

Edit `config/envy.yaml`:

```yaml
skills:
  sandbox:
    enabled: true
    allowed_commands:
      - "your-safe-command"
    blocked_commands:
      - "dangerous-command"
    require_confirmation: true
```

### Disable Confirmation (Not Recommended)

```yaml
security:
  require_voice_confirmation: false
  require_dashboard_confirmation: false
```

## Audit Logging

All commands are logged to:
```
artifacts/audit.log
```

Log format:
```
2024-01-01 12:00:00 - SKILL: SysControlSkill - COMMAND: python test.py - USER: confirmed
```

## Best Practices

1. **Review Logs Regularly**: Check `artifacts/audit.log` for suspicious activity
2. **Limit Allowed Commands**: Only enable commands you trust
3. **Use Confirmation**: Keep confirmation enabled for destructive actions
4. **Monitor Dashboard**: Watch the web dashboard for unexpected commands
5. **Restrict Network Access**: If using remote LLM, use secure endpoints

## Disabling System Control

If you want to completely disable system control:

1. Edit `config/envy.yaml`
2. Remove `SysControlSkill` from enabled skills:
   ```yaml
   skills:
     enabled:
       - CodeSkill
       - ResearchSkill
       - ReminderSkill
   ```
3. Restart Envy

## Security Considerations

- **Local Models**: Using local LLM models keeps all data on your machine
- **Remote Endpoints**: If using remote LLM, ensure endpoints use HTTPS
- **File Access**: Skills can create/modify files in the workspace directory
- **Network Access**: ResearchSkill may make network requests (if implemented)

## Reporting Issues

If you discover a security vulnerability:
1. Do not create a public issue
2. Review the code and suggest fixes
3. Test fixes in a safe environment
