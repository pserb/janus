# scraper/manager.py
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Type, Optional

from app.scraper.base import BaseScraper
from app.scraper.example_company import ExampleCompanyScraper, GoogleScraper
from app.models import Company, Job
from app.schemas import JobCreate

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperManager:
    """Manager for all scrapers"""
    
    def __init__(self, db: Session):
        self.db = db
        self.scrapers: List[Type[BaseScraper]] = [
            ExampleCompanyScraper,
            GoogleScraper,
            # Add more scrapers here as they're implemented
        ]
    
    async def run_all_scrapers(self):
        """Run all scrapers and store results"""
        logger.info("Starting scraper manager")
        
        for scraper_class in self.scrapers:
            try:
                # Initialize scraper
                scraper = scraper_class()
                
                # Find or create company in the database
                company = self._get_or_create_company(
                    name=scraper.company_name,
                    career_page_url=scraper.career_page_url
                )
                
                # Run the scraper
                jobs = await scraper.scrape()
                
                # Process and store the jobs
                await self._process_jobs(company, jobs)
                
                # Update the company's last scrape timestamp
                company.last_scrape_timestamp = datetime.utcnow()
                self.db.commit()
                
            except Exception as e:
                logger.error(f"Error running scraper for {scraper_class.__name__}: {str(e)}")
    
    def _get_or_create_company(self, name: str, career_page_url: str) -> Company:
        """Get or create a company in the database"""
        company = self.db.query(Company).filter(Company.name == name).first()
        
        if not company:
            logger.info(f"Creating new company: {name}")
            company = Company(
                name=name,
                career_page_url=career_page_url
            )
            self.db.add(company)
            self.db.commit()
        
        return company
    
    async def _process_jobs(self, company: Company, jobs: List[Dict[str, Any]]):
        """Process and store jobs for a company"""
        for job_data in jobs:
            try:
                # Check if job already exists (by company_id and link)
                existing_job = self.db.query(Job).filter(
                    Job.company_id == company.id,
                    Job.link == job_data["link"]
                ).first()
                
                if existing_job:
                    # Job already exists, update it if needed
                    logger.debug(f"Job already exists: {job_data['title']}")
                    # You could update the job here if needed
                else:
                    # Create new job
                    job_create = JobCreate(
                        company_id=company.id,
                        title=job_data["title"],
                        link=job_data["link"],
                        posting_date=job_data["posting_date"],
                        discovery_date=datetime.utcnow(),
                        category=job_data["category"],
                        description=job_data.get("description", ""),
                        requirements_summary=job_data.get("requirements_summary", "")
                    )
                    
                    # Create job in database
                    job = Job(**job_create.model_dump())
                    self.db.add(job)
                    logger.info(f"Created new job: {job_data['title']} at {company.name}")
            
            except Exception as e:
                logger.error(f"Error processing job {job_data.get('title', 'Unknown')}: {str(e)}")
        
        self.db.commit()


async def run_scrapers(db: Session):
    """Run all scrapers - can be called from a scheduler"""
    manager = ScraperManager(db)
    await manager.run_all_scrapers()