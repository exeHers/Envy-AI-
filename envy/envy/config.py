from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigError(RuntimeError):
    """Raised when the configuration cannot be loaded."""


def _resolve_env(value: Any, context: Dict[str, Any]) -> Any:
    if isinstance(value, str):
        resolved = value
        while "${" in resolved:
            start = resolved.index("${")
            end = resolved.index("}", start)
            key = resolved[start + 2 : end]
            replacement = context
            for part in key.split("."):
                replacement = replacement.get(part)
                if replacement is None:
                    break
            if replacement is None:
                replacement = os.environ.get(key.split(".")[-1], "")
            resolved = resolved[:start] + str(replacement) + resolved[end + 1 :]
        return resolved
    if isinstance(value, dict):
        return {k: _resolve_env(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(item, context) for item in value]
    return value


@dataclass
class Config:
    data: Dict[str, Any]
    profile: str

    def get(self, path: str, default: Any = None) -> Any:
        node: Any = self.data
        for part in path.split("."):
            if not isinstance(node, dict):
                return default
            node = node.get(part)
            if node is None:
                return default
        return node

    @property
    def paths(self) -> Dict[str, Any]:
        return self.data.get("paths", {})


def load_config(profile: str = "balanced", overrides: Optional[Dict[str, Any]] = None) -> Config:
    config_path = Path(__file__).resolve().parent.parent / "config" / "envy.yaml"
    if not config_path.exists():
        raise ConfigError(f"Config file missing: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        raw_config: Dict[str, Any] = yaml.safe_load(handle)

    profiles = raw_config.get("profiles", {})
    if profile not in profiles:
        raise ConfigError(f"Unknown profile '{profile}'. Available: {', '.join(profiles)}")

    # Merge base config with profile overrides.
    config = dict(raw_config)
    profile_settings = profiles.get(profile, {})

    def merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                base[key] = merge(dict(base[key]), value)
            else:
                base[key] = value
        return base

    config = merge(config, {"profile": profile})
    config = merge(config, profile_settings)

    if overrides:
        config = merge(config, overrides)

    resolved = _resolve_env(config, config)
    return Config(data=resolved, profile=profile)
