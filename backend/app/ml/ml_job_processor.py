# ml/ml_job_processor.py
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
import tensorflow as tf
from tensorflow.keras.layers import Dense, Embedding, GlobalAveragePooling1D, Input
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.optimizers import Adam
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM, TFAutoModelForSequenceClassification

# Ensure nltk dependencies
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

logger = logging.getLogger(__name__)

class MLJobProcessor:
    """Process job listings using pure ML approaches without regex patterns"""
    
    def __init__(self):
        """Initialize ML models"""
        logger.info("Initializing ML Job Processor")
        
        # Initialize sentence transformer for text embeddings
        try:
            from sentence_transformers import SentenceTransformer
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence transformer model")
        except ImportError:
            logger.warning("SentenceTransformer not available, falling back to TF-IDF")
            self.sentence_model = None
            
        # Init NLP pipeline components
        self.init_nlp_components()
    
    def init_nlp_components(self):
        """Initialize all NLP pipeline components"""
        
        # Text summarization model
        logger.info("Initializing summarization model")
        try:
            # Try to load a local model or use Hugging Face pipeline
            self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn", 
                                      device=-1)  # -1 means CPU
            logger.info("Loaded summarization model")
        except Exception as e:
            logger.warning(f"Failed to load summarization model: {e}")
            self.summarizer = None
            
        # Text classification for categorizing requirements
        logger.info("Initializing text classification model")
        try:
            self.text_classifier = pipeline("text-classification", 
                                          model="distilbert-base-uncased-finetuned-sst-2-english",
                                          device=-1)
            logger.info("Loaded text classification model")
        except Exception as e:
            logger.warning(f"Failed to load text classification model: {e}")
            self.text_classifier = None
            
        # Zero-shot classification for categorizing requirement types
        logger.info("Initializing zero-shot classification model")
        try:
            self.zero_shot_classifier = pipeline("zero-shot-classification", 
                                               model="facebook/bart-large-mnli", 
                                               device=-1)
            logger.info("Loaded zero-shot classification model")
        except Exception as e:
            logger.warning(f"Failed to load zero-shot classification model: {e}")
            self.zero_shot_classifier = None
        
        # Initialize BERT-based tokenizer and model for text similarity
        logger.info("Initializing BERT tokenizer")
        try:
            self.bert_tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
            logger.info("Loaded BERT tokenizer")
        except Exception as e:
            logger.warning(f"Failed to load BERT tokenizer: {e}")
            self.bert_tokenizer = None
            
        # TF-IDF vectorizer as fallback
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Create stop words set
        self.stop_words = set(stopwords.words('english'))
    
    def extract_requirements_section(self, text: str) -> str:
        """
        Extract the requirements section from job description using ML
        
        Args:
            text: Full job description text
            
        Returns:
            Requirements section text
        """
        if not text:
            return ""
        
        # Split into sentences
        sentences = sent_tokenize(text)
        
        if not sentences:
            return ""
            
        # If we have sentence embeddings model
        if self.sentence_model:
            # Create embeddings for all sentences
            embeddings = self.sentence_model.encode(sentences)
            
            # Create a query for requirements-related content
            queries = [
                "job requirements",
                "qualifications needed",
                "skills required",
                "what you'll need",
                "what we're looking for",
                "minimum requirements",
                "preferred qualifications"
            ]
            query_embeddings = self.sentence_model.encode(queries)
            
            # Average the query embeddings
            avg_query = np.mean(query_embeddings, axis=0)
            
            # Compute similarity scores
            similarities = np.dot(embeddings, avg_query) / (
                np.linalg.norm(embeddings, axis=1) * np.linalg.norm(avg_query)
            )
            
            # Find sentences with high similarity to requirements
            threshold = 0.5  # Adjust this threshold based on experimentation
            req_sentences_idx = np.where(similarities > threshold)[0]
            
            # If no sentences above threshold, use top N sentences
            if len(req_sentences_idx) < 3:
                req_sentences_idx = np.argsort(similarities)[-5:]  # Get top 5
            
            # Sort indices to maintain original order
            req_sentences_idx = sorted(req_sentences_idx)
            
            # Extract requirement sentences
            req_sentences = [sentences[i] for i in req_sentences_idx]
            
            return " ".join(req_sentences)
        
        else:
            # Fallback: Use TF-IDF and clustering
            try:
                # Create TF-IDF matrix
                tfidf_matrix = self.tfidf_vectorizer.fit_transform([" ".join(sentences)])
                
                # Calculate the similarity of each sentence to requirement keywords
                req_keywords = [
                    "requirements", "qualifications", "skills", "experience", 
                    "degree", "education", "background", "knowledge", "familiar"
                ]
                keyword_matrix = self.tfidf_vectorizer.transform(req_keywords)
                
                # Calculate similarity scores
                similarity_scores = (tfidf_matrix * keyword_matrix.T).toarray().flatten()
                
                # Get sentences with highest scores
                top_sentence_indices = np.argsort(similarity_scores)[-10:]
                req_sentences = [sentences[i] for i in sorted(top_sentence_indices)]
                
                return " ".join(req_sentences)
            except:
                # Last resort - return first 30% of text
                return text[:int(len(text) * 0.3)]
    
    def extract_key_requirements(self, text: str, max_length: int = 1000) -> List[str]:
        """
        Extract key requirement statements from text
        
        Args:
            text: Requirements section text
            max_length: Maximum total character length
            
        Returns:
            List of key requirement statements
        """
        if not text:
            return []
        
        # Split into sentences
        sentences = sent_tokenize(text)
        
        if not sentences:
            return []
        
        if self.zero_shot_classifier:
            # Define requirement categories
            requirement_categories = [
                "education requirements", 
                "experience requirements",
                "technical skills",
                "soft skills",
                "job responsibilities",
                "not a requirement"  # To filter out non-requirements
            ]
            
            # Filter out too short sentences
            valid_sentences = [s for s in sentences if len(s) > 15]
            
            if not valid_sentences:
                return []
            
            # Classify each sentence
            classified_sentences = []
            
            for sentence in valid_sentences:
                try:
                    result = self.zero_shot_classifier(
                        sentence, 
                        candidate_labels=requirement_categories,
                        multi_label=False
                    )
                    
                    # Get top category and score
                    top_category = result['labels'][0]
                    top_score = result['scores'][0]
                    
                    # Only keep if it's likely a requirement (not "not a requirement")
                    if top_category != "not a requirement" and top_score > 0.5:
                        classified_sentences.append({
                            'text': sentence,
                            'category': top_category,
                            'score': top_score
                        })
                except Exception as e:
                    logger.warning(f"Error classifying sentence '{sentence}': {str(e)}")
            
            # Sort by score within each category
            by_category = {}
            for sent in classified_sentences:
                category = sent['category']
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(sent)
            
            # Sort each category by score
            for category in by_category:
                by_category[category] = sorted(
                    by_category[category], 
                    key=lambda x: x['score'], 
                    reverse=True
                )
            
            # Select top requirements from each category
            selected_requirements = []
            
            # Priority order for categories
            category_priority = [
                "education requirements", 
                "experience requirements",
                "technical skills",
                "soft skills",
                "job responsibilities"
            ]
            
            # Get top items from each category based on priority
            category_limits = {
                "education requirements": 2,
                "experience requirements": 3,
                "technical skills": 4,
                "soft skills": 2,
                "job responsibilities": 3
            }
            
            total_len = 0
            for category in category_priority:
                if category in by_category:
                    # Take top N from this category
                    for item in by_category[category][:category_limits[category]]:
                        if total_len + len(item['text']) <= max_length:
                            selected_requirements.append(item['text'])
                            total_len += len(item['text'])
            
            return selected_requirements
            
        else:
            # Fallback: Use TF-IDF importance
            try:
                # Create TF-IDF matrix
                tfidf_matrix = self.tfidf_vectorizer.fit_transform(sentences)
                
                # Get importance score for each sentence
                importance_scores = tfidf_matrix.sum(axis=1).A1
                
                # Get sentences with highest scores
                top_sentence_indices = np.argsort(importance_scores)[-10:]
                
                # Return in original order
                selected_requirements = [sentences[i] for i in sorted(top_sentence_indices)]
                
                return selected_requirements
            except:
                # Last resort - return all sentences
                return sentences
    
    def categorize_requirements(self, requirements: List[str]) -> Dict[str, List[str]]:
        """
        Categorize requirements by type
        
        Args:
            requirements: List of requirement statements
            
        Returns:
            Dictionary mapping category to list of requirements
        """
        if not requirements:
            return {}
        
        if self.zero_shot_classifier:
            # Define detailed requirement categories
            requirement_categories = [
                "education", 
                "experience",
                "technical skills",
                "soft skills",
                "other"
            ]
            
            categorized = {category: [] for category in requirement_categories}
            
            for req in requirements:
                try:
                    result = self.zero_shot_classifier(
                        req, 
                        candidate_labels=requirement_categories,
                        multi_label=False
                    )
                    
                    # Get top category
                    top_category = result['labels'][0]
                    categorized[top_category].append(req)
                except Exception as e:
                    logger.warning(f"Error categorizing requirement '{req}': {str(e)}")
                    categorized["other"].append(req)
            
            return categorized
        else:
            # Fallback: Use keyword-based categorization
            categorized = {
                "education": [],
                "experience": [],
                "technical skills": [],
                "soft skills": [],
                "other": []
            }
            
            # Simple keyword-based categorization
            education_keywords = ["degree", "bachelor", "master", "phd", "education", "graduate"]
            experience_keywords = ["experience", "years", "worked", "previous"]
            tech_skills_keywords = ["programming", "software", "technical", "development", "code", "language", "hardware", "design"]
            soft_skills_keywords = ["communication", "teamwork", "problem solving", "analytical", "interpersonal"]
            
            for req in requirements:
                req_lower = req.lower()
                
                # Check education
                if any(keyword in req_lower for keyword in education_keywords):
                    categorized["education"].append(req)
                # Check experience
                elif any(keyword in req_lower for keyword in experience_keywords):
                    categorized["experience"].append(req)
                # Check technical skills
                elif any(keyword in req_lower for keyword in tech_skills_keywords):
                    categorized["technical skills"].append(req)
                # Check soft skills
                elif any(keyword in req_lower for keyword in soft_skills_keywords):
                    categorized["soft skills"].append(req)
                # Default to other
                else:
                    categorized["other"].append(req)
            
            return categorized
    
    def format_requirements_summary(self, categorized_requirements: Dict[str, List[str]]) -> str:
        """
        Format categorized requirements into a nice summary
        
        Args:
            categorized_requirements: Dictionary mapping category to list of requirements
            
        Returns:
            Formatted summary string
        """
        if not categorized_requirements:
            return "No specific requirements listed."
        
        # Start with header
        summary = "Key Requirements:\n\n"
        
        # Define category display names and order
        categories_order = [
            "education",
            "experience",
            "technical skills",
            "soft skills",
            "other"
        ]
        
        category_display_names = {
            "education": "Education:",
            "experience": "Experience:",
            "technical skills": "Technical Skills:",
            "soft skills": "Soft Skills:",
            "other": "Other Requirements:"
        }
        
        # Process each category
        for category in categories_order:
            requirements = categorized_requirements.get(category, [])
            
            if requirements:
                # Add category header
                summary += f"{category_display_names[category]}\n"
                
                # Add each requirement as a bullet point
                for req in requirements:
                    # Clean up the requirement
                    req = req.strip()
                    if not req.endswith(('.', '!', '?')):
                        req += '.'
                    
                    # Convert first character to uppercase
                    if req and req[0].islower():
                        req = req[0].upper() + req[1:]
                    
                    # Add as bullet point
                    summary += f"• {req}\n"
                
                # Add spacing between categories
                summary += "\n"
        
        return summary.strip()
    
    def process_job_description(self, description: str) -> str:
        """
        Process a job description to extract and format requirements
        
        Args:
            description: Full job description text
            
        Returns:
            Formatted requirements summary
        """
        try:
            # Extract requirements section
            requirements_section = self.extract_requirements_section(description)
            
            if not requirements_section:
                return "No specific requirements listed."
            
            # Extract key requirements
            key_requirements = self.extract_key_requirements(requirements_section)
            
            if not key_requirements:
                return "No specific requirements listed."
            
            # Categorize requirements
            categorized_requirements = self.categorize_requirements(key_requirements)
            
            # Format summary
            summary = self.format_requirements_summary(categorized_requirements)
            
            return summary
        
        except Exception as e:
            logger.error(f"Error processing job description: {str(e)}")
            return "Failed to process requirements."
    
    def classify_job_category(self, title: str, description: str = "") -> str:
        """
        Classify a job as 'software' or 'hardware' using ML
        
        Args:
            title: Job title
            description: Job description
            
        Returns:
            'software' or 'hardware'
        """
        # Combine title and a snippet of description
        text = title
        if description:
            # Add first 500 chars of description if available
            text += " " + description[:500]
        
        if self.zero_shot_classifier:
            try:
                # Use zero-shot classification
                result = self.zero_shot_classifier(
                    text,
                    candidate_labels=["software engineering", "hardware engineering"],
                    multi_label=False
                )
                
                # Get top category
                top_category = result['labels'][0]
                
                if top_category == "software engineering":
                    return "software"
                else:
                    return "hardware"
            except Exception as e:
                logger.warning(f"Error classifying job: {str(e)}")
        
        # Fallback to TF-IDF and keyword based approach
        try:
            # Software vs Hardware keywords
            software_keywords = [
                "software", "developer", "web", "app", "application", "cloud", "full-stack",
                "backend", "frontend", "data scientist", "machine learning", "devops",
                "python", "java", "javascript", "react", "node", "database"
            ]
            
            hardware_keywords = [
                "hardware", "electrical", "electronic", "circuit", "pcb", "fpga",
                "embedded", "firmware", "asic", "analog", "digital design", "rf",
                "signal", "power", "systems engineer"
            ]
            
            # Count keyword matches
            text_lower = text.lower()
            software_count = sum(1 for kw in software_keywords if kw in text_lower)
            hardware_count = sum(1 for kw in hardware_keywords if kw in text_lower)
            
            # Return category with more matches
            if hardware_count > software_count:
                return "hardware"
            else:
                # Default to software (more common)
                return "software"
                
        except Exception as e:
            logger.error(f"Error in classify_job_category fallback: {str(e)}")
            # Default to software if all else fails
            return "software"


# Create singleton instance
ml_processor = MLJobProcessor()

def process_job_requirements(description: str) -> str:
    """Process job requirements using ML"""
    return ml_processor.process_job_description(description)

def classify_job(title: str, description: str = "") -> str:
    """Classify job as software or hardware using ML"""
    return ml_processor.classify_job_category(title, description)