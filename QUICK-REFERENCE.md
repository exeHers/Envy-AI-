# ENVY - QUICK REFERENCE CARD

## 📍 What You Have

Location: `/workspace/`

```
/workspace/
├── envy/                          ← Source code repository
├── envy-ready.zip                 ← Final package (67KB)
├── cursor-build-log.txt           ← Complete build log
├── ENVY-DEPLOYMENT-GUIDE.md       ← Deployment instructions
├── FINAL-DELIVERY-CHECKLIST.md    ← Acceptance verification
└── QUICK-REFERENCE.md             ← This file
```

## 🚀 Quick Start (5 Minutes)

### 1. Extract
```bash
unzip envy-ready.zip
cd envy/
```

### 2. Install
```bash
./install_envy.sh
```

### 3. Download Models
```bash
./scripts/download_models.sh
```

### 4. Run
```bash
./run_envy_local.sh
```

### 5. Activate
Say **"Envy"** out loud!

Dashboard: http://localhost:8080

## 📝 Key Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview & features |
| `install_envy.sh` | Automated installer |
| `run_envy_local.sh` | Start Envy |
| `config/envy.yaml` | All settings |
| `docs/install-linux.md` | Detailed Linux guide |
| `docs/security.md` | Security features |
| `docs/troubleshooting.md` | Problem solving |
| `tests/run_tests.sh` | Run acceptance tests |

## 🎯 Voice Commands

| Say This | Envy Does This |
|----------|----------------|
| "Envy, create test.py that prints hello" | Creates Python file |
| "Envy, research quantum computing" | Generates research summary |
| "Envy, remind me to stretch in 10 minutes" | Sets reminder |

## ⚙️ Configuration

File: `config/envy.yaml`

### Change Performance Profile
```yaml
system:
  profile: "balanced"  # low, balanced, or power
```

### Enable Remote LLM Fallback
```yaml
llm:
  remote:
    enabled: true
```

### Adjust Resource Limits
```yaml
resources:
  max_cpu_percent: 50
  max_memory_mb: 4096
```

## 🔧 Common Commands

| Task | Command |
|------|---------|
| Install | `./install_envy.sh` |
| Run | `./run_envy_local.sh` |
| Run headless | `./run_envy_local.sh --no-gui` |
| Run tests | `./tests/run_tests.sh` |
| Check logs | `tail -f artifacts/logs/envy.log` |
| Download models | `./scripts/download_models.sh` |
| Performance report | `./artifacts/perf-report-gen.sh` |

## 🐛 Troubleshooting

### Models Not Found
```bash
./scripts/download_models.sh
```

### High CPU Usage
Edit `config/envy.yaml`:
```yaml
system:
  profile: "low"
```

### Microphone Issues
```bash
arecord -l                    # List devices
arecord -d 5 test.wav         # Test recording
aplay test.wav                # Test playback
```

### View Logs
```bash
cat artifacts/logs/envy.log
```

## 📊 System Requirements

| Component | Requirement |
|-----------|-------------|
| CPU | Intel i3+ (4+ cores) |
| RAM | 16GB (min 8GB) |
| GPU | NVIDIA GTX 1070 (8GB) - optional |
| Storage | 10GB free |
| OS | Linux or Windows 10/11 |
| Python | 3.10+ |

## 🎓 Core Tech Stack

- **Wake Word**: VOSK (keyword spotting)
- **STT**: Faster-Whisper (speech recognition)
- **TTS**: pyttsx3 (speech synthesis)
- **LLM**: llama.cpp (local) + Hugging Face (fallback)
- **Web**: FastAPI + HTML/CSS/JS
- **Services**: systemd (Linux), NSSM (Windows)

## 📚 Documentation

All docs in `envy/docs/`:

1. `install-linux.md` - Linux installation
2. `install-windows.md` - Windows installation
3. `security.md` - Security features
4. `troubleshooting.md` - Problem solving
5. `custom-skills.md` - Create skills

## 🔒 Security

- ✅ Local-first (no cloud by default)
- ✅ Sandboxed execution
- ✅ Confirmations for dangerous actions
- ✅ SysControlSkill disabled by default
- ✅ Web dashboard localhost-only

## 🎁 What's Included

- ✅ 4 Skills (Code, Research, Reminder, SysControl)
- ✅ Web Dashboard with REST API
- ✅ Automated installers
- ✅ Service wrappers (24/7 operation)
- ✅ 6 acceptance tests
- ✅ 6 documentation guides
- ✅ MIT License (free & open)

## 📞 Support

1. Check logs: `artifacts/logs/envy.log`
2. Read: `docs/troubleshooting.md`
3. Run tests: `./tests/run_tests.sh`
4. Generate report: `./artifacts/perf-report-gen.sh`

## 🎯 Acceptance Tests

Run all tests:
```bash
./tests/run_tests.sh
```

Individual tests:
- ✅ Wake word detection
- ✅ STT pipeline
- ✅ TTS synthesis
- ✅ LLM response
- ✅ CodeSkill (create files)
- ✅ ResearchSkill (summaries)

## 💡 Pro Tips

1. **Start Simple**: Use default "balanced" profile first
2. **GPU Optional**: Works on CPU-only systems
3. **Remote Fallback**: Enable if local LLM unavailable
4. **Custom Skills**: Easy to add (see custom-skills.md)
5. **Dashboard**: Use for testing without voice

## 🏃 Next Steps

1. ✅ Extract `envy-ready.zip`
2. ✅ Run `install_envy.sh`
3. ✅ Download models
4. ✅ Run `./run_envy_local.sh`
5. ✅ Say "Envy" to test!

## 📦 Package Info

- **Size**: 67KB compressed
- **Files**: 52 total
- **License**: MIT (Free & Open Source)
- **Platform**: Linux + Windows
- **Python**: 3.10+

## ⚡ Performance

| Metric | Value |
|--------|-------|
| Wake detection | ~100-200ms |
| Speech recognition | ~1-3s |
| LLM inference | ~2-10s |
| Speech synthesis | ~0.5-1s |
| **Total latency** | **~4-15s** |

---

**Ready to deploy!** Extract, install, and say "Envy" to start.

Built with ❤️ by Cursor AI • MIT License
