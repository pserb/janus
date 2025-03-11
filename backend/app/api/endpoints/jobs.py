from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, Optional
from datetime import datetime

from ...database import get_db
from ... import crud, schemas

router = APIRouter()


@router.get("/", response_model=schemas.PaginatedResponse)
def read_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    company_id: Optional[int] = None,
    is_active: Optional[bool] = Query(True),
    since: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
) -> Any:
    """
    Retrieve paginated jobs with optional filtering.

    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page
    - **category**: Filter by job category ('software', 'hardware', or 'all')
    - **company_id**: Filter by company ID
    - **is_active**: Filter active/inactive jobs
    - **since**: Get jobs posted after this timestamp (ISO format)
    - **search**: Search in job title, description, and requirements
    """
    skip = (page - 1) * page_size

    # Process 'since' parameter if provided
    posted_after = None
    if since:
        try:
            posted_after = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid timestamp format for 'since'"
            )

    # Get jobs with filters
    jobs, total = crud.get_jobs(
        db=db,
        skip=skip,
        limit=page_size,
        company_id=company_id,
        category=category,
        is_active=is_active,
        posted_after=posted_after,
        search=search,
    )

    # Calculate pagination info
    total_pages = (total + page_size - 1) // page_size  # Ceiling division

    # Convert SQLAlchemy models to Pydantic models with company names
    job_list = []
    for job in jobs:
        job_dict = {
            "id": job.id,
            "company_id": job.company_id,
            "company_name": job.company.name,
            "title": job.title,
            "link": job.link,
            "posting_date": job.posting_date,
            "discovery_date": job.discovery_date,
            "category": job.category,
            "description": job.description,
            "requirements_summary": job.requirements_summary,
            "is_active": job.is_active,
            "job_source": job.job_source,
            "source_job_id": job.source_job_id,
            "location": job.location,
            "salary_info": job.salary_info,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }
        job_list.append(job_dict)

    return {
        "items": job_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{job_id}", response_model=schemas.Job)
def read_job(job_id: int, db: Session = Depends(get_db)) -> Any:
    """
    Get a specific job by ID.
    """
    job = crud.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Add company name to the job
    company = crud.get_company(db=db, company_id=job.company_id)
    job_dict = {
        "id": job.id,
        "company_id": job.company_id,
        "company_name": company.name if company else "Unknown",
        "title": job.title,
        "link": job.link,
        "posting_date": job.posting_date,
        "discovery_date": job.discovery_date,
        "category": job.category,
        "description": job.description,
        "requirements_summary": job.requirements_summary,
        "is_active": job.is_active,
        "job_source": job.job_source,
        "source_job_id": job.source_job_id,
        "location": job.location,
        "salary_info": job.salary_info,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }

    return job_dict


@router.post("/", response_model=schemas.Job)
def create_job(job: schemas.JobCreate, db: Session = Depends(get_db)) -> Any:
    """
    Create a new job.
    """
    try:
        db_job = crud.create_job(db=db, job=job)

        # Add company name to response
        company = crud.get_company(db=db, company_id=db_job.company_id)
        job_dict = {
            "id": db_job.id,
            "company_id": db_job.company_id,
            "company_name": company.name if company else "Unknown",
            "title": db_job.title,
            "link": db_job.link,
            "posting_date": db_job.posting_date,
            "discovery_date": db_job.discovery_date,
            "category": db_job.category,
            "description": db_job.description,
            "requirements_summary": db_job.requirements_summary,
            "is_active": db_job.is_active,
            "job_source": db_job.job_source,
            "source_job_id": db_job.source_job_id,
            "location": db_job.location,
            "salary_info": db_job.salary_info,
            "created_at": db_job.created_at,
            "updated_at": db_job.updated_at,
        }

        return job_dict
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{job_id}", response_model=schemas.Job)
def update_job(
    job_id: int, job: schemas.JobUpdate, db: Session = Depends(get_db)
) -> Any:
    """
    Update a job.
    """
    db_job = crud.update_job(db=db, job_id=job_id, job=job)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Add company name to response
    company = crud.get_company(db=db, company_id=db_job.company_id)
    job_dict = {
        "id": db_job.id,
        "company_id": db_job.company_id,
        "company_name": company.name if company else "Unknown",
        "title": db_job.title,
        "link": db_job.link,
        "posting_date": db_job.posting_date,
        "discovery_date": db_job.discovery_date,
        "category": db_job.category,
        "description": db_job.description,
        "requirements_summary": db_job.requirements_summary,
        "is_active": db_job.is_active,
        "job_source": db_job.job_source,
        "source_job_id": db_job.source_job_id,
        "location": db_job.location,
        "salary_info": db_job.salary_info,
        "created_at": db_job.created_at,
        "updated_at": db_job.updated_at,
    }

    return job_dict


@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)) -> Any:
    """
    Delete a job.
    """
    success = crud.delete_job(db=db, job_id=job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"message": "Job deleted successfully"}


@router.get("/recent/since", response_model=list[schemas.Job])
def get_jobs_since(
    timestamp: str, limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)
) -> Any:
    """
    Get jobs discovered after a specific timestamp.
    """
    try:
        since_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    jobs = crud.get_jobs_since(db=db, timestamp=since_timestamp, limit=limit)

    # Convert SQLAlchemy models to Pydantic models with company names
    job_list = []
    for job in jobs:
        job_dict = {
            "id": job.id,
            "company_id": job.company_id,
            "company_name": job.company.name,
            "title": job.title,
            "link": job.link,
            "posting_date": job.posting_date,
            "discovery_date": job.discovery_date,
            "category": job.category,
            "description": job.description,
            "requirements_summary": job.requirements_summary,
            "is_active": job.is_active,
            "job_source": job.job_source,
            "source_job_id": job.source_job_id,
            "location": job.location,
            "salary_info": job.salary_info,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }
        job_list.append(job_dict)

    return job_list