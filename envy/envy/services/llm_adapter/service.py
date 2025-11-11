from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

logger = logging.getLogger("envy.llm_adapter")


try:
    from llama_cpp import Llama  # type: ignore
except ImportError:  # pragma: no cover - optional
    Llama = None


@dataclass
class LLMConfig:
    provider: str = "stub"
    model_path: Optional[str] = None
    max_tokens: int = 256
    gpu_layers: int = 0
    remote: Dict[str, str] | None = None


class LLMAdapter:
    def __init__(self, config: LLMConfig):
        self.config = config
        self._llama = None
        if self.config.provider == "llama_cpp" and Llama and self.config.model_path:
            try:
                self._llama = Llama(
                    model_path=self.config.model_path,
                    n_ctx=2048,
                    n_threads=4,
                    n_gpu_layers=self.config.gpu_layers,
                )
                logger.info("Loaded llama.cpp model %s", self.config.model_path)
            except Exception as exc:  # pragma: no cover - runtime guard
                logger.error("Failed to load llama.cpp model: %s", exc)

    async def complete(self, prompt: str, persona: str = "neutral") -> str:
        provider = self.config.provider
        if provider == "stub":
            return self._stub_completion(prompt, persona)
        if provider == "llama_cpp" and self._llama:
            return await asyncio.to_thread(self._llama_completion, prompt, persona)
        if provider == "remote" and self.config.remote:
            return await self._remote_completion(prompt)
        logger.warning("LLM provider unavailable; returning stub response.")
        return self._stub_completion(prompt, persona)

    def _stub_completion(self, prompt: str, persona: str) -> str:
        return (
            "Envy here. I processed your request locally using the lightweight fallback model. "
            f"Prompt summary: {prompt[:120]}..."
        )

    def _llama_completion(self, prompt: str, persona: str) -> str:
        response = self._llama.create_completion(
            prompt=f"[Persona: {persona}] {prompt}\nAssistant:",
            max_tokens=self.config.max_tokens,
            temperature=0.7,
        )
        return response["choices"][0]["text"].strip()

    async def _remote_completion(self, prompt: str) -> str:
        remote_cfg = self.config.remote or {}
        url = remote_cfg.get("url")
        headers = {}
        token_env = remote_cfg.get("auth_env")
        if token_env:
            import os

            token = os.getenv(token_env)
            if token:
                headers["Authorization"] = f"Bearer {token}"
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": self.config.max_tokens}}
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "")
            if isinstance(data, dict):
                return data.get("generated_text", "")
            return str(data)


class CompletionRequest(BaseModel):
    prompt: str
    persona: str = "neutral"


class CompletionResponse(BaseModel):
    text: str
    provider: str


def create_app(adapter: LLMAdapter) -> FastAPI:
    app = FastAPI(title="Envy LLM Adapter")

    @app.post("/complete", response_model=CompletionResponse)
    async def complete(request: CompletionRequest):
        text = await adapter.complete(request.prompt, persona=request.persona)
        return CompletionResponse(text=text, provider=adapter.config.provider)

    return app
