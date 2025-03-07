# app/ml/processors/requirements_extractor.py
import logging
import re
from typing import List, Dict, Tuple, Optional, Set, Any

# Import ML-related packages with fallback
try:
    import nltk
    from nltk.tokenize import sent_tokenize
    from nltk.corpus import stopwords
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available, using simplified tokenization")

logger = logging.getLogger(__name__)

class RequirementsExtractor:
    """
    Extracts and summarizes job requirements from job descriptions
    
    Uses a hybrid approach:
    1. Locate requirements section using pattern matching and ML techniques
    2. Extract key requirements as bullet points
    3. Categorize and format requirements into a readable summary
    """
    
    def __init__(self):
        """Initialize the requirements extractor"""
        # Patterns to identify requirements sections
        self.section_patterns = [
            r'(?i)requirements?[:\s]+(.*?)(?:(?:\n\n|\n[A-Z]|\Z))',
            r'(?i)qualifications?[:\s]+(.*?)(?:(?:\n\n|\n[A-Z]|\Z))',
            r'(?i)what you\'ll need[:\s]+(.*?)(?:(?:\n\n|\n[A-Z]|\Z))',
            r'(?i)what we\'re looking for[:\s]+(.*?)(?:(?:\n\n|\n[A-Z]|\Z))',
            r'(?i)skills[:\s]+(.*?)(?:(?:\n\n|\n[A-Z]|\Z))',
            r'(?i)basic qualifications[:\s]+(.*?)(?:(?:\n\n|\n[A-Z]|\Z))',
            r'(?i)minimum qualifications[:\s]+(.*?)(?:(?:\n\n|\n[A-Z]|\Z))',
            r'(?i)preferred qualifications[:\s]+(.*?)(?:(?:\n\n|\n[A-Z]|\Z))'
        ]
        
        # Patterns to identify bullet points
        self.bullet_patterns = [
            r'•\s+(.*?)(?:\n|$)',
            r'-\s+(.*?)(?:\n|$)',
            r'\*\s+(.*?)(?:\n|$)',
            r'\d+\.\s+(.*?)(?:\n|$)',
        ]
        
        # Important keywords to identify key requirements
        self.important_keywords = [
            'experience', 'degree', 'knowledge', 'skill', 'background',
            'proficiency', 'ability', 'years', 'understanding', 'familiar',
            'bachelor', 'master', 'phd', 'education', 'required', 'qualification',
            'programming', 'language', 'software', 'hardware', 'system', 'design',
            'engineering', 'computer science', 'electrical', 'team', 'collaborate'
        ]
        
        # Category keywords
        self.education_keywords = [
            'degree', 'bachelor', 'master', 'phd', 'bs', 'ms', 'education', 
            'university', 'college', 'graduate'
        ]
        
        self.experience_keywords = [
            'experience', 'years', 'work', 'professional', 'industry', 'background'
        ]
        
        self.technical_keywords = [
            'programming', 'language', 'code', 'development', 'software', 'hardware',
            'tools', 'platform', 'framework', 'library', 'system', 'technical'
        ]
        
        self.soft_skills_keywords = [
            'communicate', 'team', 'collaborate', 'interpersonal', 'problem-solving',
            'analytical', 'organized', 'leadership', 'detail', 'time management'
        ]
        
        logger.info("Requirements extractor initialized")
    
    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK or fallback approach"""
        if not text:
            return []
            
        if NLTK_AVAILABLE:
            return sent_tokenize(text)
        else:
            # Simple fallback sentence splitting
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def extract_requirements(self, description: str, max_bullets: int = 5) -> str:
        """Extract key requirements from job description"""
        if not description:
            return "No requirements specified."
        
        try:
            # Find the requirements section
            requirements_section = self._find_requirements_section(description)
            
            if not requirements_section:
                # If no specific section found, use the whole description
                requirements_section = description
            
            # Extract bullet points
            bullet_points = self._extract_bullet_points(requirements_section)
            
            if bullet_points:
                # Score and select the most important bullet points
                scored_points = self._score_bullet_points(bullet_points)
                
                # Categorize points
                categorized_points = self._categorize_points(scored_points)
                
                # Format the selected bullet points
                return self._format_categorized_points(categorized_points)
            else:
                # If no bullet points, extract key sentences
                return self._extract_key_sentences(requirements_section, max_sentences=3)
        
        except Exception as e:
            logger.error(f"Error extracting requirements: {str(e)}")
            return "No specific requirements extracted."
    
    def _find_requirements_section(self, description: str) -> str:
        """Find the requirements section in the job description"""
        for pattern in self.section_patterns:
            match = re.search(pattern, description, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points from text"""
        bullet_points = []
        for pattern in self.bullet_patterns:
            points = re.findall(pattern, text, re.MULTILINE)
            bullet_points.extend([p.strip() for p in points if p.strip()])
        
        # If no bullet points were found, try to find sentences that look like requirements
        if not bullet_points:
            sentences = self.split_sentences(text)
            for sentence in sentences:
                # Look for sentences that start with requirement-like phrases
                if re.match(r'^(must|should|need to|required to|ability to|experience (in|with))', 
                           sentence.lower()):
                    bullet_points.append(sentence)
        
        return bullet_points
    
    def _score_bullet_points(self, bullet_points: List[str]) -> List[Tuple[str, float]]:
        """Score bullet points by relevance to requirements"""
        scored_points = []
        
        for point in bullet_points:
            point_lower = point.lower()
            
            # Base score
            score = 1.0
            
            # Keywords in point
            score += sum(2.0 for keyword in self.important_keywords 
                         if re.search(r'\b{}\b'.format(re.escape(keyword)), point_lower))
            
            # Prefer points with specific numbers (e.g., years of experience)
            if re.search(r'\d+', point):
                score += 2.0
            
            # Prefer points with educational requirements
            if any(re.search(r'\b{}\b'.format(re.escape(kw)), point_lower) 
                   for kw in self.education_keywords):
                score += 3.0
            
            # Prefer points mentioning years of experience
            if re.search(r'\b\d+\+?\s*(year|yr)s?\b', point_lower):
                score += 3.0
            
            # Adjust score based on length (preference for concise points)
            length = len(point)
            if 40 <= length <= 150:
                score += 1.0
            elif length > 150:
                score -= 1.0
            
            scored_points.append((point, score))
        
        # Sort by score (descending)
        return sorted(scored_points, key=lambda x: x[1], reverse=True)
    
    def _categorize_points(self, scored_points: List[Tuple[str, float]]) -> Dict[str, List[str]]:
        """Categorize requirements by type"""
        categories = {
            'education': [],
            'experience': [],
            'technical': [],
            'soft_skills': [],
            'other': []
        }
        
        for point, _ in scored_points:
            point_lower = point.lower()
            
            # Check categories
            if any(kw in point_lower for kw in self.education_keywords):
                categories['education'].append(point)
            elif any(kw in point_lower for kw in self.experience_keywords):
                categories['experience'].append(point)
            elif any(kw in point_lower for kw in self.technical_keywords):
                categories['technical'].append(point)
            elif any(kw in point_lower for kw in self.soft_skills_keywords):
                categories['soft_skills'].append(point)
            else:
                categories['other'].append(point)
        
        return categories
    
    def _format_categorized_points(self, categories: Dict[str, List[str]]) -> str:
        """Format categorized points into a readable summary"""
        if sum(len(points) for points in categories.values()) == 0:
            return "No specific requirements extracted."
        
        result = "Key Requirements:\n\n"
        
        # Category display names and order
        category_order = [
            ('education', 'Education:', 1),  # (key, display_name, max_items)
            ('experience', 'Experience:', 2),
            ('technical', 'Technical Skills:', 3),
            ('soft_skills', 'Soft Skills:', 1),
            ('other', 'Other Requirements:', 1)
        ]
        
        # Add each category
        for key, display_name, max_items in category_order:
            points = categories.get(key, [])
            if points:
                # Add section header
                result += f"{display_name}\n"
                
                # Add top N points from this category
                for point in points[:max_items]:
                    # Clean up point text
                    cleaned_point = point.strip()
                    if not cleaned_point.endswith(('.', '!', '?')):
                        cleaned_point += '.'
                        
                    # Format as bullet point
                    result += f"• {cleaned_point}\n"
                
                # Add space between categories
                result += "\n"
        
        return result.strip()
    
    def _extract_key_sentences(self, text: str, max_sentences: int = 3) -> str:
        """Extract key sentences when no bullet points are found"""
        sentences = self.split_sentences(text)
        
        # Score sentences for relevance
        scored_sentences = []
        for sentence in sentences:
            if len(sentence) < 15 or len(sentence) > 200:  # Skip very short/long sentences
                continue
                
            score = 0
            sentence_lower = sentence.lower()
            
            # Check for important keywords
            score += sum(1.0 for keyword in self.important_keywords 
                        if keyword in sentence_lower)
            
            # Boost sentences mentioning education
            if any(kw in sentence_lower for kw in self.education_keywords):
                score += 2.0
            
            # Boost sentences mentioning experience with years
            if re.search(r'\b\d+\+?\s*(year|yr)s?\b', sentence_lower):
                score += 3.0
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and take top sentences
        top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)[:max_sentences]
        
        if not top_sentences:
            return "No specific requirements extracted."
        
        # Format as bullet points
        result = "Key Requirements:\n\n"
        for sentence, _ in top_sentences:
            result += f"• {sentence.strip()}\n"
        
        return result.strip()


# Create singleton instance
_extractor = RequirementsExtractor()

def extract_requirements_summary(description: str) -> str:
    """
    Extract and summarize requirements from a job description
    
    This is the main function to be called from external modules.
    
    Args:
        description: The job description text
        
    Returns:
        A formatted summary of key requirements
    """
    return _extractor.extract_requirements(description)