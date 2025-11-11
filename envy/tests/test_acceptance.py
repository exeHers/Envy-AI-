"""Acceptance tests for Envy."""
import pytest
import asyncio
import sys
import os
from pathlib import Path
import numpy as np
import wave

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.config_loader import get_config
from services.stt_service import STTService
from services.tts_service import TTSService
from services.llm_adapter import LLMAdapter
from services.skill_manager import SkillManager
from services.router import Router


@pytest.fixture
def config():
    """Get configuration."""
    return get_config()


@pytest.fixture
def stt_service():
    """Create STT service."""
    stt = STTService()
    stt.initialize()
    return stt


@pytest.fixture
def tts_service():
    """Create TTS service."""
    tts = TTSService()
    tts.initialize()
    return tts


@pytest.fixture
def llm_adapter():
    """Create LLM adapter."""
    llm = LLMAdapter()
    llm.initialize()
    return llm


@pytest.fixture
def skill_manager():
    """Create skill manager."""
    sm = SkillManager()
    sm.initialize()
    return sm


@pytest.fixture
def router(skill_manager):
    """Create router."""
    r = Router(skill_manager=skill_manager)
    r.initialize()
    return r


def create_test_audio(text: str, filename: str, duration: float = 2.0):
    """Create a test audio file with tone (simulated speech)."""
    sample_rate = 16000
    samples = int(sample_rate * duration)
    
    # Create a simple tone as placeholder
    t = np.linspace(0, duration, samples)
    # Mix of frequencies to simulate speech
    audio = np.sin(2 * np.pi * 440 * t) * 0.3 + np.sin(2 * np.pi * 880 * t) * 0.2
    audio = (audio * 32767).astype(np.int16)
    
    # Save to WAV file
    output_path = Path(__file__).parent / "test_audio" / filename
    output_path.parent.mkdir(exist_ok=True)
    
    with wave.open(str(output_path), 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
        
    return output_path


class TestAcceptance:
    """Acceptance tests for Envy."""
    
    def test_config_loads(self, config):
        """Test that configuration loads properly."""
        assert config is not None
        assert config.get("profile") in ["low", "balanced", "power"]
        assert config.get("wake_word.keyword") == "envy"
        print("✓ Configuration loads correctly")
        
    def test_stt_initialization(self, stt_service):
        """Test STT service initialization."""
        assert stt_service is not None
        assert stt_service.model is not None
        print("✓ STT service initializes")
        
    def test_tts_initialization(self, tts_service):
        """Test TTS service initialization."""
        assert tts_service is not None
        assert tts_service.engine is not None
        print("✓ TTS service initializes")
        
    def test_tts_synthesis(self, tts_service):
        """Test TTS synthesis to file."""
        output_path = Path(__file__).parent.parent / "artifacts" / "tests" / "tts-output.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        result = tts_service.save_to_file(
            "Hello, this is Envy speaking.",
            str(output_path)
        )
        
        assert result is True
        assert output_path.exists()
        print(f"✓ TTS synthesized audio to {output_path}")
        
    def test_llm_adapter_initialization(self, llm_adapter):
        """Test LLM adapter initialization."""
        assert llm_adapter is not None
        print("✓ LLM adapter initializes")
        
    def test_llm_adapter_generate(self, llm_adapter):
        """Test LLM generation (or fallback)."""
        response = llm_adapter.generate("Hello, how are you?", max_tokens=50)
        assert response is not None
        assert len(response) > 0
        print(f"✓ LLM generated response: {response[:100]}")
        
    def test_llm_intent_classification(self, llm_adapter):
        """Test intent classification."""
        intent = llm_adapter.classify_intent("Create a file called test.py that prints hello")
        assert intent is not None
        assert intent["skill"] == "CodeSkill"
        assert intent["confidence"] > 0.7
        print(f"✓ Intent classified: {intent}")
        
    def test_skill_manager_loads_skills(self, skill_manager):
        """Test that skill manager loads skills."""
        assert skill_manager is not None
        skills = skill_manager.list_skills()
        assert len(skills) > 0
        assert "CodeSkill" in skills
        print(f"✓ Loaded {len(skills)} skills: {skills}")
        
    @pytest.mark.asyncio
    async def test_code_skill_creates_file(self, skill_manager):
        """Test CodeSkill creates a file."""
        result = await skill_manager.execute_skill(
            "CodeSkill",
            "create_file",
            {
                "filename": "test.py",
                "description": "create test.py that prints hello"
            }
        )
        
        assert result["success"] is True
        assert "test.py" in result["response"]
        
        # Check file exists
        workspace = Path.cwd() / "workspace"
        test_file = workspace / "test.py"
        assert test_file.exists()
        
        # Check content
        content = test_file.read_text()
        assert "hello" in content.lower()
        
        print(f"✓ CodeSkill created file: {test_file}")
        print(f"  Content: {content}")
        
    @pytest.mark.asyncio
    async def test_research_skill_creates_summary(self, skill_manager):
        """Test ResearchSkill creates research summary."""
        result = await skill_manager.execute_skill(
            "ResearchSkill",
            "research",
            {
                "query": "research quantum computing",
                "topic": "quantum computing"
            }
        )
        
        assert result["success"] is True
        assert "research" in result["response"].lower()
        
        # Check file was created
        workspace = Path.cwd() / "workspace"
        research_files = list(workspace.glob("research_*.md"))
        assert len(research_files) > 0
        
        print(f"✓ ResearchSkill created summary: {research_files[0]}")
        
    @pytest.mark.asyncio
    async def test_router_processes_request(self, router):
        """Test router processes a request end-to-end."""
        result = await router.process_request("Create a file called hello.py")
        
        assert result is not None
        assert result["success"] is True or result["response"] != ""
        
        print(f"✓ Router processed request: {result['response']}")
        
    def test_wake_word_detection_placeholder(self):
        """Test wake word detection (placeholder - requires audio input)."""
        # This would require actual audio input or mock
        # For now, we just verify the wake listener can be created
        from services.wake_listener import WakeListener
        
        wake_detected = False
        
        def callback():
            nonlocal wake_detected
            wake_detected = True
            
        listener = WakeListener(callback=callback)
        assert listener is not None
        
        # Note: Full test would require feeding audio with "Envy" keyword
        print("✓ Wake listener can be instantiated")


def main():
    """Run acceptance tests."""
    print("\n" + "=" * 60)
    print("Running Envy Acceptance Tests")
    print("=" * 60 + "\n")
    
    # Run pytest
    result = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s"
    ])
    
    return result


if __name__ == "__main__":
    sys.exit(main())
