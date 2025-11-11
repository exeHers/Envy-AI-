from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp

from envy.config import Config

LOGGER = logging.getLogger("llm_adapter")


@dataclass
class LLMResult:
    text: str
    strategy: str
    used_remote: bool = False


class LLMAdapter:
    """Adapter that routes prompts to local or remote models based on config strategy."""

    def __init__(self, config: Config):
        self.config = config
        self.default_strategy = config.get("llm.strategies", {}).get("default", "rule")

    async def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> LLMResult:
        context = context or {}
        profile_data = self.config.get("profiles", {}).get(self.config.profile, {})
        strategy = context.get(
            "strategy",
            profile_data.get("llm", {}).get("strategy", self.default_strategy or "rule"),
        )
        if strategy == "rule":
            return self._rule_based(prompt)
        if strategy in {"local", "gpu"}:
            return await self._local_stub(prompt, strategy=strategy)
        if strategy == "remote":
            return await self._remote_call(prompt)
        LOGGER.warning("Unknown LLM strategy '%s', defaulting to rule", strategy)
        return self._rule_based(prompt)

    def _rule_based(self, prompt: str) -> LLMResult:
        templates = self.config.get("llm.strategies.rule.fallback_texts", [])
        if not templates:
            templates = [
                "Understood. I will handle that.",
                "Noted. Taking the requested action.",
                "Working on it and will report back shortly.",
            ]
        text = random.choice(templates)
        LOGGER.debug("Rule-based LLM responding with: %s", text)
        return LLMResult(text=text, strategy="rule")

    async def _local_stub(self, prompt: str, strategy: str) -> LLMResult:
        """Placeholder implementation that mimics a local LLM."""

        def synthesize() -> str:
            prompt_lower = prompt.lower()
            if "research" in prompt_lower:
                return "I'll compile a concise research summary from trusted sources."
            if "code" in prompt_lower or "create" in prompt_lower:
                return "I'll draft the requested code snippet and save it for you."
            if "remind" in prompt_lower:
                return "I'll capture that reminder and alert you at the right time."
            return f"I'm considering: {prompt.strip()[:120]}..."

        text = await asyncio.to_thread(synthesize)
        LOGGER.debug("Local stub LLM returning: %s", text)
        return LLMResult(text=text, strategy=strategy)

    async def _remote_call(self, prompt: str) -> LLMResult:
        remote_cfg = self.config.get("llm.strategies.remote", {})
        if not remote_cfg.get("enabled", False):
            LOGGER.warning("Remote LLM strategy requested but disabled; using rule fallback.")
            fallback = self._rule_based(prompt)
            fallback.strategy = "remote-disabled"
            return fallback

        endpoint = remote_cfg.get("endpoint")
        if not endpoint:
            raise RuntimeError("Remote LLM endpoint missing in configuration.")

        headers = {}
        api_key_env = remote_cfg.get("api_key_env")
        if api_key_env:
            from os import environ

            api_key = environ.get(api_key_env)
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

        payload = {"inputs": prompt}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload, headers=headers, timeout=30) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
        except Exception as exc:  # pragma: no cover - network
            LOGGER.error("Remote LLM call failed: %s", exc)
            fallback = self._rule_based(prompt)
            fallback.strategy = "remote-error"
            return fallback

        text = ""
        if isinstance(data, dict):
            text = data.get("generated_text") or data.get("text") or ""
        elif isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                text = first.get("generated_text") or first.get("text") or ""

        if not text:
            text = self._rule_based(prompt).text

        return LLMResult(text=text, strategy="remote", used_remote=True)
