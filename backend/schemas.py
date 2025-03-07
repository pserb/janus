# schemas.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Generic, TypeVar, Dict, Any
from datetime import datetime

# Base models
class CompanyBase(BaseModel):
    name: str
    career_page_url: str
    scrape_frequency_hours: Optional[int] = 24

class JobBase(BaseModel):
    title: str
    link: str
    category: str
    description: Optional[str] = None
    requirements_summary: Optional[str] = None

# Create models
class CompanyCreate(CompanyBase):
    scraper_config: Optional[Dict[str, Any]] = None

class JobCreate(JobBase):
    company_id: int
    posting_date: datetime
    discovery_date: Optional[datetime] = None
    is_active: Optional[bool] = True

    @validator('posting_date', 'discovery_date', pre=True)
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value

# Read models
class Company(CompanyBase):
    id: int
    scraper_config: Optional[Dict[str, Any]] = None
    last_scrape_timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True

class Job(JobBase):
    id: int
    company_id: int
    company_name: Optional[str] = None
    posting_date: datetime
    discovery_date: datetime
    is_active: bool

    class Config:
        from_attributes = True

# Pagination
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

# Stats
class JobListingStats(BaseModel):
    total_jobs: int
    software_jobs: int
    hardware_jobs: int
    new_jobs: int
    last_update_time: datetime