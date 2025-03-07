# ml/summarizer.py
import logging
import re
from typing import List, Optional, Dict, Tuple

# In a production environment, you would import and use transformers here
# from transformers import pipeline

logger = logging.getLogger(__name__)

class RequirementsSummarizer:
    """Class for summarizing job requirements using NLP"""
    
    def __init__(self):
        # In a real implementation, you would initialize the model here
        # self.summarizer = pipeline("summarization", model="t5-small")
        logger.info("Initialized requirements summarizer")
        
        # Common section headers for requirements
        self.section_headers = [
            r'requirements',
            r'qualifications',
            r'what you\'ll need',
            r'what we\'re looking for',
            r'skills',
            r'basic qualifications',
            r'minimum qualifications',
            r'preferred qualifications',
            r'about you',
            r'we\'re looking for',
            r'the ideal candidate',
            r'you have',
            r'you should have',
            r'experience'
        ]
        
        # Common education keywords
        self.education_keywords = [
            r'degree', r'bachelor', r'b\.?s\.?', r'master', r'm\.?s\.?', 
            r'phd', r'ph\.?d\.?', r'education', r'university', r'college'
        ]
        
        # Technical skills keywords
        self.technical_keywords = [
            r'programming', r'software', r'development', r'python', r'java', 
            r'javascript', r'c\+\+', r'react', r'nodejs', r'sql', r'database',
            r'git', r'algorithm', r'data structure', r'html', r'css', r'cloud',
            r'aws', r'azure', r'testing', r'ci/cd', r'devops', r'docker', r'kubernetes',
            r'fpga', r'circuit', r'pcb', r'hardware', r'embedded', r'firmware',
            r'verilog', r'hdl', r'electrical', r'electronic', r'digital design'
        ]
    
    def summarize(self, text: str, max_length: int = 150) -> str:
        """
        Summarize job requirements text with beautiful formatting
        
        In a real implementation, this would use a transformer model.
        This is a rule-based implementation that focuses on good formatting.
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
                # If bullet points found, categorize and format them
                return self._format_categorized_bullet_points(bullet_points)
            else:
                # If no bullet points, extract key sentences
                return self._extract_key_sentences(requirements_section)
        
        except Exception as e:
            logger.error(f"Error summarizing requirements: {str(e)}")
            return "Failed to summarize requirements."
    
    def _extract_requirements_section(self, text: str) -> str:
        """Extract requirements section from job description"""
        
        # Clean up text - normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Create regex pattern for section headers
        section_pattern = '|'.join(self.section_headers)
        patterns = [
            # Pattern 1: Headers with colon followed by content until next section
            rf'(?i)({section_pattern})[:\s]+(.*?)(?=\n\n[A-Z]|\n[A-Z][a-z]+[:\s]|\Z)',
            
            # Pattern 2: Headers in all caps or title case
            rf'(?i)(?:\n|\A)([A-Z\s]+({section_pattern})[A-Z\s]+)(?:\n|\Z)(.*?)(?=\n\n[A-Z]|\n[A-Z][a-z]+[:\s]|\Z)',
            
            # Pattern 3: Numbered or bulleted headers
            rf'(?i)(?:\d+\.\s+|\*\s+|•\s+)({section_pattern})[:\s]+(.*?)(?=\n\n|\n\d+\.|\n\*|\n•|\Z)'
        ]
        
        all_sections = []
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    section_content = match.group(2).strip()
                    if len(section_content) > 30:  # Minimum content length
                        all_sections.append(section_content)
        
        # If multiple sections found, concatenate them
        if all_sections:
            combined_section = '\n\n'.join(all_sections)
            return combined_section
        
        # If no specific section found, look for bullet points that might contain requirements
        bullet_matches = re.findall(r'(?:•|\*|-|\d+\.)\s+(?:Must|Should|Experience|Knowledge|Ability|Proficiency|Degree)(.*?)(?:\n|$)', text, re.IGNORECASE)
        if bullet_matches and len(''.join(bullet_matches)) > 30:
            # Reconstruct bullet points
            reconstructed = '\n'.join([f"• {m.strip()}" for m in bullet_matches])
            return reconstructed
        
        # Last resort: return the first 30% of the text
        # as it often contains key requirements
        return text[:int(len(text) * 0.3)]
    
    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points from text"""
        # Look for common bullet point patterns
        bullet_patterns = [
            r'•\s+(.*?)(?:\n|$)',
            r'-\s+(.*?)(?:\n|$)',
            r'\*\s+(.*?)(?:\n|$)',
            r'\d+\.\s+(.*?)(?:\n|$)',
        ]
        
        bullet_points = []
        for pattern in bullet_patterns:
            points = re.findall(pattern, text, re.DOTALL)
            bullet_points.extend(points)
        
        # Clean up points
        bullet_points = [p.strip() for p in bullet_points if p.strip()]
        
        # Remove very short points and duplicates
        bullet_points = [p for p in bullet_points if len(p) > 10]
        bullet_points = list(dict.fromkeys(bullet_points))
        
        return bullet_points
    
    def _score_and_categorize_bullet_points(self, points: List[str]) -> Dict[str, List[Tuple[str, float]]]:
        """Score and categorize bullet points by type"""
        categories = {
            'education': [],
            'technical': [],
            'experience': [],
            'soft_skills': [],
            'other': []
        }
        
        for point in points:
            # Calculate a base score
            score = 1
            point_lower = point.lower()
            
            # Determine category and adjust score
            
            # Check for education requirements
            if any(re.search(rf'\b{kw}\b', point_lower) for kw in self.education_keywords):
                category = 'education'
                score += 3
                if re.search(r'\b(?:bachelor|master|phd|degree)\b', point_lower):
                    score += 2
            
            # Check for technical skills
            elif any(re.search(rf'\b{kw}\b', point_lower) for kw in self.technical_keywords):
                category = 'technical'
                score += 2
                if re.search(r'\bexperience\b', point_lower):
                    score += 1
            
            # Check for experience requirements
            elif re.search(r'\b(?:experience|years|year of|worked with)\b', point_lower):
                category = 'experience'
                score += 2
                if re.search(r'\b\d+\+?\s*(?:year|yr)s?\b', point_lower):
                    score += 3  # Years of experience are important
            
            # Check for soft skills
            elif re.search(r'\b(?:team|collaborat|communicat|problem[\s-]solv|analytical|detail|self[\s-]motivated|leadership)\b', point_lower):
                category = 'soft_skills'
                score += 1
            
            # Other requirements
            else:
                category = 'other'
            
            # Adjust score based on length (prefer concise points)
            length = len(point)
            if 20 <= length <= 100:
                score += 1
            elif length > 200:
                score -= 1
            
            # Add to the appropriate category
            categories[category].append((point, score))
        
        # Sort each category by score
        for category in categories:
            categories[category] = sorted(categories[category], key=lambda x: x[1], reverse=True)
        
        return categories
    
    def _format_categorized_bullet_points(self, bullet_points: List[str], max_points: int = 10) -> str:
        """Format categorized bullet points into a beautiful summary"""
        # Score and categorize bullet points
        categories = self._score_and_categorize_bullet_points(bullet_points)
        
        # Start building our formatted summary
        summary = "Key Requirements:\n\n"
        
        # Track total points added
        points_added = 0
        
        # Define sections with their headers and max points per section
        sections = [
            ('education', 'Education:', 1),
            ('experience', 'Experience:', 2),
            ('technical', 'Technical Skills:', 3),
            ('soft_skills', 'Soft Skills:', 1),
            ('other', 'Other Requirements:', 1)
        ]
        
        # Add each section if it has items
        for category, header, max_cat_points in sections:
            if categories[category]:
                # Get top N points for this category
                top_points = categories[category][:max_cat_points]
                
                if top_points:
                    # Add section header
                    summary += f"{header}\n"
                    
                    # Add points
                    for point, _ in top_points:
                        # Format nicely
                        formatted_point = point.capitalize()
                        if not formatted_point.endswith('.'):
                            formatted_point += '.'
                            
                        summary += f"• {formatted_point}\n"
                    
                    # Add spacing between sections
                    summary += "\n"
                    
                    # Update count
                    points_added += len(top_points)
                    
                    # Check if we've hit our maximum
                    if points_added >= max_points:
                        break
        
        # If we haven't added any points, fall back to simple formatting
        if points_added == 0:
            return self._format_simple_bullet_points(bullet_points, max_points)
        
        return summary.strip()
    
    def _format_simple_bullet_points(self, points: List[str], max_points: int = 5) -> str:
        """Simple formatting for bullet points when categorization fails"""
        # Score points by importance
        scored_points = []
        for point in points:
            # Simple scoring based on keywords
            score = 0
            point_lower = point.lower()
            
            important_keywords = [
                'experience', 'degree', 'bachelor', 'master', 'phd',
                'required', 'essential', 'must', 'need',
                'proficiency', 'skills', 'knowledge'
            ]
            
            score += sum(2 for kw in important_keywords if kw in point_lower)
            
            # Points with years of experience are important
            if re.search(r'\b\d+\+?\s*(?:year|yr)s?\b', point_lower):
                score += 3
                
            scored_points.append((point, score))
        
        # Sort by score
        scored_points.sort(key=lambda x: x[1], reverse=True)
        
        # Format the top points
        result = "Key Requirements:\n\n"
        for point, _ in scored_points[:max_points]:
            # Format nicely
            formatted_point = point.capitalize()
            if not formatted_point.endswith('.'):
                formatted_point += '.'
                
            result += f"• {formatted_point}\n"
        
        return result.strip()
    
    def _extract_key_sentences(self, text: str, max_sentences: int = 5) -> str:
        """Extract key sentences when no bullet points are found"""
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Score sentences by keyword relevance
        scored_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10 or len(sentence) > 200:  # Skip very short or long sentences
                continue
                
            # Base score
            score = 1
            sentence_lower = sentence.lower()
            
            # Score based on important keywords
            important_keywords = [
                'experience', 'degree', 'knowledge', 'skill', 'background',
                'proficiency', 'ability', 'years', 'understanding', 'familiar',
                'required', 'essential', 'must', 'need', 'seeking'
            ]
            
            score += sum(2 for keyword in important_keywords if keyword in sentence_lower)
            
            # Education is important
            if any(kw in sentence_lower for kw in self.education_keywords):
                score += 3
                
            # Years of experience are important
            if re.search(r'\b\d+\+?\s*(?:year|yr)s?\b', sentence_lower):
                score += 3
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and select top sentences
        top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)[:max_sentences]
        
        if not top_sentences:
            return "No specific requirements extracted."
        
        # Format the result as bullet points for consistency
        result = "Key Requirements:\n\n"
        for sentence, _ in top_sentences:
            # Clean and format sentence
            formatted = sentence.strip()
            if not formatted.endswith(('.', '!', '?')):
                formatted += '.'
                
            result += f"• {formatted}\n"
        
        return result.strip()


# Singleton instance
summarizer = RequirementsSummarizer()

def summarize_job_requirements(text: str) -> str:
    """Summarize job requirements from text"""
    return summarizer.summarize(text)