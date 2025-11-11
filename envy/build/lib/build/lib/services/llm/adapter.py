from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import load_config, resolve_profile
from ..logger import get_logger


logger = get_logger("llm_adapter")

try:
    from llama_cpp import Llama  # type: ignore
except Exception:  # noqa: BLE001
    Llama = None  # type: ignore[assignment]


@dataclass
class LLMResponse:
    text: str
    provider: str
    duration_s: float
    tokens: int
    used_remote: bool


class LLMAdapter:
    def __init__(self, config_path: Optional[Path] = None, profile: Optional[str] = None):
        self.config = load_config(config_path)
        self.profile = resolve_profile(self.config, profile)
        self.engine = self.profile["llm"]["engine"]
        self.model_path = Path(self.profile["llm"].get("model_path", ""))
        self.remote_conf = self.config.get("remote_endpoints", {})
        self._llama = None
        self._loaded_engine = None

    def _ensure_local_model(self):
        if self.engine != "llama-cpp":
            return
        if Llama is None:
            logger.warning("llama_cpp_python not available; falling back to rule-based responses.")
            self.engine = "rule-based"
            return
        if not self.model_path.exists():
            logger.warning("LLM model not found at %s; falling back to rule-based responses.", self.model_path)
            self.engine = "rule-based"
            return
        if self._llama is None:
            logger.info("Loading llama.cpp model: %s", self.model_path)
            self._llama = Llama(model_path=str(self.model_path), n_gpu_layers=20, n_ctx=2048, verbose=False)
            self._loaded_engine = "llama-cpp"

    def _rule_based(self, prompt: str) -> str:
        lowered = prompt.lower()
        if "create" in lowered and "test.py" in lowered:
            return "Sure. I will instruct the CodeSkill to create test.py with the requested contents."
        if "research" in lowered:
            return "I'll gather a concise summary and place it in the research folder."
        if "remind" in lowered:
            return "Reminder noted. I'll keep that queued."
        return "Envy says: noted. (Rule-based fallback response.)"

    def generate(self, prompt: str, max_tokens: int = 256) -> LLMResponse:
        start = time.monotonic()
        provider = "rule-based"
        tokens = 0
        used_remote = False
        text = ""

        self._ensure_local_model()

        if self.engine == "llama-cpp" and self._llama is not None:
            response = self._llama.create_completion(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.6,
                top_p=0.95,
                echo=False,
            )
            text = response["choices"][0]["text"].strip()
            tokens = response.get("usage", {}).get("completion_tokens", len(text.split()))
            provider = "llama-cpp"
        elif self.remote_conf.get("enabled") and self.remote_conf.get("endpoints"):
            endpoint = self.remote_conf["endpoints"][0]
            try:
                import requests

                payload = {
                    "model": endpoint.get("model", ""),
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                }
                response = requests.post(endpoint["url"], json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
                text = data.get("choices", [{}])[0].get("text", "")
                tokens = data.get("usage", {}).get("completion_tokens", len(text.split()))
                provider = endpoint["name"]
                used_remote = True
            except Exception as exc:  # noqa: BLE001
                logger.error("Remote endpoint failed: %s", exc)
                text = self._rule_based(prompt)
        else:
            text = self._rule_based(prompt)

        duration = time.monotonic() - start
        logger.info("LLM(%s) completed in %.2fs", provider, duration)
        return LLMResponse(text=text, provider=provider, duration_s=duration, tokens=tokens, used_remote=used_remote)

    def classify_intent(self, transcript: str) -> Dict[str, Any]:
        transcript_lower = transcript.lower()
        intent = "general"
        metadata: Dict[str, Any] = {}

        if "create" in transcript_lower and "test.py" in transcript_lower:
            intent = "skill:codeskill"
            metadata["action"] = "create_file"
            metadata["filename"] = "test.py"
        elif "research" in transcript_lower:
            intent = "skill:researchskill"
            metadata["topic"] = transcript_lower.replace("research", "").strip()
        elif "remind" in transcript_lower:
            intent = "skill:reminderskill"
            metadata["reminder"] = transcript
        elif "shutdown" in transcript_lower or "reboot" in transcript_lower:
            intent = "skill:syscontrol"
            metadata["command"] = "shutdown"
        else:
            metadata["prompt"] = transcript

        logger.info("Intent classified as %s with metadata %s", intent, json.dumps(metadata))
        return {"intent": intent, "metadata": metadata}
