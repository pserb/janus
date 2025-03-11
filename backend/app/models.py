from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz

from .database import Base


class Company(Base):
    """
    Model representing a company with job listings.
    """

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    website = Column(String, nullable=True)
    career_page_url = Column(String, nullable=False)
    ticker = Column(String, nullable=True, index=True)
    logo_path = Column(String, nullable=True)
    scrape_frequency_hours = Column(Float, default=24.0, nullable=False)
    last_scraped = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(pytz.utc),
        onupdate=lambda: datetime.now(pytz.utc),
    )

    # Relationships
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")


class Job(Base):
    """
    Model representing a job listing.
    """

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String, nullable=False, index=True)
    link = Column(String, nullable=False)
    posting_date = Column(DateTime, nullable=False, index=True)
    discovery_date = Column(
        DateTime, default=lambda: datetime.now(pytz.utc), nullable=False
    )
    category = Column(String, nullable=False, index=True)  # 'software' or 'hardware'
    description = Column(Text, nullable=True)
    requirements_summary = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    job_source = Column(
        String, nullable=True
    )  # Source of the job (e.g., 'linkedin', 'indeed', 'company_website')
    source_job_id = Column(
        String, nullable=True
    )  # Original ID from the source, if available
    location = Column(String, nullable=True)
    salary_info = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(pytz.utc),
        onupdate=lambda: datetime.now(pytz.utc),
    )

    # Relationships
    company = relationship("Company", back_populates="jobs")

    # Indexes
    __table_args__ = (
        Index("idx_jobs_company_source_id", "company_id", "source_job_id"),
        UniqueConstraint("company_id", "link", name="uq_company_job_link"),
    )


class Source(Base):
    """
    Model representing a job source (job board or career page).
    """

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    url = Column(String, nullable=False)
    crawler_type = Column(
        String, nullable=False
    )  # Type of crawler to use for this source
    crawl_frequency_minutes = Column(Integer, default=60, nullable=False)
    last_crawled = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=2)  # 1 = high, 2 = medium, 3 = low
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(pytz.utc),
        onupdate=lambda: datetime.now(pytz.utc),
    )


class CrawlLog(Base):
    """
    Model for logging crawl operations and their results.
    """

    __tablename__ = "crawl_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    start_time = Column(
        DateTime, default=lambda: datetime.now(pytz.utc), nullable=False
    )
    end_time = Column(DateTime, nullable=True)
    status = Column(String, nullable=False)  # 'started', 'completed', 'failed'
    jobs_found = Column(Integer, default=0)
    jobs_new = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_crawl_logs_source", "source_id"),
        Index("idx_crawl_logs_company", "company_id"),
        Index("idx_crawl_logs_status", "status"),
    )


class SyncInfo(Base):
    """
    Model for tracking synchronization information.
    """

    __tablename__ = "sync_info"

    id = Column(Integer, primary_key=True)
    last_sync_timestamp = Column(
        DateTime, default=lambda: datetime.now(pytz.utc), nullable=False
    )
    frontend_version = Column(String, nullable=True)
    backend_version = Column(String, nullable=True)
