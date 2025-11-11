# Security Documentation

Envy is designed with security and privacy as core principles. This document explains the security features and best practices.

## Security Philosophy

1. **Privacy First**: All processing happens locally by default
2. **Sandboxed Execution**: Skills run in isolated environments
3. **Explicit Confirmation**: Dangerous actions require approval
4. **Minimal Permissions**: Principle of least privilege
5. **Transparent Operations**: All actions are logged

## Privacy & Data

### What Data is Processed Locally?

- Voice input (microphone)
- Speech recognition (STT)
- Natural language processing (LLM)
- Text-to-speech (TTS)
- File operations
- Skill execution

**None of this data leaves your machine by default.**

### What Data Might be Sent Remotely?

Only if you explicitly enable remote LLM fallback:

```yaml
llm:
  remote:
    enabled: true  # DEFAULT: false
```

When enabled, user prompts may be sent to:
- Hugging Face Inference API (free tier)

**To ensure complete privacy, keep `llm.remote.enabled: false`**

### Data Storage

Envy stores:
- Configuration: `config/envy.yaml`
- Logs: `artifacts/logs/envy.log`
- TTS output: `artifacts/tts-output.wav`
- Research files: `artifacts/research/`
- Reminders: `artifacts/reminders.json`

All stored locally. No cloud sync.

## Skill Security

### Sandboxing

Skills run with:
- **Process Isolation**: Separate processes with timeouts
- **Resource Limits**: CPU and memory constraints
- **File System Restrictions**: Limited write access

Configure in `config/envy.yaml`:

```yaml
skills:
  sandboxed: true  # RECOMMENDED: true
  timeout: 60      # Max execution time (seconds)
```

### Skill Permissions

Each skill has different permission levels:

#### CodeSkill (Safe)
- Creates files in workspace
- Limited to allowed extensions
- Cannot delete or modify system files

```yaml
skills:
  code:
    allowed_extensions: [".py", ".js", ".txt", ".md"]
    max_file_size_kb: 1024
```

#### ResearchSkill (Safe)
- Generates text summaries
- Saves to research directory
- No system access

#### ReminderSkill (Safe)
- Stores data in JSON file
- No external access
- Read/write to reminders file only

#### SysControlSkill (DANGEROUS - Disabled by Default)

**THIS SKILL IS DISABLED BY DEFAULT**

Enables system command execution. Only enable if you understand the risks:

```yaml
skills:
  syscontrol:
    enabled: false  # DEFAULT: false
    require_confirmation: true
    whitelist: ["ls", "pwd", "date"]  # Only allow these commands
    blacklist: ["rm", "sudo", "shutdown"]  # Never allow these
```

**Security recommendations:**
1. Keep disabled unless absolutely needed
2. Use strict whitelist (specific commands only)
3. Never add `rm`, `sudo`, or destructive commands
4. Enable confirmation requirement
5. Monitor logs carefully

## Confirmation System

### Voice Confirmation

Destructive actions require voice confirmation:

```yaml
security:
  require_voice_confirmation: true
```

### Dashboard Confirmation

Web dashboard provides visual confirmation for sensitive actions.

### Destructive Actions

Defined in config:

```yaml
security:
  destructive_actions:
    - delete
    - remove
    - shutdown
    - reboot
    - kill
```

These always require explicit confirmation.

## Network Security

### Local-Only Mode (Default)

By default, Envy only listens locally:

```yaml
web:
  host: "127.0.0.1"  # Local only
  port: 8080
```

**Do not expose to internet without proper security!**

### Exposing Dashboard (Not Recommended)

If you must expose the dashboard:

```yaml
web:
  host: "0.0.0.0"  # Listen on all interfaces
```

**Then secure with:**
1. Firewall rules
2. VPN access
3. Reverse proxy with authentication
4. HTTPS with valid certificate

## File System Security

### Restricted Write Access

Envy only writes to:
- `artifacts/` - Logs, outputs, research
- Configured workspace (default: `/workspace`)
- Skill-specific directories

### File Validation

CodeSkill validates:
- File extensions (whitelist)
- File size limits
- Path traversal attempts

```python
# Path traversal protection
if ".." in filename or "/" in filename:
    reject()
```

## Command Execution Security

### Sandboxing System Commands

When SysControlSkill is enabled:

