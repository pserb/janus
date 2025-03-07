# models.py
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    career_page_url = Column(String, nullable=False)
    scraper_config = Column(JSON, nullable=True)
    last_scrape_timestamp = Column(DateTime, nullable=True)
    scrape_frequency_hours = Column(Integer, default=24)

    # Relationship
    jobs = relationship("Job", back_populates="company")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    posting_date = Column(DateTime, nullable=False)
    discovery_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    category = Column(String, nullable=False)  # software or hardware
    description = Column(Text, nullable=True)
    requirements_summary = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Unique constraint on company_id and link
    __table_args__ = (
        # SQLAlchemy constraint syntax
        {"UniqueConstraint('company_id', 'link')"},
    )

    # Relationship
    company = relationship("Company", back_populates="jobs")