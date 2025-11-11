from __future__ import annotations

import pathlib
from functools import lru_cache
from typing import Any, Dict

import yaml


CONFIG_PATH = pathlib.Path(__file__).resolve().parents[1] / "config" / "envy.yaml"


class ConfigError(RuntimeError):
    """Raised when configuration loading fails."""


@lru_cache(maxsize=1)
def load_config(path: pathlib.Path | None = None) -> Dict[str, Any]:
    """
    Load configuration from envy.yaml and memoize the result.

    Parameters
    ----------
    path:
        Optional override for the config path.
    """
    target = path or CONFIG_PATH
    if not target.exists():
        raise ConfigError(f"Configuration file not found: {target}")
    with target.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ConfigError("Configuration root must be a mapping")
    return config


def resolve_profile(config: Dict[str, Any], profile_name: str | None = None) -> Dict[str, Any]:
    profiles = config.get("profiles", {})
    options = profiles.get("options", {})
    default = profiles.get("default")

    selected = profile_name or config.get("runtime", {}).get("profile") or default
    if selected not in options:
        raise ConfigError(f"Profile '{selected}' not defined in config")
    merged = {**config, **options[selected]}
    merged["resolved_profile"] = selected
    return merged
