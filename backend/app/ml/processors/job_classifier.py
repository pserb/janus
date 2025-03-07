# app/ml/processors/job_classifier.py
import logging
import re
from typing import List, Dict, Tuple, Optional, Set, Any

# Import ML-related packages with fallback to avoid hard failures
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, using rule-based fallback")

try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available, using simplified tokenization")

logger = logging.getLogger(__name__)

class JobClassifier:
    """
    Classifies job listings as either 'software' or 'hardware'
    
    Uses a hybrid approach:
    1. First tries ML-based classification if scikit-learn is available
    2. Falls back to rule-based keyword matching if ML dependencies not available
    3. Includes both title and description text in classification
    """
    
    def __init__(self):
        """Initialize the classifier with training data and keywords"""
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
        
        # Keywords that strongly indicate job type
        self.software_keywords: Set[str] = {
            'software', 'web', 'frontend', 'backend', 'fullstack', 'full-stack', 
            'javascript', 'python', 'java', 'c++', 'react', 'node', 'django', 'flask',
            'app', 'mobile', 'ios', 'android', 'cloud', 'devops', 'ml', 'ai',
            'machine learning', 'data science', 'algorithm', 'coding', 'programmer',
            'development', 'developer', 'database', 'sql', 'nosql', 'api', 'aws',
            'azure', 'gcp', 'saas', 'webdev', 'frontend', 'backend'
        }
        
        self.hardware_keywords: Set[str] = {
            'hardware', 'electrical', 'electronics', 'circuit', 'pcb', 'fpga', 
            'embedded', 'firmware', 'asic', 'rf', 'analog', 'signal', 'systems engineer',
            'power electronics', 'digital design', 'silicon', 'semiconductor',
            'electronic', 'board', 'vlsi', 'soc', 'verification', 'verilog', 'hdl',
            'processor', 'microcontroller', 'schematic', 'layout', 'hardware', 'chip'
        }
        
        # Initialize ML classifier if scikit-learn is available
        self.ml_classifier = None
        if SKLEARN_AVAILABLE:
            self._train_classifier()
            logger.info("ML-based job classifier initialized")
        else:
            logger.info("Using keyword-based job classifier")
    
    def _train_classifier(self) -> None:
        """Train the ML classifier with the provided training data"""
        if not SKLEARN_AVAILABLE:
            return
        
        try:
            # Extract titles and labels from training data
            X_train = [title for title, _ in self.training_data]
            y_train = [label for _, label in self.training_data]
            
            # Create a pipeline with TF-IDF vectorizer and Naive Bayes classifier
            self.ml_classifier = Pipeline([
                ('vectorizer', TfidfVectorizer(lowercase=True, ngram_range=(1, 2))),
                ('classifier', MultinomialNB())
            ])
            
            # Train the classifier
            self.ml_classifier.fit(X_train, y_train)
            logger.info("Job classifier trained successfully")
        except Exception as e:
            logger.error(f"Failed to train ML classifier: {str(e)}")
            self.ml_classifier = None
    
    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words, with NLTK if available"""
        if not text:
            return []
            
        text = text.lower()
        
        if NLTK_AVAILABLE:
            # Use NLTK for better tokenization
            tokens = word_tokenize(text)
            stop_words = set(stopwords.words('english'))
            tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
            return tokens
        else:
            # Simple fallback tokenization
            tokens = re.findall(r'\b\w+\b', text.lower())
            return tokens
    
    def classify(self, title: str, description: str = "") -> str:
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
        
        # 1. First check for strong keywords in title
        for keyword in self.hardware_keywords:
            if keyword in title_lower:
                return 'hardware'
        
        for keyword in self.software_keywords:
            if keyword in title_lower:
                return 'software'
        
        # 2. Check description for keywords (if provided)
        if description:
            # Count keyword matches in description
            hardware_count = sum(1 for keyword in self.hardware_keywords if keyword in desc_lower)
            software_count = sum(1 for keyword in self.software_keywords if keyword in desc_lower)
            
            if hardware_count > software_count + 1:  # Hardware needs a stronger signal
                return 'hardware'
            elif software_count > 0:
                return 'software'  # Default to software if any software keywords found
        
        # 3. Use ML classifier if available
        if self.ml_classifier:
            try:
                # Combine title and a snippet of description
                text_to_classify = title
                if description:
                    # Add first 500 chars of description if available
                    text_to_classify += " " + description[:500]
                    
                prediction = self.ml_classifier.predict([text_to_classify])[0]
                return prediction
            except Exception as e:
                logger.error(f"Error using ML classifier: {str(e)}")
        
        # Default to software (most common category)
        return 'software'


# Create singleton instance
_classifier = JobClassifier()

def classify_job_category(title: str, description: str = "") -> str:
    """
    Classify a job as 'software' or 'hardware' based on title and description
    
    This is the main function to be called from external modules.
    
    Args:
        title: Job title
        description: Job description (optional)
        
    Returns:
        'software' or 'hardware'
    """
    return _classifier.classify(title, description)