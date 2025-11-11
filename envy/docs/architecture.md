## Envy Architecture Overview

Envy is a modular, microservice-oriented personal assistant designed to run fully on local hardware without requiring paid APIs. The system is organized into lightweight Python services that communicate over HTTP (FastAPI) and an asynchronous event bus. Each service can run independently during development or be orchestrated by the launcher scripts for production deployments.

### Core Services

- **Wake Listener (`wake_listener`)**  
  Continuously monitors microphone audio using the Vosk keyword recognizer. It keeps CPU usage low by running with lightweight models and only notifying downstream services when the wake word “Envy” is detected. For automated tests and headless demos, it can consume prerecorded WAV files.

- **Speech-to-Text (`stt_service`)**  
  Captures the utterance after wake detection and performs streaming transcription. It defaults to Vosk small English models and can optionally leverage Whisper.cpp or WhisperX when the hardware profile permits. Partial transcripts are streamed to the router.

- **Router (`router`)**  
  Central coordination service that receives transcripts, performs intent detection, and dispatches actions to skills. It uses a tiered approach: rules-based classifiers for known intents and an LLM adapter fallback for open-ended requests. The router also enforces confirmation workflows for sensitive operations.

- **Skill Manager (`skill_manager`)**  
  Dynamically loads drop-in Python skill modules from `skills/`. Each skill runs in a sandboxed worker process with resource limits and timeout controls. The initial reference skills include:
  - `CodeSkill`: File creation and editing with confirmation flow.
  - `ResearchSkill`: Web research using optional HTTP requests, summarizing results locally.
  - `SysControlSkill`: Controlled system command execution with whitelisting.
  - `ReminderSkill`: Local reminder scheduling with persistence.

- **LLM Adapter (`llm_adapter`)**  
  Abstracts language-model access. The default profile uses a local rule-based stub to keep the system fully offline. Optional profiles load quantized GGUF models via `llama.cpp` or call free remote endpoints (disabled by default). Configuration lives in `config/envy.yaml`.

- **Text-to-Speech (`tts_service`)**  
  Streams responses using `pyttsx3` for low-latency playback and can optionally invoke higher-quality engines like Coqui TTS. Audio is written to temporary WAV files for playback and auditing.

- **Web Dashboard (`dashboard`)**  
  FastAPI + HTMX/Alpine.js front-end providing real-time logs, configuration editing, confirmation dialogs, and manual command triggers. It exposes a REST API for service status and artifact browsing.

### Supporting Components

- **Event Bus**  
  A lightweight `asyncio` Pub/Sub broker persists in the router process. Services send events via HTTP endpoints; the router rebroadcasts to subscribers. This avoids external message brokers while retaining loose coupling.

- **Configuration (`config/envy.yaml`)**  
  Profiles (`low`, `balanced`, `power`) define CPU/GPU allocations, model choices, and feature toggles. Users can override values via CLI flags or environment variables.

- **Installers and Service Wrappers**  
  - `install_envy.sh` / `install_envy.bat`: Bootstrap scripts that configure Python environments, download models, and register system services.
  - `start-envy.sh` / `start-envy.bat`: Launch scripts used by users and service managers.
  - Systemd unit and Windows NSSM wrapper included in `scripts/`.

- **Artifacts and Reporting**  
  Automated tests produce logs under `artifacts/tests/`. Performance metrics (CPU, GPU, memory, latency) are gathered by `artifacts/perf-report-gen.sh` and saved to `artifacts/perf-report.txt`. Packaged releases are archived as `envy-ready.zip`.

### Data Flow Summary

1. Wake listener detects “Envy” and notifies the router.  
2. Router signals the STT service to capture and transcribe the utterance.  
3. Router interprets the transcript, either dispatching directly to a skill or invoking the LLM adapter.  
4. Skill manager executes the requested action, returning structured results.  
5. Router formats a response and hands it to the TTS service for playback.  
6. Dashboard updates reflect each step, and relevant artifacts are stored for auditing.

### Off By Default, Opt-in Features

- Remote LLM endpoints (Hugging Face Inference, OpenRouter) are disabled by default.  
- Optional high-resource models (Whisper large, advanced TTS) require manual opt-in during installation or via the dashboard.

This architecture allows Envy to run entirely offline on modest hardware while remaining extensible and maintainable. Every component can be swapped or upgraded without touching the rest of the stack.
