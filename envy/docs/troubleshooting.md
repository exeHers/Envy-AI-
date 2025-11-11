# Troubleshooting Guide

Common issues and solutions for Envy Personal Assistant.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Audio Problems](#audio-problems)
- [Model Issues](#model-issues)
- [Performance Issues](#performance-issues)
- [GPU Issues](#gpu-issues)
- [Service Issues](#service-issues)
- [General Debugging](#general-debugging)

## Installation Issues

### Python Version Error

**Error:** `Python 3.10+ required`

**Solution:**
```bash
# Check version
python3 --version

# Install Python 3.10+ from python.org or your package manager
```

### pip Install Fails

**Error:** `error: Microsoft Visual C++ 14.0 or greater is required`

**Solution (Windows):**
1. Install Visual C++ Build Tools
2. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

**Solution (Linux):**
```bash
sudo apt install build-essential python3-dev
```

### Virtual Environment Issues

**Error:** `No module named 'venv'`

**Solution:**
```bash
# Ubuntu/Debian
sudo apt install python3-venv

# Or use virtualenv instead
pip install virtualenv
virtualenv venv
```

## Audio Problems

### Microphone Not Working

**Check if detected:**

Linux:
```bash
arecord -l
```

Windows:
```cmd
# Right-click sound icon → Recording devices
```

**Test microphone:**

Linux:
```bash
arecord -d 5 test.wav
aplay test.wav
```

**Common fixes:**

1. **Wrong default device** - Set default in system settings
2. **Permissions** (Linux):
   ```bash
   sudo usermod -a -G audio $USER
   # Log out and back in
   ```
3. **Driver issues** - Update audio drivers

### "ALSA lib" Errors (Linux)

**Error:** Multiple ALSA warnings in output

**These are usually harmless.** To suppress:

```bash
# Create ALSA config
cat > ~/.asoundrc << 'EOF'
pcm.!default {
    type pulse
}
ctl.!default {
    type pulse
}
EOF
```

### No Sound Output

**Check:**
1. Volume not muted
2. Correct output device selected
3. TTS engine initialized

**Test TTS separately:**
```python
import pyttsx3
engine = pyttsx3.init()
engine.say("Test")
engine.runAndWait()
```

### "Audio device not found"

**Linux:**
```bash
# Restart PulseAudio
pulseaudio -k
pulseaudio --start

# Or use ALSA directly
# Edit config/envy.yaml to use different audio backend
```

## Model Issues

### "VOSK model not found"

**Error:** `FileNotFoundError: VOSK model not found at models/vosk-model-small-en-us-0.15`

**Solution:**
```bash
./scripts/download_models.sh
```

Or manually:
1. Download: https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
2. Extract to `models/` directory

### Whisper Model Download Fails

**Error:** Whisper download timeout or fails

**Solution:**

Models are auto-downloaded on first use. If fails:

```python
# Pre-download in Python
from faster_whisper import WhisperModel
model = WhisperModel("base", download_root="models/")
```

Or download manually from Hugging Face:
- https://huggingface.co/guillaumekln/faster-whisper-base

### LLM Model Not Found

**Error:** `Local model not found`

**Options:**

1. **Download model:**
   ```bash
   # Using huggingface-cli
   pip install huggingface-hub
   huggingface-cli download TheBloke/Llama-2-7B-Chat-GGUF llama-2-7b-chat.Q4_0.gguf --local-dir models/
   ```

2. **Use remote fallback:**
   ```yaml
   # config/envy.yaml
   llm:
     primary: "remote"
     remote:
       enabled: true
   ```

3. **Use different model:**
   Update path in config to point to your GGUF model

### Model Too Large for RAM/VRAM

**Error:** Out of memory when loading model

**Solutions:**

1. **Use smaller model:**
   ```yaml
   stt:
     model_size: "tiny"  # Instead of base/small
   ```

2. **Reduce context size:**
   ```yaml
   llm:
     local:
       context_size: 1024  # Instead of 2048
       gpu_layers: 15      # Reduce layers
   ```

3. **Use CPU-only:**
   ```yaml
   resources:
     gpu_enabled: false
   ```

## Performance Issues

### High CPU Usage

**Check usage:**
```bash
top
# or
htop
```

**Solutions:**

1. **Reduce profile:**
   ```yaml
   system:
     profile: "low"
   ```

2. **Limit CPU:**
   ```yaml
   resources:
     max_cpu_percent: 30
   ```

3. **Reduce threads:**
   ```yaml
   llm:
     local:
       threads: 2
   ```

### High Memory Usage

**Check:**
```bash
free -h
```

**Solutions:**

1. **Reduce context:**
   ```yaml
   llm:
     local:
       context_size: 512
   ```

2. **Use smaller models:**
   ```yaml
   stt:
     model_size: "tiny"
   ```

### Slow Response Time

**Normal latencies:**
- Wake word: ~100-200ms
- STT: ~1-3s
- LLM: 2-10s
- TTS: ~0.5-1s
- Total: 4-15s

**If slower:**

1. **Enable GPU:**
   ```yaml
   resources:
     gpu_enabled: true
   llm:
     local:
       gpu_layers: 20
   ```

2. **Use power profile:**
   ```yaml
   system:
     profile: "power"
   ```

3. **Reduce quality for speed:**
   ```yaml
   stt:
     model_size: "tiny"
     compute_type: "int8"
   ```

### System Becomes Unresponsive

**Cause:** Envy using too many resources

**Immediate fix:**
```bash
# Kill Envy
pkill -f main.py
```

**Permanent fix:**
```yaml
resources:
  max_cpu_percent: 40
  max_memory_mb: 2048

system:
  profile: "low"
```

## GPU Issues

### GPU Not Detected

**Check GPU:**

Linux:
```bash
nvidia-smi
lspci | grep -i nvidia
```

Windows:
```cmd
nvidia-smi
```

**If not working:**

1. **Install NVIDIA drivers**
2. **Install CUDA Toolkit**
3. **Reinstall llama-cpp-python with CUDA:**

   ```bash
   pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121
   ```

### "CUDA out of memory"

**Error:** Model too large for GPU

**Solutions:**

1. **Reduce GPU layers:**
   ```yaml
   llm:
     local:
       gpu_layers: 10  # Reduce from 20
   ```

2. **Reduce memory fraction:**
   ```yaml
   resources:
     gpu_memory_fraction: 0.5
   ```

3. **Use CPU for LLM:**
   ```yaml
   llm:
     local:
       gpu_layers: 0
   ```

### GPU Not Being Used

**Check config:**
```yaml
resources:
  gpu_enabled: true

llm:
  local:
    gpu_layers: 20  # Must be > 0
```

**Verify CUDA installation:**
```bash
nvcc --version
```

## Service Issues

### Service Won't Start

**Linux:**
```bash
# Check status
sudo systemctl status envy

# View logs
sudo journalctl -u envy -n 50

# Check for errors
sudo journalctl -u envy | grep ERROR
```

**Windows:**
```cmd
# Check service
sc query Envy

# View Event Viewer logs
eventvwr
```

**Common causes:**
1. Python virtual environment not activated in service
2. Incorrect paths in service file
3. Missing dependencies
4. Permission issues

### Permission Denied

**Error:** Permission denied accessing audio/files

**Linux:**
```bash
# Add to audio group
sudo usermod -a -G audio $USER

# Fix file permissions
chmod 755 run_envy_local.sh
chmod 644 config/envy.yaml
```

### Port Already in Use

**Error:** `Address already in use: 8080`

**Find what's using port:**

Linux:
```bash
sudo lsof -i :8080
```

Windows:
```cmd
netstat -ano | findstr :8080
```

**Solution:**

1. **Change port:**
   ```yaml
   web:
     port: 8081
   ```

2. **Kill process using port**

3. **Disable dashboard:**
   ```bash
   python main.py --no-gui
   ```

## General Debugging

### Enable Debug Logging

```yaml
# config/envy.yaml
logging:
  level: "DEBUG"
  console: true
```

### Check Logs

```bash
# View all logs
cat artifacts/logs/envy.log

# Watch live
tail -f artifacts/logs/envy.log

# Search for errors
grep ERROR artifacts/logs/envy.log

# View last 50 lines
tail -50 artifacts/logs/envy.log
```

### Test Individual Components

**Test wake word:**
```python
from services.wake_listener import WakeListener
listener = WakeListener(lambda: print("Wake!"))
listener.load_model()
print("Model loaded successfully")
```

**Test STT:**
```python
from services.stt_service import STTService
stt = STTService()
stt.load_model()
print("STT ready")
```

**Test TTS:**
```python
from services.tts_service import TTSService
tts = TTSService()
tts.speak("Test")
```

**Test LLM:**
```python
from services.llm_adapter import LLMAdapter
llm = LLMAdapter()
response, source = llm.generate("Hello")
print(f"Response from {source}: {response}")
```

### Run Tests

```bash
./tests/run_tests.sh
```

Check results in `artifacts/tests/acceptance_results.json`

### Clean Restart

```bash
# Stop Envy
pkill -f main.py

# Clear logs
rm artifacts/logs/*.log

# Clear test artifacts
rm -rf artifacts/tests/*

# Restart
./run_envy_local.sh
```

### Reinstall Dependencies

```bash
# Activate venv
source venv/bin/activate

# Reinstall
pip install --force-reinstall -r requirements.txt
```

### Reset Configuration

```bash
# Backup current config
cp config/envy.yaml config/envy.yaml.backup

# Use default config (if you have a template)
# Or manually edit config/envy.yaml
```

## Still Need Help?

1. **Check logs:** `artifacts/logs/envy.log`
2. **Run tests:** `./tests/run_tests.sh`
3. **Generate performance report:** `./artifacts/perf-report-gen.sh`
4. **Search issues:** Look for similar problems in GitHub issues
5. **Create issue:** Include:
   - OS and version
   - Hardware specs
   - Python version
   - Error logs
   - Steps to reproduce

## Emergency Recovery

If Envy is completely broken:

```bash
# 1. Stop everything
pkill -f main.py
sudo systemctl stop envy

# 2. Backup important data
cp -r artifacts/ artifacts.backup/

# 3. Clean install
rm -rf venv/
./install_envy.sh

# 4. Restore config
cp config/envy.yaml.backup config/envy.yaml

# 5. Test
./tests/run_tests.sh
```

---

**Most issues can be resolved by checking logs and adjusting configuration. Don't hesitate to lower resource usage if system becomes unstable.**
