# scraper/ml_job_processor.py
import re
import logging
from typing import Dict, List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)

class JobClassifier:
    """ML-based classifier for job postings"""
    
    def __init__(self):
        """Initialize the classifier with training data"""
        # Sample training data for software vs hardware jobs
        self.training_data = [
            # Software engineering job examples
            ("Software Engineer Intern", "software"),
            ("Frontend Developer", "software"),
            ("Backend Developer", "software"),
            ("Full Stack Engineer", "software"),
            ("Web Developer Intern", "software"),
            ("Mobile App Developer", "software"),
            ("iOS Engineer", "software"),
            ("Android Developer Intern", "software"),
            ("Machine Learning Engineer", "software"),
            ("Data Scientist", "software"),
            ("DevOps Engineer", "software"),
            ("Site Reliability Engineer", "software"),
            ("Cloud Engineer", "software"),
            ("Software Development Engineer", "software"),
            ("Python Developer", "software"),
            ("JavaScript Engineer", "software"),
            ("React Developer", "software"),
            ("QA Engineer (Software)", "software"),
            ("Software Test Engineer", "software"),
            
            # Hardware engineering job examples
            ("Hardware Engineer Intern", "hardware"),
            ("Electrical Engineer", "hardware"),
            ("PCB Designer", "hardware"),
            ("FPGA Engineer", "hardware"),
            ("Embedded Systems Engineer", "hardware"),
            ("IC Design Engineer", "hardware"),
            ("RF Engineer", "hardware"),
            ("ASIC Design Intern", "hardware"),
            ("Power Electronics Engineer", "hardware"),
            ("Hardware Test Engineer", "hardware"),
            ("Systems Engineer (Hardware)", "hardware"),
            ("Digital Design Engineer", "hardware"),
            ("Analog Circuit Designer", "hardware"),
            ("Electronics Engineer", "hardware"),
            ("Signal Integrity Engineer", "hardware"),
            ("Hardware Validation Engineer", "hardware"),
            ("Firmware Engineer", "hardware"),
            ("Mixed Signal Engineer", "hardware"),
            ("Silicon Design Engineer", "hardware"),
        ]
        
        # Additional keywords that strongly indicate job type
        self.software_keywords = [
            'software', 'web', 'frontend', 'backend', 'fullstack', 'full-stack', 
            'javascript', 'python', 'java', 'c++', 'react', 'node', 'django', 'flask',
            'app', 'mobile', 'ios', 'android', 'cloud', 'devops', 'ml', 'ai',
            'machine learning', 'data science', 'algorithm', 'coding'
        ]
        
        self.hardware_keywords = [
            'hardware', 'electrical', 'electronics', 'circuit', 'pcb', 'fpga', 
            'embedded', 'firmware', 'asic', 'rf', 'analog', 'signal', 'systems engineer',
            'power electronics', 'digital design', 'silicon', 'semiconductor'
        ]
        
        # Create and train the classifier
        self._train_classifier()
    
    def _train_classifier(self):
        """Train the ML classifier with the provided training data"""
        # Extract titles and labels from training data
        X_train = [title for title, _ in self.training_data]
        y_train = [label for _, label in self.training_data]
        
        # Create a pipeline with TF-IDF vectorizer and Naive Bayes classifier
        self.classifier = Pipeline([
            ('vectorizer', TfidfVectorizer(lowercase=True, ngram_range=(1, 2))),
            ('classifier', MultinomialNB())
        ])
        
        # Train the classifier
        self.classifier.fit(X_train, y_train)
        logger.info("Job classifier trained successfully")
    
    def classify_job(self, title: str, description: str = "") -> str:
        """
        Classify a job as 'software' or 'hardware' based on title and description
        
        Args:
            title: Job title
            description: Job description (optional)
            
        Returns:
            'software' or 'hardware'
        """
        # Lowercase for consistency
        title_lower = title.lower()
        desc_lower = description.lower() if description else ""
        
        # If title or description contains strong keywords, categorize immediately
        for keyword in self.hardware_keywords:
            if keyword in title_lower:
                return 'hardware'
        
        for keyword in self.software_keywords:
            if keyword in title_lower:
                return 'software'
        
        # If no strong keywords in title, check description
        if description:
            hardware_count = sum(1 for keyword in self.hardware_keywords if keyword in desc_lower)
            software_count = sum(1 for keyword in self.software_keywords if keyword in desc_lower)
            
            if hardware_count > software_count + 1:  # Hardware needs to win by 2 or more
                return 'hardware'
            elif software_count > 0:
                return 'software'  # Default to software if any software keywords found
        
        # Use ML classifier if keyword approach is indecisive
        try:
            prediction = self.classifier.predict([title])[0]
            return prediction
        except Exception as e:
            logger.error(f"Error using ML classifier: {e}")
            
            # Default to software if classifier fails
            return 'software'


