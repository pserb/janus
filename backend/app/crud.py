from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, timedelta
import pytz
from typing import List, Optional, Dict, Any, Tuple

from . import models, schemas


# Company CRUD operations
def get_company(db: Session, company_id: int) -> Optional[models.Company]:
    return db.query(models.Company).filter(models.Company.id == company_id).first()


def get_company_by_name(db: Session, name: str) -> Optional[models.Company]:
    return db.query(models.Company).filter(models.Company.name == name).first()


def get_companies(
    db: Session, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
) -> List[models.Company]:
    query = db.query(models.Company)

    if is_active is not None:
        query = query.filter(models.Company.is_active == is_active)

    return query.order_by(models.Company.name).offset(skip).limit(limit).all()


def create_company(db: Session, company: schemas.CompanyCreate) -> models.Company:
    db_company = models.Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company


def update_company(
    db: Session, company_id: int, company: schemas.CompanyUpdate
) -> Optional[models.Company]:
    db_company = (
        db.query(models.Company).filter(models.Company.id == company_id).first()
    )
    if not db_company:
        return None

    update_data = company.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_company, key, value)

    db.commit()
    db.refresh(db_company)
    return db_company


def delete_company(db: Session, company_id: int) -> bool:
    db_company = (
        db.query(models.Company).filter(models.Company.id == company_id).first()
    )
    if not db_company:
        return False

    db.delete(db_company)
    db.commit()
    return True


# Job CRUD operations
def get_job(db: Session, job_id: int) -> Optional[models.Job]:
    return db.query(models.Job).filter(models.Job.id == job_id).first()


def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[int] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    posted_after: Optional[datetime] = None,
    search: Optional[str] = None,
) -> Tuple[List[models.Job], int]:
    query = db.query(models.Job)

    # Apply filters
    if company_id:
        query = query.filter(models.Job.company_id == company_id)

    if category:
        if category.lower() != "all":
            query = query.filter(models.Job.category == category)

    if is_active is not None:
        query = query.filter(models.Job.is_active == is_active)

    if posted_after:
        query = query.filter(models.Job.posting_date >= posted_after)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.Job.title.ilike(search_term),
                models.Job.description.ilike(search_term),
                models.Job.requirements_summary.ilike(search_term),
            )
        )

    # Get total count for pagination
    total = query.count()

    # Apply pagination
    jobs = (
        query.order_by(models.Job.posting_date.desc()).offset(skip).limit(limit).all()
    )

    return jobs, total


def create_job(db: Session, job: schemas.JobCreate) -> models.Job:
    # Get company name for the job
    company = (
        db.query(models.Company).filter(models.Company.id == job.company_id).first()
    )

    if not company:
        raise ValueError(f"Company with ID {job.company_id} not found")

    # Create job object with company name
    job_data = job.dict()
    db_job = models.Job(**job_data)

    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return db_job


def update_job(
    db: Session, job_id: int, job: schemas.JobUpdate
) -> Optional[models.Job]:
    db_job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not db_job:
        return None

    update_data = job.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_job, key, value)

    db.commit()
    db.refresh(db_job)
    return db_job


def delete_job(db: Session, job_id: int) -> bool:
    db_job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not db_job:
        return False

    db.delete(db_job)
    db.commit()
    return True


def get_job_statistics(db: Session) -> Dict[str, Any]:
    total_jobs = db.query(func.count(models.Job.id)).scalar()

    software_jobs = (
        db.query(func.count(models.Job.id))
        .filter(models.Job.category == "software")
        .scalar()
    )

    hardware_jobs = (
        db.query(func.count(models.Job.id))
        .filter(models.Job.category == "hardware")
        .scalar()
    )

    # Jobs posted in the last week are considered "new"
    one_week_ago = datetime.now(pytz.utc) - timedelta(days=7)
    new_jobs = (
        db.query(func.count(models.Job.id))
        .filter(models.Job.posting_date >= one_week_ago)
        .scalar()
    )

    # Get the most recent job's discovery time
    latest_job = db.query(models.Job).order_by(models.Job.discovery_date.desc()).first()

    last_update_time = (
        latest_job.discovery_date if latest_job else datetime.now(pytz.utc)
    )

    return {
        "total_jobs": total_jobs,
        "software_jobs": software_jobs,
        "hardware_jobs": hardware_jobs,
        "new_jobs": new_jobs,
        "last_update_time": last_update_time.isoformat(),
    }


def get_jobs_since(
    db: Session, timestamp: datetime, limit: int = 100
) -> List[models.Job]:
    return (
        db.query(models.Job)
        .filter(models.Job.discovery_date > timestamp)
        .order_by(models.Job.discovery_date.desc())
        .limit(limit)
        .all()
    )


# Source CRUD operations
def get_source(db: Session, source_id: int) -> Optional[models.Source]:
    return db.query(models.Source).filter(models.Source.id == source_id).first()


