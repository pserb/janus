#!/usr/bin/env python
# import_jobs.py

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path if needed
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import from the app package
from app.models import Job, Company
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("job_importer")

def get_connection_string():
    """Get database connection string based on environment"""
    # Check for environment variable
    db_url = os.getenv("DATABASE_URL")
    
    if db_url:
        return db_url
    
    # If running directly (not in Docker), use localhost
    if os.path.exists('/etc/hosts'):
        with open('/etc/hosts', 'r') as f:
            if 'db' in f.read():
                # We're in Docker
                return "postgresql://postgres:postgres@db:5432/janus"
    
    # Default to localhost
    return "postgresql://postgres:postgres@localhost:5432/janus"

def import_jobs(json_file_path):
    """Import jobs from JSON file to database"""
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        
        # Check if the JSON is in the expected format
        if isinstance(data, dict):
            if 'json' in data:
                jobs_data = data['json']
            elif 'jobs' in data:
                jobs_data = data['jobs']
            else:
                logger.error("Unexpected JSON format. Expected a dict with 'json' or 'jobs' key.")
                return
        elif isinstance(data, list):
            jobs_data = data
        else:
            logger.error("Unexpected JSON format. Expected a list or a dict with 'json' or 'jobs' key.")
            return
        
        # Track unique jobs by company+link to avoid duplicates
        unique_jobs = {}
        for job in jobs_data:
            company = job.get('company', '')
            link = job.get('job_url', '')
            if company and link:
                key = f"{company}:{link}"
                # Keep only one version of each unique job (latest in the file)
                unique_jobs[key] = job
        
        unique_jobs_list = list(unique_jobs.values())
        
        logger.info(f"Read {len(jobs_data)} jobs from JSON file, {len(unique_jobs_list)} unique jobs after deduplication")
        
        # Statistics counters
        jobs_added = 0
        jobs_updated = 0
        companies_added = 0
        
        # Create database connection
        connection_string = get_connection_string()
        logger.info(f"Connecting to database with: {connection_string}")
        
        engine = create_engine(connection_string)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Process each job in its own transaction
        for job_data in unique_jobs_list:
            db = SessionLocal()
            try:
                result = process_job(db, job_data)
                if result == "added":
                    jobs_added += 1
                elif result == "updated":
                    jobs_updated += 1
                elif result == "company_added":
                    companies_added += 1
                
                db.commit()
            except IntegrityError as e:
                db.rollback()
                logger.warning(f"Skipping duplicate job: {job_data.get('job_title')} at {job_data.get('company')} - {str(e)}")
            except Exception as e:
                db.rollback()
                logger.error(f"Error processing job {job_data.get('job_title')}: {str(e)}")
            finally:
                db.close()
        
        logger.info(f"Import complete! Added {jobs_added} jobs, updated {jobs_updated} jobs, added {companies_added} companies")
    
    except Exception as e:
        logger.error(f"Error importing jobs: {str(e)}")

def process_job(db, job_data):
    """Process a single job and add/update it in the database"""
    # Get company (or create if not exists)
    company_name = job_data.get('company')
    if not company_name:
        logger.warning("Skipping job with no company name")
        return None
    
    # Find company by name
    company = db.query(Company).filter(Company.name == company_name).first()
    
    result = None
    
    if not company:
        # Create a generic career page URL
        domain = company_name.lower().replace(' ', '').replace(',', '').replace('.', '')
        career_page_url = f"https://{domain}.com/careers"
        
        # Create new company
        company = Company(
            name=company_name,
            career_page_url=career_page_url,
            scraper_config={"type": "api", "source": "json_import"},
            last_scrape_timestamp=datetime.utcnow()
        )
        db.add(company)
        db.flush()  # Flush to get the ID
        logger.info(f"Created new company: {company_name}")
        result = "company_added"
    
    # Format the posting date
    try:
        posting_date = datetime.strptime(job_data.get('date_posted', ''), '%Y-%m-%d')
    except (ValueError, TypeError):
        posting_date = datetime.utcnow()
        logger.warning(f"Using current date for job: {job_data.get('job_title')} - invalid date format: {job_data.get('date_posted')}")
    
    # Map the job category
    category = map_category(job_data.get('category', ''))
    
    # Create job description
    description = create_description(job_data)
    
    # Create requirements summary
    requirements_summary = create_requirements_summary(job_data)
    
    # Job URL
    job_url = job_data.get('job_url', '')
    if not job_url:
        logger.warning(f"Skipping job with no URL: {job_data.get('job_title')}")
        return None
    
    # Check if job already exists
    existing_job = db.query(Job).filter(
        Job.company_id == company.id,
        Job.link == job_url
    ).first()
    
    if existing_job:
        # Update existing job
        existing_job.title = job_data.get('job_title', 'Unknown Title')
        existing_job.posting_date = posting_date
        existing_job.category = category
        existing_job.description = description
        existing_job.requirements_summary = requirements_summary
        existing_job.is_active = True
        logger.info(f"Updated job: {job_data.get('job_title')} at {company_name}")
        result = "updated"
    else:
        # Create new job
        new_job = Job(
            company_id=company.id,
            title=job_data.get('job_title', 'Unknown Title'),
            link=job_url,
            posting_date=posting_date,
            discovery_date=datetime.utcnow(),
            category=category,
            description=description,
            requirements_summary=requirements_summary,
            is_active=True
        )
        db.add(new_job)
        logger.info(f"Added new job: {job_data.get('job_title')} at {company_name}")
        result = "added"
    
    return result

def map_category(category):
    """Map job category to standardized values"""
    if not category:
        return "software"  # Default
    
    category = category.lower()
    if 'hardware' in category or 'electrical' in category:
        return 'hardware'
    else:
        return 'software'  # Default to software for all others

def create_description(job_data):
    """Create job description from job data"""
    description = job_data.get('summary', '')
    
    if job_data.get('responsibilities'):
        if description:
            description += "\n\n"
        description += "Responsibilities:\n"
        for item in job_data['responsibilities']:
            description += f"• {item}\n"
    
    # Include location and role type if available
    location = job_data.get('location')
    role_type = job_data.get('role_type')
    
    footer = ""
    if location:
        footer += f"\nLocation: {location}"
    if role_type:
        footer += f"\nRole Type: {role_type}"
    
    if footer:
        description += "\n" + footer
    
    return description

def create_requirements_summary(job_data):
    """Create requirements summary from job data"""
    summary = ""
    
    if job_data.get('minimum_qualifications'):
        summary += "Minimum Qualifications:\n"
        for item in job_data['minimum_qualifications']:
            summary += f"• {item}\n"
    
    if job_data.get('preferred_qualifications'):
        if summary:
            summary += "\n"
        summary += "Preferred Qualifications:\n"
        for item in job_data['preferred_qualifications']:
            summary += f"• {item}\n"
    
    return summary

if __name__ == "__main__":
    # Get the file path from command line argument, or use default
    file_path = sys.argv[1] if len(sys.argv) > 1 else "processed_jobs.json"
    
    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    logger.info(f"Starting import from {file_path}")
    import_jobs(file_path)