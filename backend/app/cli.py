#!/usr/bin/env python
"""
Command-line interface for Janus backend operations.
"""

import asyncio
import logging
from datetime import datetime
import pytz
import click
import os
import sys
import random
from typing import Dict, List, Any, Optional

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.database import SessionLocal
from app.scraper.manager import ScraperManager
from app.ml.processor import process_all_jobs, process_single_batch
from app.ml.logo_fetcher import fetch_all_logos
from app import crud, models, schemas
from app.cli_init import init_sources as init_sources_func

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("janus-cli")

# Click command group
@click.group()
def cli():
    """Janus backend CLI tools."""
    pass

# Init sources command (NO sample data)
@cli.command()
def init_sources():
    """Initialize database with real companies and sources (NO fake data)."""
    companies_added, sources_added = init_sources_func()
    click.echo(f"Initialized database with {companies_added} real companies and {sources_added} job sources.")
    click.echo("No fake job data was added.")

# Scrape command
@cli.command()
@click.option('--source-id', type=int, help='Scrape a specific source by ID')
@click.option('--company-id', type=int, help='Scrape a specific company by ID')
@click.option('--all', is_flag=True, help='Scrape all available sources and companies')
def scrape(source_id, company_id, all):
    """Run job scrapers."""
    db = SessionLocal()
    try:
        manager = ScraperManager(db)
        
        if source_id:
            logger.info(f"Scraping source with ID: {source_id}")
            asyncio.run(manager.run_specific_source(source_id))
        elif company_id:
            logger.info(f"Scraping company with ID: {company_id}")
            asyncio.run(manager.run_specific_company(company_id))
        else:
            logger.info("Scraping all sources and companies")
            jobs_found, new_jobs = asyncio.run(manager.run_all_scrapers())
            logger.info(f"Scraping complete: {jobs_found} jobs found, {new_jobs} new jobs")
    finally:
        db.close()

# Process command
@cli.command()
@click.option('--limit', type=int, default=100, help='Maximum number of jobs to process')
@click.option('--all', is_flag=True, help='Process all unprocessed jobs')
def process(limit, all):
    """Run job requirement processor."""
    if all:
        logger.info("Processing all unprocessed jobs")
        processed = asyncio.run(process_all_jobs())
        logger.info(f"Processing complete: {processed} jobs processed")
    else:
        logger.info(f"Processing up to {limit} jobs")
        processed = asyncio.run(process_single_batch(limit))
        logger.info(f"Processing complete: {processed} jobs processed")

# Logos command
@cli.command()
@click.option('--limit', type=int, default=20, help='Maximum number of companies to fetch logos for')
@click.option('--all', is_flag=True, help='Fetch logos for all companies without logos')
def logos(limit, all):
    """Fetch company logos."""
    if all:
        logger.info("Fetching logos for all companies without logos")
        fetched = asyncio.run(fetch_all_logos())
        logger.info(f"Logo fetching complete: {fetched} logos fetched")
    else:
        logger.info(f"Fetching logos for up to {limit} companies")
        from app.ml.logo_fetcher import fetch_logos_batch
        fetched = asyncio.run(fetch_logos_batch(limit))
        logger.info(f"Logo fetching complete: {fetched} logos fetched")

# Stats command
@cli.command()
def stats():
    """Show job statistics."""
    db = SessionLocal()
    try:
        stats = crud.get_job_statistics(db)
        
        click.echo("\n=== Janus Job Statistics ===\n")
        click.echo(f"Total Jobs: {stats['total_jobs']}")
        click.echo(f"Software Jobs: {stats['software_jobs']}")
        click.echo(f"Hardware Jobs: {stats['hardware_jobs']}")
        click.echo(f"New Jobs (last 7 days): {stats['new_jobs']}")
        click.echo(f"Last Update: {stats['last_update_time']}")
        
    finally:
        db.close()

