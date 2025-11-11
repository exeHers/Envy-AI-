# Security Guide

## Overview

Envy is designed with security in mind, but as a system that can execute commands and access files, it requires careful configuration for production use.

## Security Features

### 1. Sandboxing

Envy includes a sandbox system that restricts system command execution:

```yaml
security:
  sandbox_enabled: true
  allowed_commands: []  # Whitelist of allowed commands
```

**Default Behavior:**
- System commands are blocked unless explicitly allowed
- Only safe commands (ls, pwd, date, echo) are permitted by default
- Dangerous commands (rm, del, format, shutdown) require explicit confirmation

### 2. Confirmation Requirements

Destructive actions require dual confirmation:

1. **Voice Confirmation**: User must verbally confirm
2. **Dashboard Confirmation**: User must confirm via web dashboard

```yaml
security:
  require_voice_confirmation: true
  require_dashboard_confirmation: true
```

### 3. File Size Limits

Prevents accidental creation of huge files:

```yaml
security:
  max_file_size_mb: 10
```

### 4. Skill Whitelisting

Only enabled skills can execute:

```yaml
skills:
  enabled:
    - CodeSkill
    - ResearchSkill
    # SysControlSkill disabled by default for safety
```

## Disabling System Control

To completely disable system command execution:

1. **Remove SysControlSkill from enabled skills:**
   ```yaml
   skills:
     enabled:
       - CodeSkill
       - ResearchSkill
       - ReminderSkill
       # SysControlSkill removed
   ```

2. **Keep sandbox enabled:**
   ```yaml
   security:
     sandbox_enabled: true
   ```

## Safe Command Whitelist

To allow specific system commands:

```yaml
security:
  allowed_commands:
    - "ls -la"
    - "git status"
    - "python --version"
```

**Warning**: Only add commands you trust completely.

## Network Security

### Remote LLM Endpoints

Remote LLM endpoints are **disabled by default**:

```yaml
llm:
  remote:
    enabled: false  # Must explicitly enable
```

If enabling remote endpoints:
- Use HTTPS only
- Verify endpoint authenticity
- Consider API key security
- Review privacy policies

### Web Dashboard

Default configuration binds to localhost only:

```yaml
web:
  host: "127.0.0.1"  # Localhost only
  port: 8080
```

**For remote access:**
- Use reverse proxy (nginx, Apache)
- Enable HTTPS/TLS
- Implement authentication
- Use firewall rules

## File System Security

### Workspace Isolation

Envy operates in its workspace directory. To restrict file access:

1. Run Envy in a dedicated directory
2. Use filesystem permissions:
   ```bash
   chmod 700 /opt/envy
   chown envy:envy /opt/envy
   ```

3. Configure workspace in config:
   ```yaml
   # In skill configs
   workspace: "/opt/envy/workspace"
   ```

### Code Execution

CodeSkill creates files but does not execute them by default. To prevent code creation:

1. Remove CodeSkill from enabled skills
2. Or restrict file extensions:
   ```python
   # In CodeSkill implementation
   ALLOWED_EXTENSIONS = ['.txt', '.md', '.json']
   ```

## Best Practices

### 1. Run as Non-Root User

Never run Envy as root:
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash envy
sudo chown -R envy:envy /opt/envy
sudo -u envy ./run_envy_local.sh
```

### 2. Firewall Configuration

Block unnecessary ports:
```bash
# Allow only localhost access
sudo ufw allow from 127.0.0.1 to any port 8080
```

### 3. Regular Updates

Keep dependencies updated:
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### 4. Log Monitoring

Monitor logs for suspicious activity:
```bash
tail -f artifacts/envy.log | grep -i "error\|warning\|command"
```

### 5. Backup Configuration

Regularly backup configuration:
```bash
cp config/envy.yaml config/envy.yaml.backup
```

## Threat Model

### Low Risk
- CodeSkill creating text files
- ResearchSkill generating summaries
- ReminderSkill setting reminders

### Medium Risk
- CodeSkill creating executable scripts
- SysControlSkill executing commands
- File system access

### High Risk
- Network access to remote endpoints
- System command execution
- Running as privileged user

## Incident Response

If security issue detected:

1. **Immediate Actions:**
   - Stop Envy service
   - Review logs: `artifacts/envy.log`
   - Check for unauthorized file changes
   - Review command history

2. **Investigation:**
   - Check system logs
   - Review web dashboard access logs
   - Verify configuration integrity

3. **Remediation:**
   - Update configuration
   - Remove compromised components
   - Change any exposed credentials
   - Restore from backup if needed

## Reporting Issues

If you discover a security vulnerability:
1. Do not disclose publicly
2. Review code and configuration
3. Document the issue
4. Implement fix or workaround

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security.html)
- [Systemd Security Hardening](https://www.freedesktop.org/software/systemd/man/systemd.exec.html)