def get_source_by_name(db: Session, name: str) -> Optional[models.Source]:
    return db.query(models.Source).filter(models.Source.name == name).first()


def get_sources(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    priority: Optional[int] = None,
) -> List[models.Source]:
    query = db.query(models.Source)

    if is_active is not None:
        query = query.filter(models.Source.is_active == is_active)

    if priority is not None:
        query = query.filter(models.Source.priority == priority)

    return (
        query.order_by(models.Source.priority, models.Source.name)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_source(db: Session, source: schemas.SourceCreate) -> models.Source:
    db_source = models.Source(**source.dict())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


def update_source(
    db: Session, source_id: int, source: schemas.SourceUpdate
) -> Optional[models.Source]:
    db_source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not db_source:
        return None

    update_data = source.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_source, key, value)

    db.commit()
    db.refresh(db_source)
    return db_source


def delete_source(db: Session, source_id: int) -> bool:
    db_source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not db_source:
        return False

    db.delete(db_source)
    db.commit()
    return True


def get_sources_for_crawling(db: Session) -> List[models.Source]:
    """
    Get sources that are due for crawling based on their crawl frequency.
    """
    query = db.query(models.Source).filter(models.Source.is_active == True)

    # For sources that have been crawled before
    sources_crawled = query.filter(models.Source.last_crawled.isnot(None)).all()
    sources_to_crawl = []

    for source in sources_crawled:
        # Check if it's time to crawl this source
        time_diff = datetime.now(pytz.utc) - source.last_crawled
        if time_diff.total_seconds() / 60 >= source.crawl_frequency_minutes:
            sources_to_crawl.append(source)

    # For sources that have never been crawled
    sources_never_crawled = query.filter(models.Source.last_crawled.is_(None)).all()
    sources_to_crawl.extend(sources_never_crawled)

    # Sort by priority
    sources_to_crawl.sort(key=lambda x: x.priority)

    return sources_to_crawl


def get_companies_for_crawling(db: Session) -> List[models.Company]:
    """
    Get companies that are due for crawling based on their scrape frequency.
    """
    query = db.query(models.Company).filter(models.Company.is_active == True)

    # For companies that have been scraped before
    companies_scraped = query.filter(models.Company.last_scraped.isnot(None)).all()
    companies_to_crawl = []

    for company in companies_scraped:
        # Check if it's time to crawl this company
        time_diff = datetime.now(pytz.utc) - company.last_scraped
        if time_diff.total_seconds() / 3600 >= company.scrape_frequency_hours:
            companies_to_crawl.append(company)

    # For companies that have never been scraped
    companies_never_scraped = query.filter(models.Company.last_scraped.is_(None)).all()
    companies_to_crawl.extend(companies_never_scraped)

    return companies_to_crawl


# Crawl log operations
def create_crawl_log(
    db: Session, source_id: Optional[int] = None, company_id: Optional[int] = None
) -> models.CrawlLog:
    db_log = models.CrawlLog(
        source_id=source_id, company_id=company_id, status="started"
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def update_crawl_log(
    db: Session,
    log_id: int,
    status: str,
    jobs_found: int = 0,
    jobs_new: int = 0,
    error_message: Optional[str] = None,
) -> models.CrawlLog:
    db_log = db.query(models.CrawlLog).filter(models.CrawlLog.id == log_id).first()
    if not db_log:
        return None

    db_log.status = status
    db_log.end_time = datetime.now(pytz.utc)
    db_log.jobs_found = jobs_found
    db_log.jobs_new = jobs_new
    if error_message:
        db_log.error_message = error_message

    db.commit()
    db.refresh(db_log)
    return db_log


# SyncInfo operations
def get_sync_info(db: Session) -> models.SyncInfo:
    sync_info = db.query(models.SyncInfo).first()
    if not sync_info:
        # Create initial sync info if not exists
        sync_info = models.SyncInfo(
            id=1,
            last_sync_timestamp=datetime.now(pytz.utc),
            frontend_version="0.1.0",
            backend_version="0.1.0",
        )
        db.add(sync_info)
        db.commit()
        db.refresh(sync_info)
    return sync_info


def update_sync_info(db: Session, sync_info: schemas.SyncInfoUpdate) -> models.SyncInfo:
    db_sync_info = db.query(models.SyncInfo).first()
    if not db_sync_info:
        # Create initial sync info if not exists
        sync_data = sync_info.dict(exclude_unset=True)
        if not sync_data.get("last_sync_timestamp"):
            sync_data["last_sync_timestamp"] = datetime.now(pytz.utc)

        db_sync_info = models.SyncInfo(id=1, **sync_data)
        db.add(db_sync_info)
    else:
        # Update existing sync info
        update_data = sync_info.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_sync_info, key, value)

    db.commit()
    db.refresh(db_sync_info)
    return db_sync_info
