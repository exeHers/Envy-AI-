"""LLM adapter with local-first strategy and deterministic fallback."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional

import requests

from ..config import EnvyConfig

LOGGER = logging.getLogger("envy.llm")


class RuleBasedResponder:
    """Simple deterministic responses used when no LLM is available."""

    def respond(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "create test.py" in prompt_lower:
            return "I will create test.py with the requested content."
        if "research" in prompt_lower:
            return "Here is a short research summary based on offline knowledge."
        if "hello" in prompt_lower:
            return "Hello! Envy at your service."
        return "Unable to reach an LLM. Providing safe fallback response."


class LLMAdapter:
    """Adapter that prioritizes local llama.cpp models with optional remote fallback."""

    def __init__(self, config: EnvyConfig):
        self.config = config
        self._local_model = self._init_local_model()
        self._rule_based = RuleBasedResponder()

    def _init_local_model(self):
        local_cfg: Dict[str, Optional[str]] = self.config.llm.get("local", {})
        if not local_cfg or not local_cfg.get("enabled", False):
            LOGGER.info("Local LLM disabled in config.")
            return None

        model_path = Path(local_cfg.get("model_path", ""))
        if not model_path.exists():
            LOGGER.warning("Local LLM model path not found: %s", model_path)
            return None

        try:
            from llama_cpp import Llama  # type: ignore

            LOGGER.info("Loading local LLM from %s", model_path)
            return Llama(
                model_path=str(model_path),
                n_ctx=int(local_cfg.get("context_size", 2048)),
                n_gpu_layers=int(local_cfg.get("gpu_layers", 20)),
                seed=local_cfg.get("seed", 42),
            )
        except ImportError:
            LOGGER.warning("llama_cpp_python not installed; skipping local LLM.")
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.error("Failed to initialize local LLM: %s", exc)
        return None

    def _call_local(self, prompt: str) -> Optional[str]:
        if not self._local_model:
            return None
        try:
            result = self._local_model(
                prompt,
                max_tokens=256,
                stop=["User:"],
                temperature=0.7,
            )
            if isinstance(result, dict):
                return result.get("choices", [{}])[0].get("text", "").strip()
            return str(result)
        except Exception as exc:  # pragma: no cover - runtime guard
            LOGGER.error("Local LLM generation failed: %s", exc)
            return None

    def _call_remote(self, prompt: str) -> Optional[str]:
        remote_cfg: Dict[str, Optional[str]] = self.config.llm.get("remote", {})
        if not remote_cfg or not remote_cfg.get("enabled", False):
            return None
        endpoint = remote_cfg.get("endpoint")
        if not endpoint:
            return None
        headers = {"Content-Type": "application/json"}
        if remote_cfg.get("auth_token"):
            headers["Authorization"] = f"Bearer {remote_cfg['auth_token']}"
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 256}}
        try:
            response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=30)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and data:
                    return data[0].get("generated_text", "").strip()
                if isinstance(data, dict):
                    return data.get("generated_text", "").strip()
            LOGGER.warning("Remote LLM request failed: %s %s", response.status_code, response.text)
        except requests.RequestException as exc:
            LOGGER.error("Remote LLM request error: %s", exc)
        return None

    def generate(self, prompt: str) -> str:
        for generator in (self._call_local, self._call_remote):
            result = generator(prompt)
            if result:
                return result
        return self._rule_based.respond(prompt)

