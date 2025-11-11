# 🔒 Envy Security Guide

This document explains the security features and best practices for Envy Personal Assistant.

## Security Architecture

### 1. Sandboxed Execution

All skills run with restricted permissions:

- **Process Isolation**: Skills execute in separate contexts
- **Timeout Limits**: Operations timeout after configurable duration
- **Resource Limits**: CPU and memory caps prevent resource exhaustion

### 2. Command Whitelisting

System commands are restricted by default:

```yaml
skills:
  sys_control_skill:
    enabled: true
    require_confirmation: true
    allowed_commands:
      - "date"
      - "time"
      - "uptime"
      - "df -h"
      - "free -h"
    dangerous_commands:
      - "rm"
      - "del"
      - "format"
      - "shutdown"
      - "reboot"
```

**Default Behavior:**
- Only whitelisted commands execute
- Dangerous commands are blocked
- Whitelist-only mode enabled by default

### 3. Confirmation Requirements

Destructive actions require multiple confirmations:

1. **Voice Confirmation**: User must confirm via voice
2. **Dashboard Confirmation**: User must confirm in web interface
3. **Execute**: Only after both confirmations

**Configuration:**
```yaml
security:
  require_voice_confirmation: true
  require_dashboard_confirmation: true
  sandbox_mode: true
  whitelist_only: true
```

### 4. File System Isolation

CodeSkill operates in restricted workspace:

- **Workspace Directory**: All file operations in `workspace/` only
- **Extension Whitelist**: Only allowed file types can be created
- **Size Limits**: Maximum file size restrictions
- **No System Files**: Cannot access system directories

**Configuration:**
```yaml
skills:
  code_skill:
    workspace_dir: "workspace"
    allowed_extensions: [".py", ".js", ".html", ".css", ".txt", ".md"]
    max_file_size_kb: 1024
```

### 5. Network Isolation

By default, Envy runs entirely offline:

- **Local Models**: All AI processing on-device
- **No External Calls**: No internet requests required
- **Optional Remote**: Remote LLM is opt-in and disabled by default

**Remote LLM (Optional):**
```yaml
llm:
  local_enabled: true
  remote_enabled: false  # Disabled by default
  remote_endpoint: ""    # No endpoint configured
  remote_api_key: ""     # No API key stored
```

### 6. Data Privacy

All data stays on your machine:

- **No Telemetry**: No usage statistics sent anywhere
- **Local Storage**: All data in local files
- **No Cloud Sync**: No automatic cloud uploads
- **User Control**: You own all data

## Best Practices

### For Home Use

1. **Keep Whitelist Minimal**: Only add commands you actually need
2. **Review Logs Regularly**: Check `logs/envy.log` for unusual activity
3. **Use Confirmation**: Keep voice/dashboard confirmation enabled
4. **Limit Network Access**: Keep remote LLM disabled unless needed
5. **Update Config**: Review `config/envy.yaml` after installation

### For Development

1. **Test in Sandbox**: Always test new skills in isolated environment
2. **Validate Inputs**: Sanitize all user inputs in custom skills
3. **Handle Errors**: Use try/except to prevent crashes
4. **Resource Limits**: Respect timeout and resource configurations
5. **Document Changes**: Comment security-relevant code

### For Advanced Users

1. **Firewall Rules**: Consider blocking outbound connections
2. **Separate User**: Run Envy under dedicated low-privilege user
3. **AppArmor/SELinux**: Use mandatory access control if available
4. **Audit Logs**: Enable detailed logging for security audits
5. **Regular Backups**: Backup workspace and config regularly

## Disabling System Control

If you don't need system command execution:

```yaml
skills:
  sys_control_skill:
    enabled: false  # Completely disable the skill
```

Or restrict to read-only commands:

```yaml
skills:
  sys_control_skill:
    enabled: true
    allowed_commands:
      - "date"
      - "uptime"
      # Remove any write/modify commands
```

## Custom Skill Security

When creating custom skills:

### DO:
- ✅ Validate all inputs
- ✅ Use whitelist approach for allowed operations
- ✅ Set timeouts on long-running operations
- ✅ Handle exceptions gracefully
- ✅ Log security-relevant events
- ✅ Require confirmations for destructive actions

### DON'T:
- ❌ Execute arbitrary user input as shell commands
- ❌ Access files outside workspace without explicit permission
- ❌ Make network requests without user consent
- ❌ Store sensitive data in plain text
- ❌ Trust external data sources without validation
- ❌ Disable security checks for convenience

### Example Secure Skill:

```python
from skills.base_skill import BaseSkill
import re

class SecureSkill(BaseSkill):
    def execute(self, action, command, parameters):
        # 1. Validate inputs
        if not self._validate_command(command):
            return self.error_response("Invalid command")
        
        # 2. Check permissions
        if not self._has_permission(action):
            return self.error_response("Permission denied")
        
        # 3. Sanitize inputs
        safe_command = self._sanitize(command)
        
        # 4. Execute with timeout
        try:
            result = self._execute_with_timeout(safe_command, timeout=30)
            return self.success_response(result)
        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            return self.error_response("Execution failed")
    
    def _validate_command(self, command):
        # Only allow alphanumeric and basic punctuation
        return bool(re.match(r'^[a-zA-Z0-9\s\.\-_]+$', command))
```

## Security Updates

### Keeping Envy Secure

1. **Update Dependencies**: Regularly update Python packages
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Review Config**: Check configuration after updates
   ```bash
   cat config/envy.yaml
   ```

3. **Monitor Logs**: Watch for unusual patterns
   ```bash
   tail -f logs/envy.log
   ```

4. **Test Changes**: Run tests after modifications
   ```bash
   python tests/run_tests.py
   ```

## Incident Response

If you suspect security issues:

1. **Stop Envy**: Immediately stop the service
   ```bash
   sudo systemctl stop envy  # Linux
   # or
   nssm stop Envy  # Windows
   ```

2. **Review Logs**: Check what happened
   ```bash
   grep -i "error\|warn\|fail" logs/envy.log
   ```

3. **Check Files**: Verify workspace integrity
   ```bash
   ls -la workspace/
   ```

4. **Reset Config**: Restore default configuration
   ```bash
   cp config/envy.yaml.backup config/envy.yaml
   ```

5. **Restart Clean**: Start with fresh state
   ```bash
   rm -rf workspace/*
   ./run_envy_local.sh
   ```

## Reporting Issues

For security concerns:

1. Document the issue thoroughly
2. Include log excerpts (sanitize personal data)
3. Describe steps to reproduce
4. Note your system configuration
5. Keep report confidential until resolved

## Compliance Notes

Envy is designed for personal use and includes:

- **Data Sovereignty**: All data stays local
- **No Tracking**: No user behavior tracking
- **No Account**: No registration or authentication required
- **Open Source**: Full source code available for audit
- **No Cloud**: No cloud services required

For enterprise or regulated environments, additional security hardening may be required.

---

**Security is a shared responsibility. Use Envy responsibly and stay vigilant!**
