# Envy AI Assistant - Security Documentation

Security architecture, best practices, and configuration for safe operation.

---

## Security Philosophy

Envy is designed with **security-first principles**:

1. **Local-first**: All processing happens on your machine by default
2. **Sandboxed execution**: Skills run in restricted environments
3. **Explicit permissions**: Dangerous actions require confirmation
4. **Minimal privileges**: Services run with least necessary permissions
5. **Transparent operation**: All actions are logged and auditable

---

## Threat Model

### Assumptions

- **Physical security**: Attacker does not have physical access to the machine
- **OS security**: The underlying OS is reasonably secure and up-to-date
- **User trust**: The user is not intentionally trying to break the system
- **Network security**: Basic network security measures are in place

### Threats Addressed

1. **Command injection**: Malicious voice commands
2. **File system access**: Unauthorized file read/write/delete
3. **System compromise**: Execution of dangerous system commands
4. **Data exfiltration**: Unauthorized network access
5. **Resource exhaustion**: DoS via excessive resource consumption

---

## Security Features

### 1. Sandboxed Skill Execution

All skills run with restrictions:

```yaml
security:
  sandbox_execution: true
  max_file_size_mb: 10
  blocked_paths:
    - "/etc"
    - "/sys"
    - "/proc"
    - "C:\\Windows"
    - "C:\\System32"
```

**Implementation**:
- File operations limited to `workspace/` directory
- System paths are blacklisted
- File size limits prevent DoS
- Execution timeouts prevent hanging

### 2. Command Whitelisting

System commands are whitelisted by default:

```yaml
skills:
  sys_control_skill:
    whitelist_mode: true
    allowed_commands:
      - "echo"
      - "date"
      - "uptime"
      - "whoami"
```

**Only safe, read-only commands are allowed by default.**

To add commands:

```yaml
allowed_commands:
  - "ls"
  - "cat"
  # Never add: rm, dd, shutdown, format, etc.
```

### 3. Confirmation Workflows

Destructive actions require dual confirmation:

```yaml
security:
  require_voice_confirmation: true
  require_dashboard_confirmation: true
```

**Flow**:
1. User: "Delete all files"
2. Envy: "This requires confirmation" (voice)
3. Dashboard displays action preview
4. User confirms via voice AND dashboard
5. Action executes

**Destructive actions**:
- File deletion
- System shutdown/reboot
- User account modifications
- Network configuration changes

### 4. Privacy Protection

#### Local Processing

All core operations are local:
- Wake word detection: VOSK (local)
- Speech recognition: Faster-Whisper (local)
- LLM inference: llama.cpp (local)
- Text-to-speech: pyttsx3 (local)

**No data is sent to external servers by default.**

#### Optional Remote Fallback

Remote LLM fallback is **disabled by default**:

```yaml
llm:
  remote:
    enabled: false  # DISABLED
```

To enable (opt-in):

```yaml
llm:
  remote:
    enabled: true
    provider: "huggingface"
    api_key: ""  # Free tier, no key needed
```

**When using remote fallback**:
- Only text prompts are sent (no audio)
- No personally identifiable information
- User is informed via logs
- Can be disabled anytime

### 5. Resource Limits

Prevent resource exhaustion:

```yaml
profiles:
  balanced:
    max_cpu_percent: 60
    max_memory_mb: 4096

skills:
  max_execution_time: 60  # seconds
```

**Linux (systemd)**:

```ini
MemoryMax=4G
CPUQuota=60%
```

### 6. Logging and Auditing

All actions are logged:

```
2025-11-11 10:30:45 - INFO - Wake word detected
2025-11-11 10:30:50 - INFO - User said: create test.py
2025-11-11 10:30:51 - INFO - Executing skill: code_skill
2025-11-11 10:30:52 - INFO - File created: workspace/test.py
```

**Log locations**:
- Main log: `artifacts/logs/envy.log`
- Service log: `journalctl -u envy@$USER` (Linux)
- Metrics: `artifacts/logs/metrics.json`

---

## Security Best Practices

### Configuration

#### 1. Use Restrictive Defaults

```yaml
security:
  sandbox_execution: true
  require_voice_confirmation: true
  require_dashboard_confirmation: true
```

#### 2. Minimal Whitelist

Only add commands you actually need:

```yaml
skills:
  sys_control_skill:
    whitelist_mode: true
    allowed_commands:
      - "echo"
      - "date"
      # Add others carefully
```

#### 3. Block Sensitive Paths

```yaml
security:
  blocked_paths:
    - "/etc"
    - "/home/user/.ssh"
    - "/root"
    - "C:\\Windows"
```

#### 4. Disable Remote Services

```yaml
llm:
  remote:
    enabled: false
```

### Deployment

#### 1. Run as Non-Root User

**Never run Envy as root/administrator.**

Linux:
```bash
# Good
./run_envy_local.sh

# Bad
sudo ./run_envy_local.sh
```

#### 2. Use Systemd Hardening

The included systemd service has security features:

```ini
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/opt/envy/data /opt/envy/artifacts
```

#### 3. Firewall Configuration

Only expose necessary ports:

