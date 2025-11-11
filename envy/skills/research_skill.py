"""
Research Skill - Researches topics and creates summaries
MIT License
"""

import os
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent))
from __init__ import BaseSkill

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.config_manager import get_config
from services.llm_adapter import LLMAdapter

logger = logging.getLogger(__name__)


class ResearchSkill(BaseSkill):
    """Skill for researching topics and creating summaries"""
    
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.llm_adapter = LLMAdapter()
        self.output_path = Path(self.config.get('skills.research.output_path', 'artifacts/research'))
        self.max_results = self.config.get('skills.research.max_results', 5)
        
        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ResearchSkill initialized (output: {self.output_path})")
    
    def execute(self, command: str) -> str:
        """Execute research command"""
        try:
            # Extract topic
            topic = self.extract_topic(command)
            
            if not topic:
                return "Could not determine research topic from command."
            
            logger.info(f"Researching topic: {topic}")
            
            # Generate research summary using LLM
            summary = self.research_topic(topic)
            
            # Save to file
            filename = self.generate_filename(topic)
            file_path = self.output_path / filename
            
            with open(file_path, 'w') as f:
                f.write(f"# Research: {topic}\n\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"## Summary\n\n{summary}\n")
            
            logger.info(f"Research saved to {file_path}")
            
            # Return brief response
            brief_summary = summary[:200] + "..." if len(summary) > 200 else summary
            return f"Research on {topic} complete. {brief_summary} Full details saved to {filename}."
            
        except Exception as e:
            logger.error(f"ResearchSkill execution failed: {e}")
            return f"Research failed: {str(e)}"
    
    def extract_topic(self, command: str) -> Optional[str]:
        """Extract research topic from command"""
        command_lower = command.lower()
        
        # Pattern 1: "research X"
        match = re.search(r'research\s+(.+)', command_lower)
        if match:
            return match.group(1).strip()
        
        # Pattern 2: "tell me about X"
        match = re.search(r'tell me about\s+(.+)', command_lower)
        if match:
            return match.group(1).strip()
        
        # Pattern 3: "look up X"
        match = re.search(r'look up\s+(.+)', command_lower)
        if match:
            return match.group(1).strip()
        
        # Pattern 4: "search for X"
        match = re.search(r'search for\s+(.+)', command_lower)
        if match:
            return match.group(1).strip()
        
        return None
    
    def research_topic(self, topic: str) -> str:
        """Research topic and generate summary"""
        try:
            # Use LLM to generate research summary
            prompt = f"""Provide a concise research summary about: {topic}

Include:
1. Overview and key points
2. Important facts or concepts
3. Current relevance or applications

Keep the response informative but concise (around 200-300 words)."""
            
            summary, source = self.llm_adapter.generate(prompt, max_tokens=400)
            
            if summary:
                return summary
            else:
                return f"Unable to research {topic}. Please try again."
                
        except Exception as e:
            logger.error(f"Research generation failed: {e}")
            return f"Research generation error: {str(e)}"
    
    def generate_filename(self, topic: str) -> str:
        """Generate safe filename from topic"""
        # Remove special characters
        safe_topic = re.sub(r'[^\w\s-]', '', topic.lower())
        safe_topic = re.sub(r'[\s_]+', '_', safe_topic)
        safe_topic = safe_topic[:50]  # Limit length
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"research_{safe_topic}_{timestamp}.md"
    
    def requires_confirmation(self) -> bool:
        return False
    
    def get_description(self) -> str:
        return "Researches topics and creates summaries using LLM"
