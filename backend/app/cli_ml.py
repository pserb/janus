# cli_ml.py
import asyncio
import argparse
import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("janus-ml-cli")

async def run_ml_scraper():
    """Run the ML-based scraper"""
    from app.database import SessionLocal
    from app.scraper.ml_manager import run_ml_scrapers
    
    logger.info("Starting ML scraper run")
    
    db = SessionLocal()
    try:
        new_jobs = await run_ml_scrapers(db)
        logger.info(f"ML scraper run completed with {new_jobs} new jobs")
    finally:
        db.close()

async def process_existing_jobs():
    """Reprocess existing jobs with ML"""
    from app.database import SessionLocal
    from app.models import Job
    from app.ml.ml_job_processor import process_job_requirements, classify_job
    
    logger.info("Starting reprocessing of existing jobs with ML")
    
    db = SessionLocal()
    try:
        # Get all jobs
        jobs = db.query(Job).filter(
            Job.description.isnot(None),
            Job.description != ""
        ).all()
        
        logger.info(f"Found {len(jobs)} jobs to process")
        
        processed_count = 0
        for job in jobs:
            try:
                logger.info(f"Processing job {job.id}: {job.title}")
                
                # Classify job with ML
                job.category = classify_job(job.title, job.description)
                
                # Process requirements with ML
                job.requirements_summary = process_job_requirements(job.description)
                
                # Commit changes
                db.commit()
                
                processed_count += 1
                
                # Prevent CPU overload
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing job {job.id}: {str(e)}")
                db.rollback()
        
        logger.info(f"Successfully processed {processed_count} jobs")
        
    finally:
        db.close()

async def process_company_jobs(company_name: str):
    """Reprocess jobs for a specific company with ML"""
    from app.database import SessionLocal
    from app.models import Job, Company
    from app.ml.ml_job_processor import process_job_requirements, classify_job
    
    logger.info(f"Starting reprocessing of {company_name} jobs with ML")
    
    db = SessionLocal()
    try:
        # Get company
        company = db.query(Company).filter(Company.name == company_name).first()
        
        if not company:
            logger.error(f"Company not found: {company_name}")
            return
        
        # Get all jobs for this company
        jobs = db.query(Job).filter(
            Job.company_id == company.id,
            Job.description.isnot(None),
            Job.description != ""
        ).all()
        
        logger.info(f"Found {len(jobs)} jobs to process for {company_name}")
        
        processed_count = 0
        for job in jobs:
            try:
                logger.info(f"Processing job {job.id}: {job.title}")
                
                # Classify job with ML
                job.category = classify_job(job.title, job.description)
                
                # Process requirements with ML
                job.requirements_summary = process_job_requirements(job.description)
                
                # Commit changes
                db.commit()
                
                processed_count += 1
                
                # Prevent CPU overload
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing job {job.id}: {str(e)}")
                db.rollback()
        
        logger.info(f"Successfully processed {processed_count} jobs for {company_name}")
        
    finally:
        db.close()

def main():
    """Main CLI entrypoint"""
    parser = argparse.ArgumentParser(description="Janus ML-Based CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # ML Scraper command
    scraper_parser = subparsers.add_parser("scrape", help="Run ML scraper")
    
    # Process existing jobs command
    process_parser = subparsers.add_parser("process", help="Process existing jobs with ML")
    
    # Process company jobs command
    company_parser = subparsers.add_parser("company", help="Process jobs for a specific company")
    company_parser.add_argument("name", help="Company name")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run command
    if args.command == "scrape":
        asyncio.run(run_ml_scraper())
    elif args.command == "process":
        asyncio.run(process_existing_jobs())
    elif args.command == "company":
        asyncio.run(process_company_jobs(args.name))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()