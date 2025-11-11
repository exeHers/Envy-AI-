from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

LOGGER = logging.getLogger(__name__)


class ConfigError(RuntimeError):
    """Raised when configuration parsing fails."""


@dataclass(slots=True)
class RuntimeConfig:
    """Resolved configuration for the active profile."""

    raw: Dict[str, Any]
    profile_name: str
    wake: Dict[str, Any]
    stt: Dict[str, Any]
    llm: Dict[str, Any]
    tts: Dict[str, Any]
    parallel_skills: int
    gpu: Dict[str, Any]
    audio: Dict[str, Any]
    logging: Dict[str, Any]
    skills: Dict[str, Any]
    web: Dict[str, Any]
    security: Dict[str, Any]
    artifacts: Dict[str, Any]
    persona: Dict[str, Any]
    optional_remote: Dict[str, Any]
    overrides: Dict[str, Any] = field(default_factory=dict)

    def dump(self) -> Dict[str, Any]:
        data = dict(self.raw)
        data["active_profile"] = self.profile_name
        data["overrides"] = self.overrides
        return data


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        try:
            return yaml.safe_load(handle) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc


def load_runtime_config(
    config_path: Path,
    profile: str | None = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> RuntimeConfig:
    """Load configuration and resolve profile-specific overrides."""

    data = _load_yaml(config_path)
    if "profiles" not in data:
        raise ConfigError("Configuration missing 'profiles' section.")

    profile_name = profile or os.environ.get("ENVY_PROFILE", "balanced")
    profiles = data["profiles"]
    if profile_name not in profiles:
        raise ConfigError(
            f"Unknown profile '{profile_name}'. Available: {', '.join(sorted(profiles))}"
        )

    resolved_profile = profiles[profile_name] or {}
    merged: Dict[str, Any] = dict(data)
    merged.pop("profiles", None)
    merged.update(resolved_profile)

    overrides = overrides or {}
    if overrides:
        LOGGER.debug("Applying configuration overrides: %s", overrides)
        merged = _deep_merge(merged, overrides)

    return RuntimeConfig(
        raw=data,
        profile_name=profile_name,
        wake=merged.get("wake", {}),
        stt=merged.get("stt", {}),
        llm=merged.get("llm", {}),
        tts=merged.get("tts", {}),
        parallel_skills=int(merged.get("parallel_skills", 1)),
        gpu=merged.get("gpu", {}),
        audio=merged.get("audio", {}),
        logging=merged.get("logging", {}),
        skills=merged.get("skills", {}),
        web=merged.get("web", {}),
        security=merged.get("security", {}),
        artifacts=merged.get("artifacts", {}),
        persona=merged.get("persona", {}),
        optional_remote=merged.get("optional_remote", {}),
        overrides=overrides,
    )


def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    result = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
