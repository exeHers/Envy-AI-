"""Configuration loader for Envy."""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ResourceConfig(BaseModel):
    max_cpu_percent: float = 50.0
    max_memory_mb: int = 4096
    max_gpu_memory_mb: int = 2048
    use_gpu: bool = True


class WakeWordConfig(BaseModel):
    keyword: str = "envy"
    sensitivity: float = 0.5
    model_path: str = "models/vosk-model-small-en-us-0.15"
    continuous_listening: bool = True


class STTConfig(BaseModel):
    engine: str = "vosk"
    vosk_model_path: str = "models/vosk-model-small-en-us-0.15"
    whisper_model: str = "small"
    use_gpu: bool = False
    streaming: bool = True


class TTSConfig(BaseModel):
    engine: str = "pyttsx3"
    voice_id: Optional[str] = None
    rate: int = 150
    volume: float = 0.9
    streaming: bool = True


class LocalLLMConfig(BaseModel):
    model_path: str = "models/llama-2-7b-chat.gguf"
    model_type: str = "llama.cpp"
    context_size: int = 2048
    n_gpu_layers: int = 20
    use_mmap: bool = True
    use_mlock: bool = False


class RemoteLLMConfig(BaseModel):
    enabled: bool = False
    endpoint: str = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
    api_key: str = ""
    timeout: int = 30


class LLMConfig(BaseModel):
    provider: str = "local"
    local: LocalLLMConfig = Field(default_factory=LocalLLMConfig)
    remote_free: RemoteLLMConfig = Field(default_factory=RemoteLLMConfig)
    fallback_enabled: bool = True


class RouterConfig(BaseModel):
    intent_classifier: str = "rule_based"
    confidence_threshold: float = 0.7
    max_response_time: int = 10


class SkillsConfig(BaseModel):
    enabled: list = Field(default_factory=lambda: ["CodeSkill", "ResearchSkill", "SysControlSkill", "ReminderSkill"])
    timeout: int = 30
    sandbox: bool = True
    require_confirmation: bool = True


class SecurityConfig(BaseModel):
    allow_system_commands: bool = False
    command_whitelist: list = Field(default_factory=list)
    require_voice_confirmation: bool = True
    require_dashboard_confirmation: bool = True
    sandbox_execution: bool = True


class WebConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    enable_cors: bool = True
    log_level: str = "info"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "artifacts/envy.log"
    max_size_mb: int = 10
    backup_count: int = 5


class PersonaConfig(BaseModel):
    name: str = "Envy"
    tone: str = "neutral"
    verbosity: str = "concise"
    sardonic_level: float = 0.3


class EnvyConfig(BaseSettings):
    profile: str = "balanced"
    resources: ResourceConfig = Field(default_factory=ResourceConfig)
    wake_word: WakeWordConfig = Field(default_factory=WakeWordConfig)
    stt: STTConfig = Field(default_factory=STTConfig)
    tts: TTSConfig = Field(default_factory=TTSConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    router: RouterConfig = Field(default_factory=RouterConfig)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    persona: PersonaConfig = Field(default_factory=PersonaConfig)

    @classmethod
    def load_from_file(cls, config_path: str = "config/envy.yaml") -> "EnvyConfig":
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            # Return defaults if file doesn't exist
            return cls()
        
        with open(config_file, 'r') as f:
            config_dict = yaml.safe_load(f) or {}
        
        # Apply profile-specific overrides
        profile = config_dict.get('profile', 'balanced')
        if profile == 'low':
            config_dict.setdefault('resources', {})['max_cpu_percent'] = 25
            config_dict.setdefault('resources', {})['max_memory_mb'] = 2048
        elif profile == 'power':
            config_dict.setdefault('resources', {})['max_cpu_percent'] = 90
            config_dict.setdefault('resources', {})['max_memory_mb'] = 8192
        
        return cls(**config_dict)

    def save_to_file(self, config_path: str = "config/envy.yaml"):
        """Save configuration to YAML file."""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = self.model_dump()
        with open(config_file, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