class RequirementExtractor:
    """ML-based extractor for job requirements"""
    
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
        
        logger.info("Requirement extractor initialized")
    
    def extract_requirements(self, description: str, max_bullets: int = 5) -> str:
        """Extract key requirements from job description"""
        if not description:
            return "No requirements specified."
        
        # Try to find the requirements section
        requirements_section = self._find_requirements_section(description)
        
        if not requirements_section:
            # If no specific section found, use the whole description
            requirements_section = description
        
        # Extract bullet points
        bullet_points = self._extract_bullet_points(requirements_section)
        
        if bullet_points:
            # Score and select the most important bullet points
            scored_points = self._score_bullet_points(bullet_points)
            
            # Format the selected bullet points
            return self._format_bullet_points(scored_points[:max_bullets])
        else:
            # If no bullet points, extract key sentences
            return self._extract_key_sentences(requirements_section, max_sentences=3)
    
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
            points = re.findall(pattern, text)
            bullet_points.extend([p.strip() for p in points if p.strip()])
        
        return bullet_points
    
    def _score_bullet_points(self, bullet_points: List[str]) -> List[Tuple[str, float]]:
        """Score bullet points by relevance to requirements"""
        scored_points = []
        
        for point in bullet_points:
            # Calculate a score based on important keywords
            score = sum(3 for keyword in self.important_keywords if re.search(r'\b{}\b'.format(re.escape(keyword)), point.lower()))
            
            # Add score based on length (preference for concise points, but not too short)
            length = len(point)
            if 40 <= length <= 200:
                score += 2
            elif 20 <= length < 40 or 200 < length <= 300:
                score += 1
            
            # Higher score for points with numbers (years of experience, etc.)
            if re.search(r'\d+', point):
                score += 2
            
            # Higher score for education requirements
            if re.search(r'(?:degree|bachelor|master|phd|bs|ms|b\.s\.|m\.s\.)', point.lower()):
                score += 3
            
            scored_points.append((point, score))
        
        # Sort by score (descending)
        return sorted(scored_points, key=lambda x: x[1], reverse=True)
    
    def _format_bullet_points(self, scored_points: List[Tuple[str, float]]) -> str:
        """Format the bullet points into a summary"""
        if not scored_points:
            return "No specific requirements extracted."
        
        result = "Key Requirements:\n"
        for point, _ in scored_points:
            result += f"• {point}\n"
        
        return result.strip()
    
    def _extract_key_sentences(self, text: str, max_sentences: int = 3) -> str:
        """Extract key sentences when no bullet points are found"""
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Score sentences by keyword relevance
        scored_sentences = []
        for sentence in sentences:
            if len(sentence) < 10:  # Skip very short sentences
                continue
                
            score = sum(2 for keyword in self.important_keywords if re.search(r'\b{}\b'.format(re.escape(keyword)), sentence.lower()))
            
            # Prefer sentences with numbers (years of experience, etc.)
            if re.search(r'\d+', sentence):
                score += 1
            
            # Prefer sentences with education requirements
            if re.search(r'(?:degree|bachelor|master|phd|bs|ms|b\.s\.|m\.s\.)', sentence.lower()):
                score += 2
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and select top sentences
        top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)[:max_sentences]
        
        if not top_sentences:
            return "No specific requirements extracted."
        
        # Format the result
        result = "Key Requirements:\n"
        for sentence, _ in top_sentences:
            result += f"• {sentence.strip()}\n"
        
        return result.strip()


# Singleton instances
job_classifier = JobClassifier()
requirement_extractor = RequirementExtractor()

def classify_job(title: str, description: str = "") -> str:
    """Classify a job as software or hardware"""
    return job_classifier.classify_job(title, description)

def extract_requirements(description: str) -> str:
    """Extract key requirements from job description"""
    return requirement_extractor.extract_requirements(description)