from pydantic import BaseModel, validator
from typing import List, Optional, Union
from datetime import datetime


# Company schemas
class CompanyBase(BaseModel):
    name: str
    website: Optional[str] = None
    career_page_url: str
    ticker: Optional[str] = None
    scrape_frequency_hours: float = 24.0
    is_active: bool = True


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    career_page_url: Optional[str] = None
    ticker: Optional[str] = None
    logo_path: Optional[str] = None
    scrape_frequency_hours: Optional[float] = None
    last_scraped: Optional[datetime] = None
    is_active: Optional[bool] = None


class CompanyInDB(CompanyBase):
    id: int
    logo_path: Optional[str] = None
    last_scraped: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Company(CompanyInDB):
    pass


# Job schemas
class JobBase(BaseModel):
    company_id: int
    title: str
    link: str
    posting_date: datetime
    category: str  # 'software' or 'hardware'
    description: Optional[str] = None
    is_active: bool = True
    job_source: Optional[str] = None
    source_job_id: Optional[str] = None
    location: Optional[str] = None
    salary_info: Optional[str] = None

    @validator("category")
    def category_must_be_valid(cls, v):
        if v not in ["software", "hardware"]:
            raise ValueError('category must be "software" or "hardware"')
        return v


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    link: Optional[str] = None
    posting_date: Optional[datetime] = None
    category: Optional[str] = None
    description: Optional[str] = None
    requirements_summary: Optional[str] = None
    is_active: Optional[bool] = None
    job_source: Optional[str] = None
    source_job_id: Optional[str] = None
    location: Optional[str] = None
    salary_info: Optional[str] = None

    @validator("category")
    def category_must_be_valid(cls, v):
        if v is not None and v not in ["software", "hardware"]:
            raise ValueError('category must be "software" or "hardware"')
        return v


class JobInDB(JobBase):
    id: int
    company_name: str
    discovery_date: datetime
    requirements_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Job(JobInDB):
    pass


# Source schemas
class SourceBase(BaseModel):
    name: str
    url: str
    crawler_type: str
    crawl_frequency_minutes: int = 60
    is_active: bool = True
    priority: int = 2  # 1 = high, 2 = medium, 3 = low


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    crawler_type: Optional[str] = None
    crawl_frequency_minutes: Optional[int] = None
    last_crawled: Optional[datetime] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class SourceInDB(SourceBase):
    id: int
    last_crawled: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Source(SourceInDB):
    pass


# Pagination schemas
class PaginatedResponse(BaseModel):
    items: List[Union[Job, Company, Source]]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobListingStats(BaseModel):
    total_jobs: int
    software_jobs: int
    hardware_jobs: int
    new_jobs: int
    last_update_time: str


# Sync info schemas
class SyncInfoBase(BaseModel):
    last_sync_timestamp: datetime
    frontend_version: Optional[str] = None
    backend_version: Optional[str] = None


class SyncInfoCreate(SyncInfoBase):
    pass


class SyncInfoUpdate(BaseModel):
    last_sync_timestamp: Optional[datetime] = None
    frontend_version: Optional[str] = None
    backend_version: Optional[str] = None


class SyncInfoInDB(SyncInfoBase):
    id: int

    class Config:
        orm_mode = True


class SyncInfo(SyncInfoInDB):
    pass
