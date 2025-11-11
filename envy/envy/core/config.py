from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigError(Exception):
    """Raised when configuration loading fails."""


def _default_config_path() -> Path:
    repo_root = Path(__file__).resolve().parent.parent.parent
    return repo_root / "config" / "envy.yaml"


def load_config(profile: str = "balanced", config_path: Path | None = None) -> Dict[str, Any]:
    """
    Load the Envy configuration and return a dictionary filtered to the selected profile.

    Args:
        profile: The resource profile to load ("low", "balanced", "power").
        config_path: Optional explicit path to the YAML configuration file.

    Returns:
        A dictionary with the merged configuration for the chosen profile.
    """
    cfg_path = Path(config_path) if config_path else _default_config_path()
    if not cfg_path.exists():
        raise ConfigError(f"Config file not found at {cfg_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    profiles = data.get("profiles", {})
    if profile not in profiles:
        raise ConfigError(f"Profile '{profile}' not defined in {cfg_path}")

    merged = dict(data.get("runtime", {}))
    merged["data_paths"] = data.get("runtime", {}).get("data_paths", {})
    merged["security"] = data.get("runtime", {}).get("security", {})
    merged["confirmation"] = data.get("runtime", {}).get("confirmation", {})
    merged.update({"profile": profile})
    merged["profile_config"] = profiles[profile]
    merged["remote_endpoints"] = data.get("remote_endpoints", {})

    _apply_env_overrides(merged)
    _resolve_relative_paths(merged, cfg_path.parent)
    return merged


def _apply_env_overrides(config: Dict[str, Any]) -> None:
    """Allow environment variables to override selected settings."""
    env_prefix = "ENVY_"
    for key, value in os.environ.items():
        if not key.startswith(env_prefix):
            continue
        *path_parts, leaf = key[len(env_prefix):].lower().split("__")
        cursor = config
        for part in path_parts:
            cursor = cursor.setdefault(part, {})
        cursor[leaf] = _interpret_env_value(value)


def _interpret_env_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "yes", "1"}:
        return True
    if lowered in {"false", "no", "0"}:
        return False
    if lowered.isdigit():
        return int(lowered)
    try:
        return float(value)
    except ValueError:
        return value


def _resolve_relative_paths(config: Dict[str, Any], base_dir: Path) -> None:
    """Resolve any path-like entries relative to the config base directory."""

    def _recurse(node: Any) -> Any:
        if isinstance(node, dict):
            return {k: _recurse(v) for k, v in node.items()}
        if isinstance(node, list):
            return [_recurse(v) for v in node]
        if isinstance(node, str) and node.startswith("models/"):
            return str((base_dir.parent / node).resolve())
        return node

    profile_cfg = config.get("profile_config", {})
    config["profile_config"] = _recurse(profile_cfg)
