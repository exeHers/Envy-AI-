from __future__ import annotations

from pathlib import Path
from typing import Dict

from ..common.config import EnvyConfig
from ..common.logging import get_logger


class LLMAdapter:
    def __init__(self, config: EnvyConfig) -> None:
        self.config = config
        self.logger = get_logger("LLMAdapter", config=config)
        self.persona = config.get("llm.persona_prompt", "You are Envy.")
        self.use_llama = False
        self.llama = None

        llama_cfg = config.get("llama_cpp", {})
        if llama_cfg.get("enabled"):
            try:
                from llama_cpp import Llama  # type: ignore

                model_path = Path(llama_cfg.get("model_path", "models/llama/ggml-model-q4_0.bin"))
                if model_path.exists():
                    self.llama = Llama(model_path=str(model_path), n_ctx=llama_cfg.get("context_length", 2048))
                    self.use_llama = True
                    self.logger.info(f"Loaded llama.cpp model from {model_path}")
                else:
                    self.logger.warning(f"Llama model path missing: {model_path}")
            except Exception as exc:  # noqa: BLE001
                self.logger.warning(f"llama.cpp unavailable, falling back to rule-based responses: {exc}")

    def respond(self, transcript: str, context: Dict[str, str]) -> Dict[str, str]:
        if self.use_llama and self.llama:
            prompt = self._build_prompt(transcript, context)
            try:
                completion = self.llama(
                    prompt,
                    max_tokens=self.config.get("llama_cpp.max_tokens", 256),
                    temperature=self.config.get("llama_cpp.temperature", 0.7),
                )
                text = completion["choices"][0]["text"].strip()
                return {"text": text, "engine": "llama_cpp"}
            except Exception as exc:  # noqa: BLE001
                self.logger.warning(f"llama.cpp inference failed: {exc}")
        return {"text": self._fallback_response(transcript, context), "engine": "rule-based"}

    def _build_prompt(self, transcript: str, context: Dict[str, str]) -> str:
        history = context.get("history", "")
        intent = context.get("intent", "unknown")
        prompt = (
            f"{self.persona}\n\n"
            f"Conversation history:\n{history}\n\n"
            f"Latest user request (intent={intent}):\n{transcript}\n\n"
            "Respond concisely."
        )
        return prompt

    def _fallback_response(self, transcript: str, context: Dict[str, str]) -> str:
        intent = context.get("intent", "fallback")
        canned = self.config.get("llm.local_rule.canned_responses", {})
        if intent.startswith("code"):
            return canned.get("code", "Generating the requested code now.")
        if intent.startswith("research"):
            return canned.get("research", "Research mode active. Compiling a summary.")
        return canned.get("fallback", "I'll handle that with my local tools.")


__all__ = ["LLMAdapter"]
