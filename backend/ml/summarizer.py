# ml/summarizer.py
import logging
import re
from typing import List, Optional

# In a production environment, you would import and use transformers here
# from transformers import pipeline

logger = logging.getLogger(__name__)

class RequirementsSummarizer:
    """Class for summarizing job requirements using NLP"""
    
    def __init__(self):
        # In a real implementation, you would initialize the model here
        # self.summarizer = pipeline("summarization", model="t5-small")
        logger.info("Initialized requirements summarizer")
    
    def summarize(self, text: str, max_length: int = 150) -> str:
        """
        Summarize job requirements text
        
        In a real implementation, this would use a transformer model.
        This is a simplified rule-based implementation for demonstration.
        """
        if not text:
            return ""
        
        try:
            # Extract requirements section if it exists
            requirements_section = self._extract_requirements_section(text)
            
            if not requirements_section:
                # If no requirements section found, return a generic message
                return "No specific requirements listed."
            
            # Extract bullet points if they exist
            bullet_points = self._extract_bullet_points(requirements_section)
            
            if bullet_points:
                # If bullet points found, use them
                return self._format_bullet_points(bullet_points, max_length)
            else:
                # Otherwise, do a simple extractive summary
                return self._simple_extractive_summary(requirements_section, max_length)
        
        except Exception as e:
            logger.error(f"Error summarizing requirements: {str(e)}")
            return "Failed to summarize requirements."
    
    def _extract_requirements_section(self, text: str) -> str:
        """Extract requirements section from job description"""
        # Look for common section headers
        patterns = [
            r"(?i)requirements?[:\s]+(.*?)(?:\n\n|\n[A-Z]|\Z)",
            r"(?i)qualifications?[:\s]+(.*?)(?:\n\n|\n[A-Z]|\Z)",
            r"(?i)what you'll need[:\s]+(.*?)(?:\n\n|\n[A-Z]|\Z)",
            r"(?i)what we're looking for[:\s]+(.*?)(?:\n\n|\n[A-Z]|\Z)",
            r"(?i)skills[:\s]+(.*?)(?:\n\n|\n[A-Z]|\Z)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no specific section found, return the first 30% of the text
        # as it often contains key requirements
        return text[:int(len(text) * 0.3)]
    
    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points from text"""
        # Look for common bullet point patterns
        bullet_patterns = [
            r"•\s+(.*?)(?:\n|$)",
            r"-\s+(.*?)(?:\n|$)",
            r"\*\s+(.*?)(?:\n|$)",
            r"\d+\.\s+(.*?)(?:\n|$)",
        ]
        
        bullet_points = []
        for pattern in bullet_patterns:
            points = re.findall(pattern, text)
            bullet_points.extend(points)
        
        # Clean up points
        bullet_points = [p.strip() for p in bullet_points if p.strip()]
        
        return bullet_points
    
    def _format_bullet_points(self, points: List[str], max_length: int) -> str:
        """Format bullet points into a summary"""
        # Take the top points up to the max length
        result = ""
        for point in points[:5]:  # Limit to 5 points
            if len(result) + len(point) < max_length:
                result += f"• {point}\n"
            else:
                break
        
        return result.strip()
    
    def _simple_extractive_summary(self, text: str, max_length: int) -> str:
        """Simple extractive summary when no bullet points are found"""
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Score sentences by important keywords
        keywords = ["experience", "degree", "knowledge", "skill", "background", 
                   "proficiency", "ability", "years", "understanding", "familiar"]
        
        scored_sentences = []
        for sentence in sentences:
            score = sum(1 for keyword in keywords if keyword.lower() in sentence.lower())
            scored_sentences.append((sentence, score))
        
        # Sort by score
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Take top sentences up to max length
        summary = ""
        for sentence, _ in scored_sentences[:3]:  # Limit to 3 sentences
            if len(summary) + len(sentence) < max_length:
                summary += sentence + " "
            else:
                break
        
        return summary.strip()


# Singleton instance
summarizer = RequirementsSummarizer()

def summarize_job_requirements(text: str) -> str:
    """Summarize job requirements from text"""
    return summarizer.summarize(text)