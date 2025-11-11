# Security Documentation

Envy includes several security features to protect your system and data.

## Security Features

### 1. Sandboxed Execution

All skill executions run in sandboxed environments with resource limits:

- **CPU Limits**: Configurable max CPU usage per profile
- **Memory Limits**: Configurable max memory usage
- **Timeouts**: Skills have execution timeouts (default: 30 seconds)
- **Process Isolation**: Skills run in separate processes

### 2. Command Whitelist

System commands are disabled by default. To enable:

1. Edit `config/envy.yaml`:
```yaml
security:
  allow_system_commands: true
  command_whitelist:
    - "ls"
    - "pwd"
    - "date"
```

2. Only whitelisted commands can be executed
3. Dangerous commands (rm, del, format, etc.) are never allowed

### 3. Confirmation Requirements

Destructive actions require dual confirmation:

1. **Voice Confirmation**: Envy asks for confirmation via voice
2. **Dashboard Confirmation**: User must confirm in web dashboard

To disable (not recommended):
```yaml
security:
  require_voice_confirmation: false
  require_dashboard_confirmation: false
```

### 4. File System Protection

- CodeSkill creates files in workspace directory only
- No access to system directories by default
- File operations are logged

### 5. Network Security

- Remote LLM endpoints are opt-in only
- No data is sent to external services by default
- All network requests are logged

## Disabling System Control

To completely disable system control:

1. Edit `config/envy.yaml`:
```yaml
security:
  allow_system_commands: false
  command_whitelist: []
```

2. Disable SysControlSkill:
```yaml
skills:
  enabled:
    - CodeSkill
    - ResearchSkill
    - ReminderSkill
    # SysControlSkill removed
```

## Safe Mode

For maximum security, use safe mode:

```yaml
security:
  allow_system_commands: false
  command_whitelist: []
  require_voice_confirmation: true
  require_dashboard_confirmation: true
  sandbox_execution: true

skills:
  enabled:
    - CodeSkill
    - ResearchSkill
    - ReminderSkill
  sandbox: true
  require_confirmation: true
```

## Best Practices

1. **Review Skills**: Only enable skills you need
2. **Use Whitelists**: Always use command whitelists if enabling system commands
3. **Monitor Logs**: Regularly check `artifacts/envy.log`
4. **Update Regularly**: Keep dependencies updated
5. **Network Isolation**: Run in isolated network if concerned about data leakage

## Security Considerations

### Local Operation
- All processing happens locally by default
- No data leaves your machine unless explicitly configured
- Models run on your hardware

### Remote LLM (Optional)
- Only enabled if explicitly configured
- Uses free/public endpoints (opt-in)
- All requests are logged
- No sensitive data should be sent

### File Access
- Skills only access workspace directory
- System files are protected
- File operations are logged

## Reporting Issues

If you discover a security vulnerability:

1. Do not create a public issue
2. Review the code and configuration
3. Document the issue
4. Implement fixes if possible

## Compliance

Envy is designed for personal use. For production deployments:

- Review all security settings
- Implement additional access controls
- Add authentication to web dashboard
- Enable audit logging
- Regular security audits
