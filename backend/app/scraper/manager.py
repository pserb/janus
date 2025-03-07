# scraper/manager.py
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Type, Optional
from sqlalchemy.exc import IntegrityError

from app.scraper.base import BaseScraper
from app.scraper.company_scrapers import AppleScraper
from app.models import Company, Job
from app.schemas import JobCreate
from app.scraper.ml_job_processor import classify_job, extract_requirements

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
        job_batch = []
        
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
                
                # Use ML to extract requirements summary
                if "requirements_summary" not in job_data or not job_data["requirements_summary"]:
                    job_data["requirements_summary"] = extract_requirements(description)
                
                # Create job data
                job_create_data = {
                    "company_id": company.id,
                    "title": job_data["title"],
                    "link": job_data["link"],
                    "posting_date": job_data["posting_date"],
                    "discovery_date": datetime.utcnow(),
                    "category": job_data["category"],
                    "description": description,
                    "requirements_summary": job_data.get("requirements_summary", ""),
                    "is_active": True
                }
                
                job_batch.append(job_create_data)
                
            except Exception as e:
                logger.error(f"Error processing job {job_data.get('title', 'Unknown')}: {str(e)}")
        
        # Now process jobs in bulk with proper error handling
        jobs_added = 0
        for job_data in job_batch:
            try:
                # First, check if job already exists to avoid unique constraint violations
                existing_job = self.db.query(Job).filter(
                    Job.company_id == company.id,
                    Job.link == job_data["link"]
                ).first()
                
                if existing_job:
                    # Job already exists
                    logger.debug(f"Job already exists: {job_data['title']} - {job_data['link']}")
                    
                    # Optionally update fields if needed
                    # For example:
                    # if existing_job.description != job_data["description"]:
                    #     existing_job.description = job_data["description"]
                    #     existing_job.requirements_summary = job_data["requirements_summary"]
                    #     self.db.commit()
                    #     logger.info(f"Updated existing job: {job_data['title']} at {company.name}")
                else:
                    # Create new job
                    try:
                        # Create job model instance
                        job_create = JobCreate(**job_data)
                        job = Job(**job_create.model_dump())
                        
                        # Add to database
                        self.db.add(job)
                        self.db.flush()  # This executes the SQL but doesn't commit yet
                        
                        # If we got here, job was successfully added
                        jobs_added += 1
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
            logger.info(f"Successfully added {jobs_added} new jobs for {company.name}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to commit job batch: {str(e)}")


async def run_scrapers(db: Session):
    """Run all scrapers - can be called from a scheduler"""
    manager = ScraperManager(db)
    await manager.run_all_scrapers()