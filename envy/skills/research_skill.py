#!/usr/bin/env python3
"""
Research Skill - Researches topics and creates summaries
Provides information gathering and synthesis capabilities
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ResearchSkill:
    """Skill for researching topics and creating summaries"""
    
    def __init__(self, config):
        self.config = config
        skill_config = config.get('skills', {}).get('research_skill', {})
        self.output_dir = skill_config.get('output_dir', './artifacts/research')
        self.max_sources = skill_config.get('max_sources', 5)
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"ResearchSkill initialized, output dir: {self.output_dir}")
    
    def execute(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute research task"""
        
        # Extract research topic
        topic = self._extract_topic(input_text)
        
        if not topic:
            return {
                'success': False,
                'error': 'Could not extract research topic',
                'response': "I couldn't understand what you want me to research."
            }
        
        logger.info(f"Researching topic: {topic}")
        
        # Conduct research (simplified - uses LLM knowledge)
        research_result = self._research_topic(topic)
        
        # Save research to file
        output_file = self._save_research(topic, research_result)
        
        # Generate spoken summary
        summary = self._generate_summary(research_result)
        
        return {
            'success': True,
            'action': 'research_completed',
            'topic': topic,
            'output_file': output_file,
            'summary': summary,
            'response': f"I've completed research on {topic}. {summary}"
        }
    
    def _extract_topic(self, input_text: str) -> Optional[str]:
        """Extract research topic from input"""
        text_lower = input_text.lower()
        
        # Remove command words at the beginning
        text_lower = text_lower.strip()
        for prefix in ['research ', 'find ', 'search ', 'look up ']:
            if text_lower.startswith(prefix):
                text_lower = text_lower[len(prefix):].strip()
                break
        
        # Remove "information about" or "about" prefix
        for prefix in ['information about ', 'about ', 'on ']:
            if text_lower.startswith(prefix):
                text_lower = text_lower[len(prefix):].strip()
                break
        
        # Clean up
        topic = text_lower.strip()
        
        if len(topic) > 3:
            return topic
        
        return None
    
    def _research_topic(self, topic: str) -> Dict[str, Any]:
        """Conduct research on topic (simplified)"""
        
        # In a full implementation, this would:
        # 1. Query multiple sources (Wikipedia, arXiv, web search APIs)
        # 2. Extract relevant information
        # 3. Synthesize findings
        
        # For this demo, we'll create a structured research result
        # In production, you'd integrate with LLM for synthesis
        
        research_data = {
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'sources': [],
            'key_findings': [],
            'summary': ''
        }
        
        # Simulate research findings
        if 'python' in topic.lower():
            research_data['summary'] = (
                f"Python is a high-level, interpreted programming language known for its "
                f"simplicity and readability. It was created by Guido van Rossum and first "
                f"released in 1991. Python is widely used in web development, data science, "
                f"machine learning, automation, and scientific computing."
            )
            research_data['key_findings'] = [
                "Created by Guido van Rossum in 1991",
                "High-level, interpreted language",
                "Known for simplicity and readability",
                "Used in web dev, data science, ML, automation",
                "Large standard library and ecosystem"
            ]
            research_data['sources'] = [
                "Python.org",
                "Wikipedia - Python (programming language)",
                "Real Python tutorials"
            ]
        
        elif 'artificial intelligence' in topic.lower() or 'ai' in topic.lower():
            research_data['summary'] = (
                f"Artificial Intelligence (AI) is the simulation of human intelligence processes "
                f"by machines, especially computer systems. These processes include learning, "
                f"reasoning, and self-correction. Major AI techniques include machine learning, "
                f"neural networks, and natural language processing."
            )
            research_data['key_findings'] = [
                "AI simulates human intelligence in machines",
                "Includes machine learning and neural networks",
                "Applications in various fields",
                "Rapid advancement in recent years",
                "Ethical considerations are important"
            ]
            research_data['sources'] = [
                "Stanford AI Lab",
                "MIT AI Research",
                "Nature - AI Journal"
            ]
        
        else:
            # Generic research template
            research_data['summary'] = (
                f"Research on '{topic}': This is a complex subject with multiple aspects. "
                f"Further detailed research would provide more specific information about "
                f"the history, current state, and future developments in this area."
            )
            research_data['key_findings'] = [
                f"Topic requires detailed investigation",
                f"Multiple perspectives available",
                f"Active area of study or interest"
            ]
            research_data['sources'] = [
                "General knowledge base",
                "Academic databases",
                "Online resources"
            ]
        
        return research_data
    
    def _save_research(self, topic: str, research_data: Dict[str, Any]) -> str:
        """Save research results to file"""
        
        # Create safe filename
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"research_{safe_topic}_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        # Format as Markdown
        content = f"# Research: {topic}\n\n"
        content += f"**Generated**: {research_data['timestamp']}\n\n"
        content += f"## Summary\n\n{research_data['summary']}\n\n"
        content += f"## Key Findings\n\n"
        
        for finding in research_data['key_findings']:
            content += f"- {finding}\n"
        
        content += f"\n## Sources\n\n"
        for source in research_data['sources']:
            content += f"- {source}\n"
        
        content += f"\n---\n\n*Research conducted by Envy AI Assistant*\n"
        
        # Save to file
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            
            logger.info(f"Research saved to: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Error saving research: {e}")
            return ""
    
    def _generate_summary(self, research_data: Dict[str, Any]) -> str:
        """Generate a concise spoken summary"""
        summary = research_data['summary']
        
        # Keep it concise for speech
        if len(summary) > 200:
            summary = summary[:197] + "..."
        
        return summary
    
    def is_destructive(self, input_text: str) -> bool:
        """Research is not destructive"""
        return False
    
    def preview_action(self, input_text: str) -> str:
        """Preview the action"""
        topic = self._extract_topic(input_text)
        return f"Research topic: {topic}"


def main():
    """Standalone test"""
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'skills': {
            'research_skill': {
                'output_dir': './artifacts/research',
                'max_sources': 5
            }
        }
    }
    
    skill = ResearchSkill(config)
    
    # Test research
    result = skill.execute("Research Python programming language")
    print(f"Result: {result}")
    print(f"\nOutput file: {result.get('output_file')}")


if __name__ == "__main__":
    main()
