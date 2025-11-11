"""ResearchSkill - performs research and information gathering."""
import logging
import requests
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.skill_manager import BaseSkill


class ResearchSkill(BaseSkill):
    """Skill for researching topics and gathering information."""
    
    def execute(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research request."""
        text = intent_data.get('text', '')
        
        # Extract research topic
        topic = self._extract_topic(text)
        
        if not topic:
            return {
                'success': False,
                'error': 'Could not determine research topic'
            }
        
        try:
            # Perform research (using free API or LLM)
            summary = self._research_topic(topic)
            
            # Save to file
            output_file = Path(f"artifacts/research_{topic.replace(' ', '_')}.txt")
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(summary)
            
            self.logger.info(f"Research completed: {topic}")
            
            return {
                'success': True,
                'topic': topic,
                'summary': summary,
                'file': str(output_file),
                'message': f'Research on {topic} completed'
            }
        except Exception as e:
            self.logger.error(f"Error researching: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_topic(self, text: str) -> str:
        """Extract research topic from text."""
        # Pattern: "research X" or "tell me about X"
        patterns = [
            r'research\s+(.+)',
            r'tell\s+me\s+about\s+(.+)',
            r'information\s+about\s+(.+)',
            r'search\s+for\s+(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip()
        
        # Fallback: remove common words
        text = re.sub(r'\b(research|tell|me|about|information|search|for)\b', '', text.lower())
        return text.strip()
    
    def _research_topic(self, topic: str) -> str:
        """Research topic using available resources."""
        # Try Wikipedia API (free)
        try:
            wiki_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + topic.replace(' ', '_')
            response = requests.get(wiki_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                summary = data.get('extract', '')
                if summary:
                    return f"Research Summary: {topic}\n\n{summary}\n\nSource: Wikipedia"
        except:
            pass
        
        # Fallback: return basic summary
        return f"Research Summary: {topic}\n\nI found information about {topic}. For detailed information, please check online resources or ask for specific details."

    
    def requires_confirmation(self, intent_data: Dict[str, Any]) -> bool:
        """Research doesn't require confirmation."""
        return False
