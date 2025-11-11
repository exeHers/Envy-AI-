 # Envy Architecture Overview

 This document sketches the high-level plan for the Envy personal assistant platform that will be implemented in this repository.

 ## System Goals

 - **Always-on wake word listener** keyed to “Envy” that keeps CPU/GPU utilisation low until activation.
 - **Streaming speech-to-text (STT) and text-to-speech (TTS)** pipelines kicked off after the wake word triggers a session.
 - **Local-first cognition** via lightweight models that run on an Intel i3 + GTX 1070 (8 GB) machine, with optional free remote fallbacks that remain disabled by default.
 - **Modular skills** in `skills/` that receive structured intents and can be safely sandboxed with explicit confirmation for destructive actions.
 - **Web dashboard** to display logs, confirm sensitive requests, review configuration, and manually trigger skills.
 - **Automated installation, testing, packaging, and service management** for Linux and Windows targets.

 ## Service Topology

 | Service | Port | Responsibility | Notes |
 |---------|------|----------------|-------|
 | `wake_listener` | 8201 | Continuous Vosk keyword spotting, notifies router when “Envy” detected | Streams from microphone or test audio fixtures |
 | `stt_service` | 8202 | Performs streaming STT on captured segments using Vosk/Whisper models | Exposes HTTP endpoint for file and real-time transcription |
 | `router` | 8203 | Session orchestration, intent classification, delegation to skills, inter-service messaging | Hosts LLM adapter + confirmation workflow |
 | `skill_manager` | 8204 | Loads skills (Code, Research, SysControl, Reminder) and executes them in workers | Enforces timeouts, sandbox policies |
 | `tts_service` | 8205 | Generates speech output (default `pyttsx3`, optional Coqui) and stores artefacts | Streams audio paths back to router |
 | `web_dashboard` | 8300 | FastAPI + HTMX front-end for monitoring, confirmations, configuration, logs, manual commands | Pulls state from router via REST |

 Internally the services communicate over REST (FastAPI + HTTP requests) with signed JWT-like tokens derived from shared secrets defined in `config/envy.yaml`.

 A lightweight message bus (`services/common/messaging.py`) provides helper clients, retry logic, and structured payloads for routing events.

 ## Execution Flow

 1. **Idle loop**: `wake_listener` streams microphone audio into a small Vosk keyword spotter. CPU/GPU limits are governed by `config/envy.yaml` profiles.
 2. **Wake detection**: when “Envy” is detected (or injected during automated tests), `wake_listener` issues `POST /session/start` to `router` with a session id and path to the recorded pre-roll buffer.
 3. **STT streaming**: `router` requests `stt_service` to transcribe the buffered segment. Partial transcripts are streamed back via Server-Sent Events (SSE) and logged to `artifacts/logs/`.
 4. **Intent resolution**: `router` applies a rules-first intent classifier. Ambiguous intents are escalated to `LLMAdapter`, which prefers local llama.cpp quantised models via `llama-cpp-python`. If unavailable, a deterministic offline responder is used, and optional free remote endpoints remain opt-in.
 5. **Skill dispatch**: Resolved intents are posted to `skill_manager`. Skills run in dedicated worker processes using a shared `BaseSkill` API and return structured results.
 6. **Security gate**: Destructive intents (filesystem writes outside `skills/`, system commands, network actions) require dual confirmation: voice (`router` asks for confirmation) and dashboard approval (`web_dashboard`).
 7. **Response synthesis**: `router` compiles textual response, triggers `tts_service` to render audio (`.wav` in `artifacts/tts/`), plays via `start-envy.sh` helpers, and pushes updates to the dashboard feed.
 8. **Session wrap**: logs, transcripts, decisions, and artefacts stored under `artifacts/sessions/<timestamp>` for audits.

 ## Configuration Profiles

 `config/envy.yaml` contains three base profiles:

 - `low`: CPU-only, reduced sampling rates, smallest Vosk model, slow polling cadence.
 - `balanced` (default): moderate CPU usage, GPU-accelerated llama.cpp if available, streaming chunk sizes tuned for responsiveness.
 - `power`: aggressive parallelism, larger STT/LLM models, faster wake listener cadence.

 Profiles cap concurrent skill executions, audio buffer lengths, and GPU VRAM reservations to keep the GTX 1070 within safe limits.

 ## Installation & Runtime Scripts

 - `install_envy.sh` / `.bat`: set up virtual environment, install dependencies, download models (Vosk small EN, quantised llama.cpp ggml), register system services (`systemd` unit or Windows NSSM wrapper), and write configuration.
 - `run_envy_local.sh`: start all microservices via a Python process manager under the selected profile, optionally headless (`--no-gui`) or with dashboard.
 - `start-envy.sh` / `.bat`: convenience wrappers consumed by services/SystemD/Windows service wrapper.
 - `packaging/create_artifacts.py`: bundles logs, models pointers, and binaries into `envy-ready.zip`.

 ## Testing Strategy

 Automated tests (executed via `pytest` + helper scripts):

 - **Wake Word Test**: feed deterministic audio fixture containing “Envy” through `wake_listener`’s file API and assert the router logs detection.
 - **STT/Skill Test**: run the CodeSkill pipeline end-to-end using fixture audio that says “Envy, create test.py that prints hello”, assert file creation and transcripts.
 - **TTS Test**: call `tts_service` to synthesise a known string, verify wave file output and log entry.
 - **LLM Fallback Test**: simulate ambiguous intent to ensure `LLMAdapter` produces a response (local rule-based fallback acceptable if local LLM missing).
 - **ResearchSkill Test**: run offline summarisation pipeline to ensure summary file + spoken response.

 Test logs are copied into `artifacts/tests/` with timestamps. `artifacts/perf-report-gen.sh` runs a scripted session while sampling CPU, memory, and GPU metrics (via `psutil` and `nvidia-smi` if available) and writes `artifacts/perf-report.txt`.

 ## Packaging

 - `envy-ready.zip` (root): includes runtime scripts, configs, fixtures, pre-downloaded lightweight models, and a `run_envy_local.sh` ready-to-execute bundle.
 - `artifacts/install-log.txt`: captured from installers.
 - `cursor-build-log.txt`: summary of acceptance criteria pass/fail with timestamps.

 ## Next Steps

 1. Implement shared configuration, logging, and messaging utilities (`services/common/`).
 2. Flesh out each microservice with FastAPI apps, including streaming endpoints.
 3. Build the skill plugins and security confirmation pipeline.
 4. Develop the dashboard UI + API.
 5. Deliver installers, service descriptors, automated tests, and packaging scripts.