```bash
# Allow only localhost access
# config/envy.yaml
web_dashboard:
  host: "127.0.0.1"  # Not 0.0.0.0
  port: 8080
```

For remote access, use SSH tunnel:

```bash
ssh -L 8080:localhost:8080 user@remote-host
```

#### 4. Regular Updates

Keep dependencies updated:

```bash
pip install --upgrade -r requirements.txt
```

Monitor for security advisories.

### Network Security

#### 1. Local-Only by Default

```yaml
web_dashboard:
  host: "127.0.0.1"  # Localhost only
```

#### 2. HTTPS (if exposing publicly)

Use reverse proxy (nginx, Apache) with TLS:

```nginx
server {
    listen 443 ssl;
    server_name envy.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
    }
}
```

#### 3. Authentication

For remote access, add authentication layer:
- Nginx basic auth
- OAuth proxy (oauth2-proxy)
- VPN access only

---

## Vulnerability Reporting

If you discover a security vulnerability:

1. **Do not** create a public issue
2. Email security contact (if available)
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

---

## Security Checklist

### Installation

- [ ] Install as non-root user
- [ ] Use virtual environment
- [ ] Review `config/envy.yaml` settings
- [ ] Set restrictive file permissions
- [ ] Verify remote services are disabled

### Configuration

- [ ] `sandbox_execution: true`
- [ ] `whitelist_mode: true`
- [ ] `require_voice_confirmation: true`
- [ ] `require_dashboard_confirmation: true`
- [ ] `host: "127.0.0.1"` (web dashboard)
- [ ] Minimal command whitelist
- [ ] Blocked sensitive paths

### Deployment

- [ ] Service runs as non-root
- [ ] Systemd security features enabled
- [ ] Firewall configured
- [ ] Logs monitored
- [ ] Updates scheduled

### Operation

- [ ] Review logs regularly
- [ ] Monitor resource usage
- [ ] Audit command history
- [ ] Test confirmation workflows
- [ ] Update dependencies monthly

---

## Known Limitations

### 1. Voice Spoofing

Envy cannot distinguish between the legitimate user and an attacker with voice access.

**Mitigation**:
- Physical security (lock room when away)
- Disable wake word when not needed
- Use confirmation workflows for dangerous actions

### 2. Local Privilege Escalation

If the OS is compromised, Envy's sandboxing may be bypassed.

**Mitigation**:
- Keep OS updated
- Use security features (SELinux, AppArmor)
- Regular security scans

### 3. Web Dashboard

The web dashboard has minimal authentication.

**Mitigation**:
- Bind to localhost only
- Use SSH tunnel for remote access
- Add reverse proxy with auth for public access

### 4. Dependency Vulnerabilities

Python packages may have vulnerabilities.

**Mitigation**:
- Regular updates
- Monitor CVE databases
- Use `pip-audit` to check for known issues

---

## Security Monitoring

### Log Analysis

Monitor for suspicious activity:

```bash
# Failed skill executions
grep "ERROR" artifacts/logs/envy.log

# System commands
grep "sys_control_skill" artifacts/logs/envy.log

# File operations
grep "file_created\|file_deleted" artifacts/logs/envy.log
```

### Resource Monitoring

Watch for resource exhaustion:

```bash
# CPU/Memory usage
htop

# GPU usage (if applicable)
nvidia-smi

# Disk usage
df -h
```

### Automated Monitoring

Set up alerts for:
- Excessive CPU/memory usage
- Repeated failed skill executions
- Unusual system commands
- Confirmation bypass attempts

---

## Compliance

### Data Privacy

Envy respects data privacy:

- **GDPR**: No data sent to third parties (local processing)
- **CCPA**: User data stays on local machine
- **HIPAA**: Can be used in compliant manner (local-only mode)

### Audit Trail

All actions are logged for compliance:

```json
{
  "timestamp": "2025-11-11T10:30:52Z",
  "user": "local",
  "action": "file_created",
  "details": {
    "skill": "code_skill",
    "file": "workspace/test.py"
  }
}
```

---

## Advanced Security

### AppArmor Profile (Linux)

Create `/etc/apparmor.d/opt.envy.envy_main`:

```
#include <tunables/global>

/opt/envy/envy_main.py {
  #include <abstractions/base>
  #include <abstractions/python>
  
  /opt/envy/** r,
  /opt/envy/workspace/** rw,
  /opt/envy/data/** rw,
  /opt/envy/artifacts/** rw,
  
  deny /etc/** rw,
  deny /root/** rw,
  deny /home/*/.ssh/** rw,
}
```

### SELinux Policy (Red Hat/Fedora)

Custom SELinux policy can be created for additional isolation.

### Container Deployment

Run in Docker for maximum isolation:

```dockerfile
FROM python:3.10-slim

RUN useradd -m envy
USER envy

COPY --chown=envy:envy . /home/envy/envy
WORKDIR /home/envy/envy

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "envy_main.py"]
```

---

## Conclusion

Envy is designed with security as a priority. By following these guidelines and using the built-in security features, you can safely run a powerful AI assistant on your local machine.

**Remember**: Security is a process, not a product. Stay vigilant, keep systems updated, and monitor logs regularly.

---

**For questions or concerns, check the [main README](../README.md) or report security issues responsibly.**
