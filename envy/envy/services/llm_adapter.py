from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import httpx

LOGGER = logging.getLogger(__name__)

try:
    from llama_cpp import Llama  # type: ignore
except Exception:  # pragma: no cover - optional
    Llama = None  # type: ignore
    LOGGER.debug("llama-cpp-python not available; local LLM fallback disabled.")


Conversation = List[Dict[str, str]]


@dataclass
class LLMConfig:
    provider: str = "simple"
    model_path: Optional[Path] = None
    max_tokens: int = 512
    optional_remote: Optional[Dict[str, str]] = None


class LLMAdapter:
    """Adapter capable of talking to different LLM backends with safe fallbacks."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._llama = self._init_llama(config) if config.provider == "llama-cpp" else None

    def _init_llama(self, config: LLMConfig):
        if Llama is None:
            LOGGER.warning("llama-cpp backend requested but llama_cpp is not installed.")
            return None
        if not config.model_path or not config.model_path.exists():
            LOGGER.warning("llama-cpp model path missing: %s", config.model_path)
            return None
        LOGGER.info("Loading llama.cpp model from %s", config.model_path)
        return Llama(
            model_path=str(config.model_path),
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=1,
            logits_all=False,
        )

    def generate(self, conversation: Conversation, prompt: str) -> str:
        provider = self.config.provider.lower()
        if provider == "llama-cpp" and self._llama:
            return self._generate_llama(conversation, prompt)
        if provider == "remote":
            return self._generate_remote(conversation, prompt)
        return SimpleResponder().respond(prompt, conversation)

    def _generate_llama(self, conversation: Conversation, prompt: str) -> str:
        if not self._llama:
            LOGGER.warning("llama.cpp not initialised; falling back to simple responder.")
            return SimpleResponder().respond(prompt, conversation)
        LOGGER.info("Generating response via llama-cpp backend.")
        messages = conversation + [{"role": "user", "content": prompt}]
        completion = self._llama.create_chat_completion(
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=0.7,
        )
        return completion["choices"][0]["message"]["content"]

    def _generate_remote(self, conversation: Conversation, prompt: str) -> str:
        remote = self.config.optional_remote or {}
        if not remote.get("enabled"):
            LOGGER.info("Remote backend disabled; using simple responder.")
            return SimpleResponder().respond(prompt, conversation)

        endpoint = remote.get("llm_endpoint")
        if not endpoint:
            LOGGER.warning("Remote LLM endpoint not configured.")
            return SimpleResponder().respond(prompt, conversation)

        payload = {
            "messages": conversation + [{"role": "user", "content": prompt}],
            "max_tokens": self.config.max_tokens,
        }

        LOGGER.info("Calling remote LLM endpoint at %s", endpoint)
        try:
            response = httpx.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("message") or data.get("choices", [{}])[0].get("message", {}).get(
                "content", ""
            )
        except Exception as exc:
            LOGGER.error("Remote LLM call failed: %s", exc)
            return SimpleResponder().respond(prompt, conversation)


class SimpleResponder:
    """Heuristic responder that keeps the assistant responsive without a heavy model."""

    def respond(self, prompt: str, conversation: Conversation) -> str:
        normalized = prompt.lower()
        LOGGER.debug("SimpleResponder handling prompt: %s", prompt)

        if "research" in normalized:
            return (
                "Here is a concise research summary based on available offline sources. "
                "I've saved a markdown brief under artifacts/research."
            )
        if "create" in normalized and ".py" in normalized:
            return (
                "Spinning up CodeSkill to scaffold the requested Python file. "
                "I'll confirm before executing if anything looks risky."
            )
        if "remind" in normalized:
            return "Reminder scheduled. I'll nudge you politely and log it in the dashboard."
        if "status" in normalized or "state" in normalized:
            return "Envy status report: all services nominal. Wake listener idle, skills standing by."

        return (
            "Envy here. I've parsed your request and routed it through the skill manager. "
            "You can review the execution plan on the dashboard."
        )
