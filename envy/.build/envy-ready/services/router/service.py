from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from ..config import resolve_profile, load_config
from ..logger import get_logger
from ..llm import LLMAdapter
from ..skill_manager import SkillManager
from ..stt_service import SttService
from ..tts_service import TtsService
from ..wake_listener import WakeListener


logger = get_logger("router")


@dataclass
class RouterResult:
    wake_detected: bool
    transcript: str
    intent: str
    skill_result: Dict
    llm_response: Dict
    tts_path: str


class EnvyRouter:
    def __init__(self, config_path: Optional[Path] = None, profile: Optional[str] = None):
        self.config = load_config(config_path)
        self.profile = resolve_profile(self.config, profile)
        self.wake_listener = WakeListener(config_path, profile)
        self.stt_service = SttService(config_path, profile)
        self.tts_service = TtsService(config_path, profile)
        self.llm_adapter = LLMAdapter(config_path, profile)
        self.skill_manager = SkillManager()

    def handle_audio_session(
        self,
        wake_wav: Path,
        command_wav: Path,
        voice_confirmed: bool = True,
        dashboard_confirmed: bool = True,
    ) -> RouterResult:
        wake_result = self.wake_listener.detect_from_file(wake_wav)
        transcript = ""
        intent = "none"
        skill_out = {
            "skill": "none",
            "success": False,
            "output": "",
            "requires_confirmation": False,
            "confirmations_obtained": False,
        }
        llm_dict = {
            "text": "",
            "provider": "none",
            "duration_s": 0.0,
            "tokens": 0,
            "used_remote": False,
        }
        tts_path = ""

        if wake_result.detected:
            stt = self.stt_service.transcribe_wav(command_wav)
            transcript = stt["text"]
            classification = self.llm_adapter.classify_intent(transcript)
            intent = classification["intent"]
            metadata = classification["metadata"]
            metadata["voice_confirmed"] = voice_confirmed
            metadata["dashboard_confirmed"] = dashboard_confirmed
            skill_exec = self.skill_manager.execute(intent, transcript, metadata)
            skill_out = {
                "skill": skill_exec.skill,
                "success": skill_exec.success,
                "output": skill_exec.output,
                "requires_confirmation": skill_exec.requires_confirmation,
                "confirmations_obtained": skill_exec.confirmations_obtained,
            }
            prompt = f"User said: {transcript}\nSkill result: {skill_exec.output}\nRespond as {self.config['assistant']['name']}."
            llm_response = self.llm_adapter.generate(prompt)
            llm_dict = llm_response.__dict__
            tts_result = self.tts_service.synthesize(llm_response.text)
            tts_path = str(tts_result.output_path)
        else:
            logger.warning("Wake word not detected in %s", wake_wav)

        return RouterResult(
            wake_detected=wake_result.detected,
            transcript=transcript,
            intent=intent,
            skill_result=skill_out,
            llm_response=llm_dict,
            tts_path=tts_path,
        )
