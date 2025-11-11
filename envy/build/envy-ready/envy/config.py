"""Configuration loader for Envy assistant."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "envy.yaml"


@dataclass
class ProfileConfig:
    """Runtime profile settings controlling resource usage."""

    name: str
    description: str
    max_cpu_percent: int
    allow_gpu: bool
    stt_model: str
    llm_model: Optional[str]
    tts_voice: str


@dataclass
class WakeConfig:
    model_path: str
    sensitivity: float
    sample_rate: int
    chunk_size: int


@dataclass
class SafetyConfig:
    destructive_requires_voice: bool
    destructive_requires_dashboard: bool
    sandbox_paths: List[str]
    command_whitelist: List[str]
    confirmation_timeout: int


@dataclass
class ServiceConfig:
    host: str
    port: int
    enabled: bool = True
    base_url: Optional[str] = None

    def url(self) -> str:
        if self.base_url:
            return self.base_url.rstrip("/")
        return f"http://{self.host}:{self.port}"


@dataclass
class EnvyConfig:
    """Top-level configuration object."""

    active_profile: str
    profiles: Dict[str, ProfileConfig]
    wake: WakeConfig
    services: Dict[str, ServiceConfig]
    safety: SafetyConfig
    skill_paths: List[str]
    artifacts_path: Path
    audio_demo_path: Path
    llm: Dict[str, Any] = field(default_factory=dict)

    def profile(self) -> ProfileConfig:
        return self.profiles[self.active_profile]

    def set_profile(self, profile_name: str) -> None:
        if profile_name not in self.profiles:
            raise ValueError(f"Unknown profile '{profile_name}'")
        self.active_profile = profile_name


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _build_profiles(raw_profiles: Dict[str, Dict[str, Any]]) -> Dict[str, ProfileConfig]:
    profiles: Dict[str, ProfileConfig] = {}
    for name, payload in raw_profiles.items():
        profiles[name] = ProfileConfig(
            name=name,
            description=payload.get("description", ""),
            max_cpu_percent=int(payload.get("max_cpu_percent", 80)),
            allow_gpu=bool(payload.get("allow_gpu", False)),
            stt_model=payload.get("stt_model", "vosk-small"),
            llm_model=payload.get("llm_model"),
            tts_voice=payload.get("tts_voice", "default"),
        )
    return profiles


def _build_services(raw_services: Dict[str, Dict[str, Any]]) -> Dict[str, ServiceConfig]:
    services: Dict[str, ServiceConfig] = {}
    for name, payload in raw_services.items():
        services[name] = ServiceConfig(
            host=payload.get("host", "127.0.0.1"),
            port=int(payload.get("port", 0)),
            enabled=bool(payload.get("enabled", True)),
            base_url=payload.get("base_url"),
        )
    return services


def load_config(path: Optional[Path] = None) -> EnvyConfig:
    """Load Envy configuration from YAML file."""
    config_path = Path(path) if path else CONFIG_PATH
    raw = _load_yaml(config_path)

    artifacts_root = Path(raw.get("artifacts_path", "artifacts")).resolve()
    audio_demo = Path(raw.get("audio_demo_path", "assets/audio")).resolve()

    return EnvyConfig(
        active_profile=raw.get("active_profile", "balanced"),
        profiles=_build_profiles(raw.get("profiles", {})),
        wake=WakeConfig(
            model_path=raw.get("wake", {}).get("model_path", "models/vosk-small"),
            sensitivity=float(raw.get("wake", {}).get("sensitivity", 0.4)),
            sample_rate=int(raw.get("wake", {}).get("sample_rate", 16000)),
            chunk_size=int(raw.get("wake", {}).get("chunk_size", 2048)),
        ),
        services=_build_services(raw.get("services", {})),
        safety=SafetyConfig(
            destructive_requires_voice=bool(
                raw.get("safety", {}).get("destructive_requires_voice", True)
            ),
            destructive_requires_dashboard=bool(
                raw.get("safety", {}).get("destructive_requires_dashboard", True)
            ),
            sandbox_paths=list(raw.get("safety", {}).get("sandbox_paths", ["workspace"])),
            command_whitelist=list(raw.get("safety", {}).get("command_whitelist", [])),
            confirmation_timeout=int(raw.get("safety", {}).get("confirmation_timeout", 30)),
        ),
        skill_paths=list(raw.get("skill_paths", ["skills"])),
        artifacts_path=artifacts_root,
        audio_demo_path=audio_demo,
        llm=raw.get("llm", {}),
    )


__all__ = ["EnvyConfig", "ProfileConfig", "WakeConfig", "ServiceConfig", "SafetyConfig", "load_config"]

