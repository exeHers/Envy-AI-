# Security Guide

Envy includes multiple security layers to protect your system from accidental or malicious commands.

## Overview

Envy's security model:
1. **Command Whitelisting**: Only approved commands can execute
2. **Voice Confirmation**: Speak "yes" or "confirm" for sensitive actions
3. **Dashboard Confirmation**: Click "Confirm" in web interface
4. **Sandboxing**: Skills run in isolated processes with timeouts
5. **Resource Limits**: CPU, memory, and execution time constraints

## System Control Security

### Command Whitelist

By default, only safe read-only commands are allowed:

```yaml
sys_control:
  whitelist_commands:
    - ls
    - pwd
    - date
    - echo
    - whoami
    - df
    - free
    - uptime
    - uname
```

### Adding Commands to Whitelist

Edit `config/envy.yaml`:

```yaml
sys_control:
  whitelist_commands:
    - ls
    - pwd
    - git        # Add git
    - docker     # Add docker
    # ... more commands
```

**⚠️ Warning**: Only add commands you trust!

### Dangerous Commands

These commands are **NEVER** allowed by default:
- `rm`, `rmdir` - File deletion
- `dd` - Disk writing
- `mkfs` - Filesystem creation
- `chmod`, `chown` - Permission changes
- `sudo`, `su` - Privilege escalation
- `systemctl` - Service management
- `reboot`, `shutdown` - System control

## Confirmation Flow

### Skills Requiring Confirmation

Configure in `config/envy.yaml`:

```yaml
skills:
  require_confirmation:
    - SysControlSkill  # Always require confirmation
    # Add more skills as needed
```

### Confirmation Process

1. **Voice Command**: "Envy, run the date command"
2. **Envy Response**: "This action requires confirmation. Please confirm to proceed."
3. **Voice Confirmation**: Say "yes" or "confirm"
4. **Dashboard Confirmation**: Click "Confirm" button in web dashboard
5. **Execution**: Command runs only after both confirmations

### Disabling Confirmation (Not Recommended)

```yaml
sys_control:
  require_voice_confirmation: false
  require_dashboard_confirmation: false
```

## Sandboxing

### Process Isolation

Skills run in separate processes:
- Cannot access parent process memory
- Limited system resources
- Timeout enforcement

### Timeouts

Configure in `config/envy.yaml`:

```yaml
skills:
  timeout: 60  # seconds per skill execution
```

If a skill exceeds the timeout, it's terminated.

### Resource Limits

```yaml
resources:
  balanced:
    max_cpu_percent: 60
    max_memory_mb: 4096
```

Skills that exceed these limits are terminated.

## Web Dashboard Security

### Network Access

By default, dashboard only listens on localhost:

```yaml
web:
  enabled: true
  host: "127.0.0.1"  # Only local access
  port: 8080
```

### Remote Access (Use with Caution)

To allow remote access:

```yaml
web:
  host: "0.0.0.0"  # Listen on all interfaces
```

**⚠️ Warning**: This exposes the dashboard to your network!

Recommended: Use SSH tunnel instead:
```bash
ssh -L 8080:localhost:8080 user@remote-machine
```

Then access via: http://localhost:8080

### Authentication

Current version does NOT include authentication. If you need remote access:

1. Use SSH tunnel (recommended)
2. Use VPN
3. Add reverse proxy with authentication (nginx, Caddy)

Example nginx config:
```nginx
location /envy/ {
    auth_basic "Envy Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://127.0.0.1:8080/;
}
```

## File System Access

### Workspace Isolation

Skills can only create files in the workspace:

```yaml
skills:
  workspace_path: "workspace"  # Relative to Envy root
```

Skills cannot:
- Write outside workspace
- Delete system files
- Modify configuration

### CodeSkill Safety

CodeSkill can create files but:
- Only in workspace directory
- Cannot overwrite existing files without confirmation
- Cannot execute created files automatically

## Voice Data Privacy

### Local Processing

All voice processing happens locally:
- Wake word detection: Local (VOSK)
- Speech-to-text: Local (Whisper)
- Text-to-speech: Local (pyttsx3)
- LLM inference: Local (llama.cpp)

**No voice data is sent to cloud services by default.**

### Optional Remote LLM

If you enable remote LLM fallback:

```yaml
llm:
  remote:
    enabled: true  # ⚠️ Sends text to remote API
    provider: "huggingface-inference"
```

**Warning**: This sends transcribed text (not audio) to the remote service.

## Model Security

### Model Verification

Verify downloaded models:

```bash
# Check SHA256 hash
sha256sum models/llama-2-7b-chat.Q4_K_M.gguf

# Compare with official hash from model page
```

### Trusted Sources

Only download models from:
- alphacephei.com (VOSK)
- huggingface.co (Whisper, LLMs)
- Official repositories

**Never** run untrusted model files!

## Logging

### Log Contents

Logs may contain:
- Voice transcriptions
- Executed commands
- System information
- Error messages

### Log Rotation

```yaml
logging:
  max_size_mb: 100
  backup_count: 3  # Keep 3 old log files
```

### Clearing Logs

```bash
rm -rf logs/*
```

## Best Practices

### 1. Minimal Privileges
- Run Envy as regular user (not root/admin)
- Don't add dangerous commands to whitelist
- Keep confirmation requirements enabled

### 2. Network Security
- Keep dashboard on localhost
- Use SSH tunnels for remote access
- Consider firewall rules

### 3. Regular Updates
- Update dependencies regularly:
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### 4. Monitor Activity
- Check logs regularly
- Review executed commands
- Monitor resource usage

### 5. Disable Unused Features
```yaml
skills:
  enabled_skills:
    - CodeSkill
    - ResearchSkill
    # Comment out unused skills
    # - SysControlSkill
```

## Incident Response

### Suspicious Activity Detected

1. **Stop Envy**:
```bash
sudo systemctl stop envy
```

2. **Check logs**:
```bash
tail -n 100 logs/envy.log
```

3. **Review executed commands**:
```bash
grep "execute_command" logs/envy.log
```

4. **Review created files**:
```bash
ls -la workspace/
```

5. **Check system changes**:
```bash
# Recent file changes
find / -mtime -1 -type f 2>/dev/null
```

### Reset Configuration

```bash
# Backup current config
cp config/envy.yaml config/envy.yaml.backup

# Restore defaults
cp config/envy.yaml.default config/envy.yaml
```

## Reporting Security Issues

Found a security issue?

1. **Do not** post publicly
2. Document the issue
3. Include steps to reproduce
4. Include Envy version and config

## Security Checklist

- [ ] Command whitelist configured
- [ ] Confirmation requirements enabled
- [ ] Dashboard on localhost only
- [ ] Running as non-privileged user
- [ ] Sensitive logs cleared
- [ ] Remote LLM disabled (or understood)
- [ ] Regular dependency updates scheduled
- [ ] Firewall configured (if using remote dashboard)
- [ ] Workspace directory isolated
- [ ] Skill timeouts configured

## Additional Resources

- [System Control Skill](../skills/sys_control_skill.py)
- [Configuration Reference](configuration.md)
- [Installation Guides](install-linux.md)