1. **Whitelist Check**: Command must be in whitelist
2. **Blacklist Check**: Command must not contain blacklisted terms
3. **Timeout**: Max execution time enforced
4. **No Shell Expansion**: No wildcards, pipes, or redirects (by default)

### Example Safe Configuration

```yaml
skills:
  syscontrol:
    enabled: true
    whitelist:
      - "ls -la"
      - "pwd"
      - "date"
      - "uptime"
      - "df -h"
    blacklist:
      - "rm"
      - "sudo"
      - "kill"
      - "shutdown"
      - "reboot"
      - ">"   # No redirects
      - "|"   # No pipes
      - "&&"  # No chaining
```

## Logging & Auditing

### What is Logged?

- All voice commands
- Skill executions
- Errors and warnings
- System events

Location: `artifacts/logs/envy.log`

### Log Rotation

Logs are automatically rotated:

```yaml
logging:
  max_size_mb: 100
  backup_count: 5
```

Keeps last 5 log files, 100MB each.

### Sensitive Data in Logs

Logs may contain:
- Voice transcriptions
- Commands executed
- File paths

**Protect log files:**

```bash
chmod 600 artifacts/logs/envy.log
```

## Resource Limits

Prevent resource exhaustion:

```yaml
resources:
  max_cpu_percent: 50    # Max CPU per service
  max_memory_mb: 4096    # Max memory per service
  
skills:
  timeout: 60            # Max skill execution time
```

## Running as Service

### Linux (systemd)

Service file includes resource limits:

```ini
[Service]
CPUQuota=50%
MemoryMax=4G
```

### Windows (NSSM)

Configure resource limits in NSSM:

```cmd
nssm set Envy AppThrottle 5000  # CPU throttle
```

## Best Practices

### 1. Keep Software Updated

```bash
# Update dependencies regularly
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### 2. Review Configuration

Regularly audit `config/envy.yaml`:
- Disable unused skills
- Tighten resource limits
- Review whitelists

### 3. Monitor Logs

```bash
# Watch logs in real-time
tail -f artifacts/logs/envy.log

# Search for errors
grep ERROR artifacts/logs/envy.log
```

### 4. Principle of Least Privilege

Only enable what you need:
- Disable remote LLM fallback if not needed
- Keep SysControlSkill disabled
- Use CPU-only mode if GPU not needed

### 5. Isolate Envy User

Run Envy as dedicated user:

```bash
# Create envy user
sudo useradd -r -s /bin/false envy

# Run service as envy user
sudo systemctl edit envy
```

## Threat Model

### What Envy Protects Against

- ✅ Remote data collection (all local by default)
- ✅ Unauthorized file access (sandboxing)
- ✅ Resource exhaustion (limits)
- ✅ Accidental destructive commands (confirmation)

### What Envy Does NOT Protect Against

- ❌ Physical access to the machine
- ❌ Malicious skills (review skills before loading)
- ❌ Network attacks if exposed to internet
- ❌ Root/admin-level exploits in dependencies

## Incident Response

If you suspect a security issue:

1. **Stop Envy immediately**
   ```bash
   sudo systemctl stop envy
   ```

2. **Review logs**
   ```bash
   cat artifacts/logs/envy.log
   ```

3. **Check for unexpected files**
   ```bash
   find /workspace -mtime -1  # Files modified in last day
   ```

4. **Restore from backup** if needed

5. **Update and harden configuration**

## Security Checklist

Before deploying Envy:

- [ ] Local LLM configured (remote disabled)
- [ ] SysControlSkill disabled (or strict whitelist)
- [ ] Web dashboard on localhost only
- [ ] Resource limits configured
- [ ] Confirmation enabled for destructive actions
- [ ] Regular log review scheduled
- [ ] Backups configured
- [ ] File permissions secured
- [ ] Running as non-root user
- [ ] Firewall rules configured

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do not open a public issue**
2. Document the issue privately
3. Report through appropriate channels
4. Allow time for fix before disclosure

## Compliance Notes

### GDPR

Envy processes data locally:
- No data transmission (by default)
- No data retention beyond local storage
- User has full control over data

### Audio Recording

Some jurisdictions require consent before recording:
- Envy records audio from microphone
- Ensure compliance with local laws
- Display notice if required

---

**Security is a shared responsibility. Review this document carefully and configure Envy according to your security requirements.**
