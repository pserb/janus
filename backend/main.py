# main.py
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import asyncio
import os

from app.database import get_db, init_db
from app.models import Job as DBJob, Company as DBCompany, Base
from app.schemas import Job, JobCreate, Company, CompanyCreate, PaginatedResponse, JobListingStats
from app.crud import (
    get_jobs,
    get_job,
    create_job,
    update_job,
    delete_job,
    get_companies,
    get_company,
    create_company,
    update_company,
    delete_company,
    get_jobs_with_pagination,
    get_jobs_since_timestamp,
    get_jobs_stats
)
from app.scheduler import ScraperScheduler
from app.ml.processor import MLProcessor

app = FastAPI(
    title="Janus API",
    description="API for Janus Internship Tracker",
    version="0.1.0",
)

# CORS middleware to allow cross-origin requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global scheduler and processor instances
scraper_scheduler = None
ml_processor = None

# Initialize database and start background tasks
@app.on_event("startup")
async def startup():
    global scraper_scheduler, ml_processor
    
    # Initialize database
    init_db()
    
    # Start scheduler and processor if not running in testing mode
    if os.environ.get("TESTING") != "true":
        # Start scraper scheduler in background
        scraper_scheduler = ScraperScheduler()
        asyncio.create_task(scraper_scheduler.start())
        
        # Start ML processor in background
        ml_processor = MLProcessor()
        asyncio.create_task(ml_processor.start())

# Shutdown background tasks
@app.on_event("shutdown")
async def shutdown():
    global scraper_scheduler, ml_processor
    
    # Stop scheduler if running
    if scraper_scheduler:
        scraper_scheduler.stop()
    
    # Stop ML processor if running
    if ml_processor:
        ml_processor.stop()

# Jobs endpoints
@app.get("/jobs", response_model=PaginatedResponse[Job])
def read_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    category: Optional[str] = Query(None, regex="^(software|hardware|all)$"),
    since: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of jobs.
    
    - **page**: Page number, starting from 1
    - **page_size**: Number of items per page (max 100)
    - **category**: Filter by category (software, hardware, all)
    - **since**: ISO timestamp to get jobs added since a specific time
    """
    try:
        if since:
            # Try to parse the timestamp
            try:
                since_timestamp = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid timestamp format")
            
            # Get jobs since the specified timestamp
            jobs = get_jobs_since_timestamp(db, since_timestamp, category)
            
            # Return as a paginated response
            total = len(jobs)
            return PaginatedResponse(
                items=jobs,
                total=total,
                page=1,
                page_size=total,
                total_pages=1
            )
        else:
            # Get paginated jobs
            return get_jobs_with_pagination(db, page, page_size, category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}", response_model=Job)
def read_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job by ID"""
    db_job = get_job(db, job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job

@app.post("/jobs", response_model=Job)
def create_job_api(job: JobCreate, db: Session = Depends(get_db)):
    """Create a new job (admin only)"""
    return create_job(db=db, job=job)

@app.delete("/jobs/{job_id}", response_model=Job)
def delete_job_api(job_id: int, db: Session = Depends(get_db)):
    """Delete a job (admin only)"""
    db_job = get_job(db, job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return delete_job(db=db, job_id=job_id)

# Companies endpoints
@app.get("/companies", response_model=List[Company])
def read_companies(db: Session = Depends(get_db)):
    """Get all companies"""
    return get_companies(db)

@app.get("/companies/{company_id}", response_model=Company)
def read_company(company_id: int, db: Session = Depends(get_db)):
    """Get a specific company by ID"""
    db_company = get_company(db, company_id)
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return db_company

@app.post("/companies", response_model=Company)
def create_company_api(company: CompanyCreate, db: Session = Depends(get_db)):
    """Create a new company (admin only)"""
    return create_company(db=db, company=company)

@app.delete("/companies/{company_id}", response_model=Company)
def delete_company_api(company_id: int, db: Session = Depends(get_db)):
    """Delete a company (admin only)"""
    db_company = get_company(db, company_id)
    if db_company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return delete_company(db=db, company_id=company_id)

# Stats endpoint
@app.get("/stats", response_model=JobListingStats)
def read_stats(db: Session = Depends(get_db)):
    """Get job listing statistics"""
    return get_jobs_stats(db)

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "0.1.0"}

# Manual scrape trigger endpoint (admin only)
@app.post("/admin/trigger-scrape")
async def trigger_scrape(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger a manual scrape (admin only)"""
    from app.scraper.manager import run_scrapers
    
    # Run scrapers in background
    background_tasks.add_task(run_scrapers, db)
    
    return {"status": "Scrape job started"}

# Manual ML processing trigger endpoint (admin only)
@app.post("/admin/trigger-ml-processing")
async def trigger_ml_processing(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger manual ML processing (admin only)"""
    from app.ml.processor import MLProcessor
    
    # Run ML processing in background
    processor = MLProcessor()
    background_tasks.add_task(processor._process_jobs)
    
    return {"status": "ML processing job started"}