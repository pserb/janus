# scraper/manager.py
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Type
from sqlalchemy.exc import IntegrityError

from app.scraper.base import BaseScraper
from app.scraper.company_scrapers import AppleScraper
from app.models import Company, Job
from app.schemas import JobCreate

# Import the updated ML functions
from app.ml.summarizer import summarize_job_requirements
from app.scraper.ml_job_processor import classify_job

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperManager:
    """Manager for all scrapers"""
    
    def __init__(self, db: Session):
        self.db = db
        self.scrapers: List[Type[BaseScraper]] = [
            AppleScraper,
            # Add more scrapers here as they're implemented
        ]
    
    async def run_all_scrapers(self):
        """Run all scrapers and store results"""
        logger.info("Starting scraper manager")
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
                
                # Process and store the jobs
                new_jobs_count = await self._process_jobs(company, jobs)
                total_new_jobs += new_jobs_count
                
                # Update the company's last scrape timestamp
                company.last_scrape_timestamp = datetime.utcnow()
                self.db.commit()
                
                logger.info(f"Successfully processed {new_jobs_count} new jobs for {company.name}")
                
            except Exception as e:
                logger.error(f"Error running scraper for {scraper_class.__name__}: {str(e)}")
        
        logger.info(f"Scraper manager completed with {total_new_jobs} new jobs")
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
    
    async def _process_jobs(self, company: Company, jobs: List[Dict[str, Any]]) -> int:
        """Process and store jobs for a company"""
        new_jobs_count = 0
        
        # First, gather all job data with appropriate processing
        for job_data in jobs:
            try:
                # Skip jobs with missing essential data
                if not job_data.get("title") or not job_data.get("link"):
                    logger.warning(f"Skipping job with missing title or link: {job_data}")
                    continue
                
                # Skip "Share this role" entries (additional check)
                if job_data["title"].lower() == "share this role." or job_data["title"].lower() == "share this role":
                    logger.info(f"Skipping 'Share this role' entry: {job_data.get('link')}")
                    continue
                
                # Skip jobs with suspicious titles
                non_job_indicators = ["share", "favorite", "login", "sign in", "apply", "submit"]
                if any(indicator in job_data["title"].lower() for indicator in non_job_indicators) and len(job_data["title"]) < 30:
                    logger.info(f"Skipping suspicious non-job title: {job_data['title']}")
                    continue
                
                # Get job description
                description = job_data.get("description", "")
                
                # Use ML to classify the job if not already classified
                if "category" not in job_data or not job_data["category"]:
                    job_data["category"] = classify_job(job_data["title"], description)
                
                # Use improved ML to extract requirements summary
                if "requirements_summary" not in job_data or not job_data["requirements_summary"]:
                    # Use the improved summarizer from app.ml.summarizer
                    job_data["requirements_summary"] = summarize_job_requirements(description)
                
                # Check if job already exists
                existing_job = self.db.query(Job).filter(
                    Job.company_id == company.id,
                    Job.link == job_data["link"]
                ).first()
                
                if existing_job:
                    # Update existing job if needed
                    if (not existing_job.requirements_summary or 
                        len(existing_job.requirements_summary) < 30 or
                        "No specific requirements" in existing_job.requirements_summary):
                        
                        # Update requirements summary
                        existing_job.requirements_summary = job_data["requirements_summary"]
                        self.db.commit()
                        logger.info(f"Updated requirements summary for existing job: {job_data['title']} at {company.name}")
                else:
                    # Create job data
                    job_create_data = {
                        "company_id": company.id,
                        "title": job_data["title"],
                        "link": job_data["link"],
                        "posting_date": job_data["posting_date"],
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
                        logger.info(f"Created new job: {job_data['title']} at {company.name}")
                        
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


async def run_scrapers(db: Session):
    """Run all scrapers - can be called from a scheduler"""
    manager = ScraperManager(db)
    return await manager.run_all_scrapers()