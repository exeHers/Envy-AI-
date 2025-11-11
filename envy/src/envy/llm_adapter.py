"""
LLM adapter supporting local llama.cpp models with rule-based and remote fallbacks.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import aiohttp

from .config import EnvyConfig

_LOGGER = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from llama_cpp import Llama  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Llama = None  # type: ignore


@dataclass
class LLMResult:
    text: str
    backend: str


class LLMAdapter:
    """
    Adapter facade providing a unified interface over multiple LLM backends.
    """

    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self._llama: Optional["Llama"] = None
        self._llama_lock = asyncio.Lock()

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResult:
        persona = self._persona_prefix()
        final_prompt = f"{persona}\n{prompt}" if persona else prompt

        backend = self.config.llm.default_backend
        if backend == "llama_cpp":
            result = await self._generate_llama(final_prompt, system_prompt)
            if result:
                return result
            backend = "rule"

        if backend == "rule":
            return self._generate_rule(final_prompt)

        if backend == "remote":
            result = await self._generate_remote(final_prompt, system_prompt)
            if result:
                return result

        _LOGGER.warning("Falling back to rule-based response.")
        return self._generate_rule(final_prompt)

    def _persona_prefix(self) -> str:
        persona = self.config.llm.persona.lower()
        if persona == "sardonic":
            return "You are Envy, a concise, slightly sardonic personal assistant."
        if persona == "friendly":
            return "You are Envy, a friendly and helpful personal assistant."
        return "You are Envy, a neutral personal assistant."

    async def _generate_llama(self, prompt: str, system_prompt: Optional[str]) -> Optional[LLMResult]:
        if Llama is None:
            _LOGGER.warning("llama_cpp is not installed; skipping local LLM backend.")
            return None

        async with self._llama_lock:
            if self._llama is None:
                model_path = self.config.llm.local_model_path
                try:
                    self._llama = Llama(model_path=model_path, n_ctx=2048, n_threads=4)
                    _LOGGER.info("Initialised llama.cpp model at %s", model_path)
                except Exception as exc:  # pragma: no cover - defensive
                    _LOGGER.error("Failed to load llama.cpp model: %s", exc)
                    return None

        assert self._llama is not None

        try:
            generation = await asyncio.to_thread(
                self._llama.create_completion,
                prompt,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                stop=["User:"],
            )
            if isinstance(generation, dict):
                text = generation.get("choices", [{}])[0].get("text", "").strip()
            else:  # pragma: no cover - defensive
                text = str(generation).strip()
            if not text:
                return None
            return LLMResult(text=text, backend="llama_cpp")
        except Exception as exc:  # pragma: no cover - defensive
            _LOGGER.error("llama_cpp generation failed: %s", exc)
            return None

    async def _generate_remote(self, prompt: str, system_prompt: Optional[str]) -> Optional[LLMResult]:
        endpoint = self.config.llm.remote_endpoint
        if not endpoint:
            _LOGGER.debug("Remote LLM endpoint not configured.")
            return None

        headers = {}
        if self.config.llm.remote_api_key_env:
            api_key = asyncio.get_running_loop().run_in_executor(
                None, lambda: __import__("os").environ.get(self.config.llm.remote_api_key_env, "")
            )
            api_key = await api_key
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

        payload = {"prompt": prompt, "system": system_prompt or self._persona_prefix(), "max_tokens": 512}

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                async with session.post(endpoint, json=payload, headers=headers) as response:
                    if response.status != 200:
                        text = await response.text()
                        _LOGGER.error("Remote LLM error %s: %s", response.status, text)
                        return None
                    data = await response.json()
        except Exception as exc:  # pragma: no cover - network dependent
            _LOGGER.error("Remote LLM request failed: %s", exc)
            return None

        text = data.get("text") or data.get("choices", [{}])[0].get("text")
        if not text:
            return None
        return LLMResult(text=text.strip(), backend="remote")

    def _generate_rule(self, prompt: str) -> LLMResult:
        """
        Deterministic fallback used when no LLM backend is available.
        """
        lowered = prompt.lower()
        if "create test.py" in lowered or "prints hello" in lowered:
            response = (
                "Acknowledged. I will create a Python file named test.py that prints 'hello from envy'. "
                "Please confirm execution in the dashboard if prompted."
            )
        elif "research" in lowered:
            response = (
                "I'll gather freely available sources, summarise them to research mode output, and place the result "
                "in the artifacts directory."
            )
        else:
            response = "Envy: ready. How can I assist you?"
        return LLMResult(text=response, backend="rule")
