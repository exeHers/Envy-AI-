"""
Configuration loading and profile management for Envy.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "envy.yaml"


@dataclass
class ProfileLimits:
    """Resource limits controlling CPU/GPU usage."""

    name: str
    max_cpu_percent: int
    max_gpu_memory_gb: float
    wake_sensitivity: float
    stt_backend: str
    llm_backend: str


@dataclass
class AudioConfig:
    wake_model_path: str
    stt_model_path: str
    sample_rate: int = 16000
    chunk_size: int = 2048
    device: Optional[str] = None
    enable_streaming: bool = True


@dataclass
class LLMConfig:
    default_backend: str
    local_model_path: str
    remote_endpoint: Optional[str] = None
    remote_api_key_env: Optional[str] = None
    persona: str = "neutral"
    temperature: float = 0.5
    max_tokens: int = 512


@dataclass
class SkillConfig:
    whitelist: Dict[str, bool] = field(default_factory=dict)
    requires_confirmation: Dict[str, bool] = field(default_factory=dict)


@dataclass
class SecurityConfig:
    destructive_confirmation: bool = True
    dashboard_double_confirm: bool = True
    command_whitelist: Dict[str, bool] = field(default_factory=dict)


@dataclass
class DashboardConfig:
    host: str = "0.0.0.0"
    port: int = 8190
    enable_https: bool = False
    auth_token_env: Optional[str] = None


@dataclass
class EnvyConfig:
    profile: ProfileLimits
    audio: AudioConfig
    llm: LLMConfig
    skills: SkillConfig
    security: SecurityConfig
    dashboard: DashboardConfig
    data_dir: Path
    artifacts_dir: Path
    custom_skills_dir: Path

    @property
    def wake_word(self) -> str:
        return "envy"


PROFILES: Dict[str, ProfileLimits] = {
    "low": ProfileLimits(
        name="low",
        max_cpu_percent=50,
        max_gpu_memory_gb=2.0,
        wake_sensitivity=0.6,
        stt_backend="vosk",
        llm_backend="rule",
    ),
    "balanced": ProfileLimits(
        name="balanced",
        max_cpu_percent=70,
        max_gpu_memory_gb=4.0,
        wake_sensitivity=0.5,
        stt_backend="vosk",
        llm_backend="llama_cpp",
    ),
    "power": ProfileLimits(
        name="power",
        max_cpu_percent=85,
        max_gpu_memory_gb=6.0,
        wake_sensitivity=0.4,
        stt_backend="vosk",
        llm_backend="llama_cpp",
    ),
}


def _resolve_profile(name: str) -> ProfileLimits:
    if name not in PROFILES:
        raise ValueError(f"Unknown profile '{name}'. Available: {', '.join(PROFILES)}")
    return PROFILES[name]


def load_config(path: Optional[os.PathLike[str] | str] = None, profile: Optional[str] = None) -> EnvyConfig:
    """Load configuration from YAML and merge with defaults."""
    yaml_path = Path(path or DEFAULT_CONFIG_PATH)
    with yaml_path.open("r", encoding="utf-8") as handle:
        data: Dict[str, Any] = yaml.safe_load(handle) or {}

    chosen_profile = profile or data.get("profile", "balanced")
    profile_config = _resolve_profile(chosen_profile)

    audio_data = data.get("audio", {})
    llm_data = data.get("llm", {})
    skill_data = data.get("skills", {})
    security_data = data.get("security", {})
    dashboard_data = data.get("dashboard", {})

    data_dir = Path(data.get("data_dir", "data")).resolve()
    artifacts_dir = Path(data.get("artifacts_dir", "artifacts")).resolve()
    skills_dir = Path(data.get("skills_dir", "skills")).resolve()

    return EnvyConfig(
        profile=profile_config,
        audio=AudioConfig(
            wake_model_path=str(audio_data.get("wake_model_path", "models/vosk-wake")),
            stt_model_path=str(audio_data.get("stt_model_path", "models/vosk-stt")),
            sample_rate=int(audio_data.get("sample_rate", 16000)),
            chunk_size=int(audio_data.get("chunk_size", 2048)),
            device=audio_data.get("device"),
            enable_streaming=bool(audio_data.get("enable_streaming", True)),
        ),
        llm=LLMConfig(
            default_backend=llm_data.get("default_backend", profile_config.llm_backend),
            local_model_path=str(llm_data.get("local_model_path", "models/ggml-envy-q4_0.gguf")),
            remote_endpoint=llm_data.get("remote_endpoint"),
            remote_api_key_env=llm_data.get("remote_api_key_env"),
            persona=llm_data.get("persona", "neutral"),
            temperature=float(llm_data.get("temperature", 0.5)),
            max_tokens=int(llm_data.get("max_tokens", 512)),
        ),
        skills=SkillConfig(
            whitelist=skill_data.get("whitelist", {}),
            requires_confirmation=skill_data.get("requires_confirmation", {}),
        ),
        security=SecurityConfig(
            destructive_confirmation=bool(security_data.get("destructive_confirmation", True)),
            dashboard_double_confirm=bool(security_data.get("dashboard_double_confirm", True)),
            command_whitelist=security_data.get("command_whitelist", {}),
        ),
        dashboard=DashboardConfig(
            host=dashboard_data.get("host", "0.0.0.0"),
            port=int(dashboard_data.get("port", 8190)),
            enable_https=bool(dashboard_data.get("enable_https", False)),
            auth_token_env=dashboard_data.get("auth_token_env"),
        ),
        data_dir=data_dir,
        artifacts_dir=artifacts_dir,
        custom_skills_dir=skills_dir,
    )
