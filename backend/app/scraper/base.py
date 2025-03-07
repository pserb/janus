# scraper/base.py
from abc import ABC, abstractmethod
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all job scrapers"""
    
    def __init__(self, company_name: str, career_page_url: str):
        self.company_name = company_name
        self.career_page_url = career_page_url
        self.logger = logging.getLogger(f"scraper.{company_name}")
    
    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape job listings from the company career page
        
        Returns:
            List[Dict[str, Any]]: List of job dictionaries with the following keys:
                - title: str - Job title
                - link: str - Application link (absolute URL)
                - posting_date: datetime - When the job was posted
                - category: str - 'software' or 'hardware'
                - description: str - Full job description
        """
        pass
    
    def classify_job_category(self, title: str, description: str = "") -> str:
        """
        Classify job as software or hardware based on title and description
        
        This is a simple implementation that can be improved with ML
        """
        title_lower = title.lower()
        desc_lower = description.lower() if description else ""
        
        # Keywords that suggest hardware roles
        hardware_keywords = [
            'hardware', 'electrical', 'electronics', 'circuit', 
            'pcb', 'fpga', 'embedded', 'firmware', 'asic', 
            'rf', 'analog', 'signal', 'systems engineer'
        ]
        
        # Check for hardware keywords in title (prioritize title matches)
        for keyword in hardware_keywords:
            if keyword in title_lower:
                return 'hardware'
        
        # Check description for hardware keywords
        if description:
            hardware_count = sum(1 for keyword in hardware_keywords if keyword in desc_lower)
            if hardware_count >= 2:  # If at least 2 hardware keywords in description
                return 'hardware'
        
        # Default to software if no hardware indicators
        return 'software'
    
    def extract_date(self, date_text: str) -> Optional[datetime]:
        """
        Extract datetime from various date formats
        
        Returns:
            datetime or None if parsing fails
        """
        # This is a placeholder - implement actual date parsing logic
        # for various formats companies might use
        try:
            # ISO format
            return datetime.fromisoformat(date_text.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            self.logger.warning(f"Failed to parse date: {date_text}")
            return datetime.utcnow()  # Default to current time
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text