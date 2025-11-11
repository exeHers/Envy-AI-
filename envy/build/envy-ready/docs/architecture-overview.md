## Envy Architecture Overview

### Core Goals
- 24/7 Jarvis-style assistant with wake-word activation, streaming speech pipeline, modular skills, and safety controls.
- Runs on modest local hardware (Intel i3 + GTX 1070 + 16 GB RAM) without paid APIs.
- Ships with installers, automation scripts, and verification tests that exercise the full voice-to-action loop.

### Services & Responsibilities
- **Wake Listener (`envy.services.wake_listener`)**  
  Continuously monitors microphone (or demo audio feed) with Vosk keyword spotting. Emits wake events to the router via HTTP. Keeps CPU use low by pausing downstream services until the wake word “Envy” is detected.

- **STT Service (`envy.services.stt_service`)**  
  Performs streaming transcription using Vosk (primary) with optional Whisper/WhisperX integration. Accepts audio chunks over HTTP and streams partial transcripts back to the router.

- **Router (`envy.services.router_service`)**  
  Orchestrates sessions after wake detection. Buffers transcripts, requests intent classification, dispatches skills, and supervises confirmation flows. Persists structured logs to `artifacts/logs/`.

- **Skill Manager (`envy.services.skill_manager`)**  
  Discovers Python modules under `skills/`, enforces execution sandbox (whitelist-based for destructive commands), and executes skills in worker subprocesses with timeouts. Ships with CodeSkill, ResearchSkill, SysControlSkill, and ReminderSkill.

- **LLM Adapter (`envy.core.llm_adapter`)**  
  Provides pluggable access to local llama.cpp/ggml/ONNX models. Falls back to a deterministic, rule-based responder when no models are configured. Optional remote endpoints (free only) are opt-in via config.

- **TTS Service (`envy.services.tts_service`)**  
  Streams synthesized speech via `pyttsx3` by default. Supports optional Coqui TTS subprocess. Saves WAV artifacts to `artifacts/audio/` and provides status updates to router and dashboard.

- **Web Dashboard (`envy.services.web_dashboard`)**  
  FastAPI + HTMX frontend for live logs, confirmations, configuration toggles, file explorer, and manual commands. Integrates with router via REST.

### Inter-Service Communication
- All services expose FastAPI HTTP endpoints with JSON payloads.
- Router communicates with STT, Skill Manager, TTS, and Dashboard via REST.
- Wake listener posts wake events to router; Router notifies dashboard using Server-Sent Events (SSE).

### Configuration
- Central YAML configuration at `config/envy.yaml` with profiles (`low`, `balanced`, `power`) controlling model choices, concurrency limits, and GPU usage.
- Optional secrets stored in `config/secrets.example.yaml`; not required for core functionality.

### Safety Controls
- Destructive actions (file writes outside sandbox, system commands) require:  
  1. Voice confirmation phrase (e.g., “Yes, proceed”).  
  2. Dashboard confirmation click.  
  3. Router enforces final execution through whitelisted commands.

### Testing & Automation
- `install_envy.sh` / `install_envy.bat` set up Python virtualenv, download models (Vosk small, TinyLlama Q4 optional), and register services (systemd / Windows service wrapper).
- Automated tests under `tests/` simulate wake word detection, STT pipeline, TTS playback, and CodeSkill + ResearchSkill flows using bundled demo audio.
- `artifacts/tests/` stores test logs; `artifacts/perf-report.txt` generated via `scripts/perf-report-gen.sh`.
- `envy-ready.zip` packaging script bundles runtime scripts, configs, and pre-downloaded or auto-fetch models.

### Parallel Build Strategy
- Cursor agents cooperate through git repo:
  1. **Core Services Agent:** Implements Python services and core pipeline.
  2. **Dashboard Agent:** Builds web dashboard frontend/back-end templates.
  3. **Installer/Packaging Agent:** Crafts install scripts, systemd/Windows service wrappers, model downloads.
  4. **QA Agent:** Authors automated tests, demo audio prep, verification scripts, and perf reporting.

### Resource Targets
- Default `balanced` profile: CPU usage <60% on 2 cores, GPU memory <5 GB.  
- Wake listener idle CPU <5%.  
- Audio latency target: <2 s wake → transcript, <3 s to first TTS output.

