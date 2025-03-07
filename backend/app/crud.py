# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import math
from typing import Optional, List

from app.models import Job as DBJob, Company as DBCompany
from app.schemas import JobCreate, CompanyCreate, PaginatedResponse, JobListingStats

# Job CRUD operations
def get_job(db: Session, job_id: int):
    return db.query(DBJob).filter(DBJob.id == job_id).first()

def get_jobs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(DBJob).offset(skip).limit(limit).all()

def create_job(db: Session, job: JobCreate):
    # Set discovery_date if not provided
    if not job.discovery_date:
        job.discovery_date = datetime.utcnow()
    
    db_job = DBJob(**job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def update_job(db: Session, job_id: int, job_data: dict):
    db_job = get_job(db, job_id)
    if db_job:
        for key, value in job_data.items():
            setattr(db_job, key, value)
        db.commit()
        db.refresh(db_job)
    return db_job

def delete_job(db: Session, job_id: int):
    db_job = get_job(db, job_id)
    if db_job:
        db.delete(db_job)
        db.commit()
    return db_job

# Company CRUD operations
def get_company(db: Session, company_id: int):
    return db.query(DBCompany).filter(DBCompany.id == company_id).first()

def get_companies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(DBCompany).offset(skip).limit(limit).all()

def create_company(db: Session, company: CompanyCreate):
    db_company = DBCompany(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def update_company(db: Session, company_id: int, company_data: dict):
    db_company = get_company(db, company_id)
    if db_company:
        for key, value in company_data.items():
            setattr(db_company, key, value)
        db.commit()
        db.refresh(db_company)
    return db_company

def delete_company(db: Session, company_id: int):
    db_company = get_company(db, company_id)
    if db_company:
        db.delete(db_company)
        db.commit()
    return db_company

# Specialized queries
def get_jobs_with_pagination(
    db: Session, 
    page: int = 1, 
    page_size: int = 50,
    category: Optional[str] = None
) -> PaginatedResponse:
    """
    Get paginated jobs with filtering options
    """
    # Define the base query
    query = db.query(
        DBJob, 
        DBCompany.name.label("company_name")
    ).join(
        DBCompany, 
        DBJob.company_id == DBCompany.id
    )
    
    # Apply category filter if specified
    if category and category != "all":
        query = query.filter(DBJob.category == category)
    
    # Filter for active jobs only
    query = query.filter(DBJob.is_active == True)
    
    # Log query for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Retrieving jobs with pagination: page={page}, page_size={page_size}, category={category}")
    
    # Order by posting date (newest first)
    query = query.order_by(desc(DBJob.posting_date))
    
    # Get total count
    total = query.count()
    logger.info(f"Total query results before pagination: {total}")
    
    total_pages = math.ceil(total / page_size)
    
    # Apply pagination
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()
    
    # Process results
    jobs = []
    for job, company_name in results:
        job_dict = {
            "id": job.id,
            "company_id": job.company_id,
            "company_name": company_name,
            "title": job.title,
            "link": job.link,
            "posting_date": job.posting_date,
            "discovery_date": job.discovery_date,
            "category": job.category,
            "description": job.description,
            "requirements_summary": job.requirements_summary,
            "is_active": job.is_active
        }
        jobs.append(job_dict)
    
    logger.info(f"Returning {len(jobs)} jobs in response")
    
    return PaginatedResponse(
        items=jobs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

def get_jobs_since_timestamp(
    db: Session, 
    timestamp: datetime,
    category: Optional[str] = None
) -> List[dict]:
    """
    Get jobs discovered since a specific timestamp
    """
    # Define the base query
    query = db.query(
        DBJob, 
        DBCompany.name.label("company_name")
    ).join(
        DBCompany, 
        DBJob.company_id == DBCompany.id
    ).filter(
        DBJob.discovery_date > timestamp
    )
    
    # Apply category filter if specified
    if category and category != "all":
        query = query.filter(DBJob.category == category)
    
    # Filter for active jobs only
    query = query.filter(DBJob.is_active == True)
    
    # Log query for debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Retrieving jobs since timestamp: {timestamp}, category={category}")
    
    # Order by posting date (newest first)
    query = query.order_by(desc(DBJob.posting_date))
    
    # Get results
    results = query.all()
    logger.info(f"Total query results for since parameter: {len(results)}")
    
    # Process results
    jobs = []
    for job, company_name in results:
        job_dict = {
            "id": job.id,
            "company_id": job.company_id,
            "company_name": company_name,
            "title": job.title,
            "link": job.link,
            "posting_date": job.posting_date,
            "discovery_date": job.discovery_date,
            "category": job.category,
            "description": job.description,
            "requirements_summary": job.requirements_summary,
            "is_active": job.is_active
        }
        jobs.append(job_dict)
    
    logger.info(f"Returning {len(jobs)} jobs since {timestamp}")
    
    return jobs

def get_jobs_stats(db: Session) -> JobListingStats:
    """Get statistics about job listings"""
    # Total jobs
    total_jobs = db.query(func.count(DBJob.id)).scalar()
    
    # Jobs by category
    software_jobs = db.query(func.count(DBJob.id)).filter(DBJob.category == "software").scalar()
    hardware_jobs = db.query(func.count(DBJob.id)).filter(DBJob.category == "hardware").scalar()
    
    # New jobs (discovered in the last 24 hours)
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    new_jobs = db.query(func.count(DBJob.id)).filter(DBJob.discovery_date > one_day_ago).scalar()
    
    # Last update time (most recent discovery_date)
    last_update = db.query(func.max(DBJob.discovery_date)).scalar() or datetime.utcnow()
    
    return JobListingStats(
        total_jobs=total_jobs,
        software_jobs=software_jobs,
        hardware_jobs=hardware_jobs,
        new_jobs=new_jobs,
        last_update_time=last_update
    )