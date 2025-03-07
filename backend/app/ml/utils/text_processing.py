# app/ml/utils/text_processing.py
import re
import logging
from typing import List, Dict, Set, Any

# Import NLTK with fallback
try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available, using simplified text processing")

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """
    Clean and normalize text by removing extra whitespace and normalizing quotes
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize different quote types
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    # Remove non-breaking spaces
    text = text.replace('\xa0', ' ')
    
    # Normalize newlines 
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text, using NLTK if available
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    if not text:
        return []
    
    if NLTK_AVAILABLE:
        return sent_tokenize(text)
    else:
        # Simple fallback for sentence tokenization
        return re.split(r'(?<=[.!?])\s+', text)

def tokenize(text: str, remove_stopwords: bool = True) -> List[str]:
    """
    Tokenize text into words, using NLTK if available
    
    Args:
        text: Input text
        remove_stopwords: Whether to remove stopwords
        
    Returns:
        List of tokens
    """
    if not text:
        return []
    
    if NLTK_AVAILABLE:
        tokens = word_tokenize(text.lower())
        if remove_stopwords:
            stop_words = set(stopwords.words('english'))
            tokens = [t for t in tokens if t.isalnum() and t not in stop_words]
        return tokens
    else:
        # Simple fallback tokenization
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens

def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """
    Extract key terms from text based on frequency and importance
    
    Args:
        text: Input text
        top_n: Number of keywords to extract
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Clean the text
    text = clean_text(text)
    
    # Tokenize
    tokens = tokenize(text, remove_stopwords=True)
    
    # Count term frequency
    term_freq = {}
    for token in tokens:
        if len(token) > 2:  # Skip very short tokens
            term_freq[token] = term_freq.get(token, 0) + 1
    
    # Sort by frequency
    sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)
    
    # Return top N terms
    return [term for term, _ in sorted_terms[:top_n]]