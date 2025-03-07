# scraper/ml_manager.py
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Type, Optional
from sqlalchemy.exc import IntegrityError

# Import the scrapers
from app.scraper.base import BaseScraper
from app.scraper.company_scrapers import AppleScraper
from app.models import Company, Job
from app.schemas import JobCreate

# Import ML processor instead of rule-based processors
from app.ml.ml_job_processor import process_job_requirements, classify_job

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLScraperManager:
    """ML-based manager for all scrapers"""
    
    def __init__(self, db: Session):
        self.db = db
        self.scrapers: List[Type[BaseScraper]] = [
            AppleScraper,
            # Add more scrapers here as they're implemented
        ]
    
    async def run_all_scrapers(self):
        """Run all scrapers and store results using ML processing"""
        logger.info("Starting ML-based scraper manager")
        total_new_jobs = 0
        
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
                logger.info(f"Running scraper for {company.name}")
                jobs = await scraper.scrape()
                logger.info(f"Scraper for {company.name} found {len(jobs)} jobs")
                
                # Process and store the jobs using ML
                new_jobs_count = await self._process_jobs_with_ml(company, jobs)
                total_new_jobs += new_jobs_count
                
                # Update the company's last scrape timestamp
                company.last_scrape_timestamp = datetime.utcnow()
                self.db.commit()
                
                logger.info(f"Successfully processed {new_jobs_count} new jobs for {company.name}")
                
            except Exception as e:
                logger.error(f"Error running scraper for {scraper_class.__name__}: {str(e)}")
        
        logger.info(f"ML-based scraper manager completed with {total_new_jobs} new jobs")
        return total_new_jobs
    
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
    
    async def _process_jobs_with_ml(self, company: Company, jobs: List[Dict[str, Any]]) -> int:
        """
        Process and store jobs for a company using ML
        
        Args:
            company: Company model instance
            jobs: List of job dictionaries from scraper
            
        Returns:
            Number of new jobs added
        """
        new_jobs_count = 0
        
        # First, process each job with ML
        for job_data in jobs:
            try:
                # Skip jobs with missing essential data
                if not job_data.get("title") or not job_data.get("link"):
                    logger.warning(f"Skipping job with missing title or link: {job_data}")
                    continue
                
                # Get job description
                description = job_data.get("description", "")
                
                # Use ML to classify the job
                logger.info(f"Classifying job: {job_data['title']}")
                job_data["category"] = classify_job(job_data["title"], description)
                
                # Use ML to extract and format requirements
                logger.info(f"Processing requirements for job: {job_data['title']}")
                job_data["requirements_summary"] = process_job_requirements(description)
                
                # Check if job already exists
                existing_job = self.db.query(Job).filter(
                    Job.company_id == company.id,
                    Job.link == job_data["link"]
                ).first()
                
                if existing_job:
                    # Update existing job if needed
                    logger.info(f"Job already exists: {job_data['title']} - updating requirements")
                    
                    # Update the requirements summary
                    existing_job.requirements_summary = job_data["requirements_summary"]
                    
                    # Update other fields if needed
                    if existing_job.description != description and description:
                        existing_job.description = description
                    
                    if existing_job.category != job_data["category"]:
                        existing_job.category = job_data["category"]
                    
                    self.db.commit()
                else:
                    # Create job data
                    logger.info(f"Creating new job: {job_data['title']}")
                    job_create_data = {
                        "company_id": company.id,
                        "title": job_data["title"],
                        "link": job_data["link"],
                        "posting_date": job_data.get("posting_date", datetime.utcnow()),
                        "discovery_date": datetime.utcnow(),
                        "category": job_data["category"],
                        "description": description,
                        "requirements_summary": job_data["requirements_summary"],
                        "is_active": True
                    }
                    
                    try:
                        # Create job model instance
                        job_create = JobCreate(**job_create_data)
                        job = Job(**job_create.model_dump())
                        
                        # Add to database
                        self.db.add(job)
                        self.db.flush()  # This executes the SQL but doesn't commit yet
                        
                        # If we got here, job was successfully added
                        new_jobs_count += 1
                        
                    except IntegrityError as e:
                        # Handle unique constraint violation
                        self.db.rollback()
                        logger.warning(f"Integrity error for job {job_data['title']}: {str(e)}")
                        
                    except Exception as e:
                        # Handle other errors
                        self.db.rollback()
                        logger.error(f"Error adding job {job_data['title']}: {str(e)}")
            
            except Exception as e:
                # Handle any other errors that might occur
                logger.error(f"Unexpected error processing job {job_data.get('title', 'Unknown')}: {str(e)}")
        
        # Commit all successful additions at the end
        try:
            self.db.commit()
            logger.info(f"Successfully committed {new_jobs_count} new jobs for {company.name}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to commit job batch: {str(e)}")
        
        return new_jobs_count


async def run_ml_scrapers(db: Session):
    """Run all scrapers with ML processing - can be called from a scheduler"""
    manager = MLScraperManager(db)
    return await manager.run_all_scrapers()