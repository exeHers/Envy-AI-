# Envy - Quick Start Guide

## Installation (2 minutes)

```bash
cd envy
./installers/install_envy.sh
```

When prompted, download models to enable full functionality.

## Running Envy

```bash
./start-envy.sh
```

Or with options:
```bash
./run_envy_local.sh --profile balanced --no-gui
```

## Web Dashboard

Open: **http://127.0.0.1:8080**

## Voice Commands

1. Say **"Envy"** to wake the assistant
2. Wait for acknowledgment ("Yes?")
3. Give your command

### Example Commands

- "Envy, create a file called hello.py that prints hello world"
- "Envy, research artificial intelligence"
- "Envy, remind me to call mom tomorrow"
- "Envy, what time is it?"

## Configuration

Edit `config/envy.yaml` to customize:
- Resource profile (low/balanced/power)
- Wake word sensitivity
- Enable/disable skills
- LLM settings

## Testing

Run acceptance tests:
```bash
source venv/bin/activate
pytest tests/test_acceptance.py -v
```

## Troubleshooting

### "VOSK model not found"
```bash
./installers/download_models.sh
```

### Audio issues
```bash
python3 -c "import sounddevice; print(sounddevice.query_devices())"
```

### High CPU usage
Switch to "low" profile in `config/envy.yaml`

## Documentation

- **README.md**: Full documentation
- **docs/install-linux.md**: Linux installation details
- **docs/install-windows.md**: Windows installation details
- **docs/security.md**: Security features and configuration

## Support

Check test logs: `artifacts/tests/test_run_initial.log`  
Check system logs: `logs/envy.log`  
Performance report: `artifacts/perf-report.txt`

---

**Envy - Your local, privacy-focused personal assistant** 🤖✨