# Seed command (clearly marked as DEMO DATA)
@cli.command()
@click.option('--count', type=int, default=20, help='Number of sample jobs to create')
@click.confirmation_option(prompt='⚠️ WARNING: This will add FAKE DEMO DATA to your database. Are you sure?')
def seed(count):
    """Seed database with FAKE SAMPLE DATA (for demo/testing only)."""
    db = SessionLocal()
    try:
        # Create sample companies
        companies = [
            {"name": "Google", "website": "https://www.google.com", "career_page_url": "https://careers.google.com/", "ticker": "GOOGL"},
            {"name": "Microsoft", "website": "https://www.microsoft.com", "career_page_url": "https://careers.microsoft.com/", "ticker": "MSFT"},
            {"name": "Apple", "website": "https://www.apple.com", "career_page_url": "https://www.apple.com/careers/", "ticker": "AAPL"},
            {"name": "Amazon", "website": "https://www.amazon.com", "career_page_url": "https://www.amazon.jobs/", "ticker": "AMZN"},
            {"name": "Meta", "website": "https://www.meta.com", "career_page_url": "https://www.meta.com/careers/", "ticker": "META"},
            {"name": "Netflix", "website": "https://www.netflix.com", "career_page_url": "https://jobs.netflix.com/", "ticker": "NFLX"},
            {"name": "Nvidia", "website": "https://www.nvidia.com", "career_page_url": "https://www.nvidia.com/en-us/about-nvidia/careers/", "ticker": "NVDA"},
            {"name": "Intel", "website": "https://www.intel.com", "career_page_url": "https://jobs.intel.com/", "ticker": "INTC"},
            {"name": "AMD", "website": "https://www.amd.com", "career_page_url": "https://jobs.amd.com/", "ticker": "AMD"},
            {"name": "IBM", "website": "https://www.ibm.com", "career_page_url": "https://www.ibm.com/employment/", "ticker": "IBM"},
        ]
        
        company_ids = []
        for company_data in companies:
            # Check if company already exists
            existing = crud.get_company_by_name(db, company_data["name"])
            if existing:
                company_ids.append(existing.id)
                continue
            
            # Create company
            company = crud.create_company(db, schemas.CompanyCreate(**company_data))
            company_ids.append(company.id)
            logger.info(f"Created company: {company.name}")
        
        # Create sample jobs
        jobs_created = 0
        
        # Job titles and descriptions
        software_titles = [
            "Software Engineer Intern",
            "Software Developer Intern",
            "Frontend Engineer Intern",
            "Backend Developer Intern",
            "Full Stack Developer Intern",
            "Mobile App Developer Intern",
            "iOS Developer Intern",
            "Android Developer Intern",
            "Web Developer Intern",
            "DevOps Engineer Intern",
            "Cloud Engineer Intern",
            "ML Engineer Intern",
            "Data Scientist Intern",
            "Entry-Level Software Engineer",
            "Junior Software Developer",
            "New Grad Software Engineer",
        ]
        
        hardware_titles = [
            "Hardware Engineer Intern",
            "Electrical Engineer Intern",
            "FPGA Engineer Intern",
            "ASIC Design Engineer Intern",
            "Embedded Systems Engineer Intern",
            "Firmware Engineer Intern",
            "Computer Architecture Intern",
            "Chip Design Intern",
            "Hardware Verification Intern",
            "Entry-Level Hardware Engineer",
            "Junior Electrical Engineer",
            "New Grad Hardware Engineer",
        ]
        
        software_description = """
About the Role:
We're looking for a talented Software Engineering Intern to join our team. As a software engineering intern, you'll work on real projects and collaborate with experienced engineers to gain valuable industry experience.

Responsibilities:
• Work on real projects with our engineering team
• Develop, test, and deploy code to production
• Participate in code reviews and design discussions
• Collaborate with cross-functional teams
• Present your work to the broader team

Requirements:
• Currently pursuing a bachelor's or master's degree in Computer Science, Software Engineering, or a related field
• Strong knowledge of data structures and algorithms
• Experience with one or more programming languages (Python, Java, C++, JavaScript)
• Excellent problem-solving skills
• Strong communication and teamwork skills
• Ability to work in a fast-paced environment

Benefits:
• Competitive internship compensation
• Mentorship from experienced engineers
• Hands-on experience with industry tools and practices
• Exposure to cutting-edge technology
• Potential for full-time opportunities after graduation
"""
        
        hardware_description = """
About the Role:
We're looking for a talented Hardware Engineering Intern to join our team. As a hardware engineering intern, you'll work on real projects and collaborate with experienced engineers to gain valuable industry experience.

Responsibilities:
• Contribute to the design and validation of hardware components
• Assist in prototyping and testing hardware systems
• Analyze test data and document results
• Collaborate with cross-functional teams
• Present your work to the broader team

Requirements:
• Currently pursuing a bachelor's or master's degree in Electrical Engineering, Computer Engineering, or a related field
• Understanding of digital logic design and computer architecture
• Experience with hardware description languages (Verilog/VHDL) is a plus
• Familiarity with circuit simulation tools
• Strong problem-solving skills
• Excellent communication and teamwork abilities

Benefits:
• Competitive internship compensation
• Mentorship from experienced engineers
• Hands-on experience with industry tools and practices
• Exposure to cutting-edge technology
• Potential for full-time opportunities after graduation
"""
        
        # Create jobs
        for i in range(count):
            try:
                # Randomly select company
                company_id = random.choice(company_ids)
                
                # Randomly select job category and title
                category = random.choice(["software", "hardware"])
                if category == "software":
                    title = random.choice(software_titles)
                    description = software_description
                else:
                    title = random.choice(hardware_titles)
                    description = hardware_description
                
                # Generate random dates within the last 30 days
                days_ago = random.randint(0, 30)
                posting_date = datetime.now(pytz.utc) - timedelta(days=days_ago)
                
                # Create job
                job_data = {
                    "company_id": company_id,
                    "title": title + " [DEMO DATA]",  # Clearly mark as demo data
                    "link": f"https://example.com/jobs/{i}",
                    "posting_date": posting_date,
                    "category": category,
                    "description": "⚠️ THIS IS DEMO DATA FOR TESTING ONLY ⚠️\n\n" + description,
                    "is_active": True,
                    "job_source": "demo_data",
                    "location": random.choice(["Remote", "San Francisco, CA", "Seattle, WA", "New York, NY", "Austin, TX"]),
                }
                
                job = crud.create_job(db, schemas.JobCreate(**job_data))
                jobs_created += 1
                
            except Exception as e:
                logger.error(f"Error creating sample job: {str(e)}")
        
        logger.info(f"Created {jobs_created} sample demo jobs (clearly marked as demo data)")
        
        # Process job requirements
        logger.info("Processing job requirements...")
        processed = asyncio.run(process_all_jobs())
        logger.info(f"Processed {processed} jobs")
        
        # Fetch logos
        logger.info("Fetching company logos...")
        fetched = asyncio.run(fetch_all_logos())
        logger.info(f"Fetched {fetched} logos")
        
    finally:
        db.close()

# Clear command
@cli.command()
@click.option('--jobs', is_flag=True, help='Clear all jobs')
@click.option('--companies', is_flag=True, help='Clear all companies')
@click.option('--all', is_flag=True, help='Clear all data')
@click.confirmation_option(prompt='Are you sure you want to clear data?')
def clear(jobs, companies, all):
    """Clear database data."""
    db = SessionLocal()
    try:
        if all or jobs:
            # Delete all jobs
            job_count = db.query(models.Job).delete()
            db.commit()
            logger.info(f"Deleted {job_count} jobs")
        
        if all or companies:
            # Delete all companies
            company_count = db.query(models.Company).delete()
            db.commit()
            logger.info(f"Deleted {company_count} companies")
        
    finally:
        db.close()

# Main entry point
if __name__ == "__main__":
    cli()