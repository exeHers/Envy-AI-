from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "envy.yaml"


def _deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge overlay into base without mutating inputs."""
    result: Dict[str, Any] = {}
    for key in base.keys() | overlay.keys():
        if key in base and key in overlay:
            if isinstance(base[key], dict) and isinstance(overlay[key], dict):
                result[key] = _deep_merge(base[key], overlay[key])
            else:
                result[key] = overlay[key]
        elif key in overlay:
            result[key] = overlay[key]
        else:
            result[key] = base[key]
    return result


def _flatten_env(prefix: str = "ENVY_") -> Dict[str, str]:
    """Extract environment variables beginning with prefix."""
    return {
        key[len(prefix) :].lower(): value
        for key, value in os.environ.items()
        if key.startswith(prefix)
    }


@dataclass
class EnvyConfig:
    """Convenience accessor for loaded configuration."""

    data: Dict[str, Any]
    profile: str
    path: Path = field(default=DEFAULT_CONFIG_PATH)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def get(self, dotted_path: str, default: Any = None) -> Any:
        parts = dotted_path.split(".")
        cursor: Any = self.data
        for part in parts:
            if isinstance(cursor, dict) and part in cursor:
                cursor = cursor[part]
            else:
                return default
        return cursor

    def with_profile_override(self, profile: Optional[str]) -> "EnvyConfig":
        if not profile or profile == self.profile:
            return self
        merged = apply_profile(self.raw_data or self.data, profile)
        return EnvyConfig(data=merged, profile=profile, path=self.path, raw_data=self.raw_data or self.data)

    @property
    def runtime_dirs(self) -> Dict[str, Path]:
        root = PROJECT_ROOT
        return {
            key: (root / value).resolve()
            for key, value in self.data.get("runtime", {}).items()
            if key.endswith("_dir")
        }

    def ensure_runtime_dirs(self) -> None:
        runtime = self.data.get("runtime", {})
        if not runtime.get("ensure_directories", False):
            return
        for _, p in self.runtime_dirs.items():
            p.mkdir(parents=True, exist_ok=True)


def apply_profile(raw_data: Dict[str, Any], profile: Optional[str]) -> Dict[str, Any]:
    data = dict(raw_data)
    profiles = data.get("profiles", {})
    default_profile = data.get("runtime", {}).get("default_profile")
    selected = profile or default_profile
    if selected and selected in profiles:
        data = _deep_merge(data, {"__profile": selected})
        data = _deep_merge(data, profiles[selected])
    data.pop("profiles", None)
    return data


def load_config(path: Optional[Path] = None, profile: Optional[str] = None) -> EnvyConfig:
    config_path = Path(path or DEFAULT_CONFIG_PATH)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        raw_data = yaml.safe_load(handle)

    env_overrides = _flatten_env()
    if env_overrides:
        raw_data = _deep_merge(raw_data, {"env": env_overrides})

    merged = apply_profile(raw_data, profile)
    config = EnvyConfig(
        data=merged,
        profile=profile or merged.get("__profile") or raw_data.get("runtime", {}).get("default_profile", "balanced"),
        path=config_path,
        raw_data=raw_data,
    )
    config.ensure_runtime_dirs()
    return config


__all__ = ["load_config", "EnvyConfig", "PROJECT_ROOT", "DEFAULT_CONFIG_PATH"]
