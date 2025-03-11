from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any

from ...database import get_db
from ... import crud, schemas

router = APIRouter()


@router.get("/", response_model=schemas.JobListingStats)
def get_stats(db: Session = Depends(get_db)) -> Any:
    """
    Get job listing statistics.

    Returns:
    - total_jobs: Total number of jobs in the database
    - software_jobs: Number of software engineering jobs
    - hardware_jobs: Number of hardware engineering jobs
    - new_jobs: Number of jobs posted within the last week
    - last_update_time: Timestamp of the most recently discovered job
    """
    stats = crud.get_job_statistics(db=db)
    return stats
