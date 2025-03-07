# cli.py
import asyncio
import argparse
import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("janus-cli")

async def run_scraper():
    """Run the scraper manually"""
    from app.database import SessionLocal
    from app.scraper.manager import run_scrapers
    
    logger.info("Starting manual scraper run")
    
    db = SessionLocal()
    try:
        await run_scrapers(db)
        logger.info("Scraper run completed")
    finally:
        db.close()

async def run_ml_processor():
    """Run the ML processor manually"""
    from app.database import SessionLocal
    from app.ml.processor import MLProcessor
    
    logger.info("Starting manual ML processor run")
    
    processor = MLProcessor()
    processor.db = SessionLocal()
    
    try:
        processed = await processor._process_jobs()
        logger.info(f"Processed {processed} jobs")
    finally:
        if processor.db:
            processor.db.close()

async def seed_sample_data():
    """Seed database with sample data for testing"""
    from app.database import SessionLocal, init_db
    from app.models import Company, Job
    
    logger.info("Seeding database with sample data")
    
    # Initialize database
    init_db()
    
    db = SessionLocal()
    try:
        # Create sample companies
        companies = [
            Company(
                name="Google",
                career_page_url="https://careers.google.com",
                scraper_config={"type": "api"},
                last_scrape_timestamp=datetime.utcnow()
            ),
            Company(
                name="Amazon",
                career_page_url="https://amazon.jobs",
                scraper_config={"type": "web"},
                last_scrape_timestamp=datetime.utcnow()
            ),
            Company(
                name="Microsoft",
                career_page_url="https://careers.microsoft.com",
                scraper_config={"type": "web"},
                last_scrape_timestamp=datetime.utcnow()
            )
        ]
        
        db.add_all(companies)
        db.commit()
        
        # Refresh to get IDs
        for company in companies:
            db.refresh(company)
        
        # Create sample jobs
        jobs = [
            Job(
                company_id=companies[0].id,
                title="Software Engineering Intern",
                link="https://careers.google.com/jobs/123",
                posting_date=datetime.utcnow(),
                discovery_date=datetime.utcnow(),
                category="software",
                description="""
                About the job:
                As a Software Engineering Intern, you will work on real-world projects that impact Google and its users.
                
                Requirements:
                • Currently pursuing a BS, MS, or PhD in Computer Science or related field
                • Experience in Python, Java, or C++
                • Strong problem-solving skills
                • Ability to work in a team environment
                • Knowledge of data structures and algorithms
                
                What you'll do:
                • Develop and maintain Google's services and products
                • Collaborate with experienced engineers and researchers
                • Design and implement new features
                • Write clean, maintainable code
                """,
                is_active=True
            ),
            Job(
                company_id=companies[1].id,
                title="Hardware Engineering Intern",
                link="https://amazon.jobs/jobs/456",
                posting_date=datetime.utcnow(),
                discovery_date=datetime.utcnow(),
                category="hardware",
                description="""
                Job Description:
                Amazon is looking for Hardware Engineering Interns to join our team.
                
                Basic Qualifications:
                • Currently enrolled in a Bachelor's or Master's degree in Electrical Engineering
                • Proficiency in circuit design and simulation
                • Experience with FPGA programming
                • Knowledge of digital and analog electronics
                
                Preferred Qualifications:
                • Experience with embedded systems
                • Familiarity with PCB design
                • Understanding of signal integrity
                • Programming experience in C or C++
                """,
                is_active=True
            ),
            Job(
                company_id=companies[2].id,
                title="Software Development Engineer Intern",
                link="https://careers.microsoft.com/jobs/789",
                posting_date=datetime.utcnow(),
                discovery_date=datetime.utcnow(),
                category="software",
                description="""
                Role Description:
                Join Microsoft as a Software Development Engineer Intern to work on challenging projects.
                
                Qualifications:
                • Currently pursuing a degree in Computer Science, Software Engineering, or related field
                • Solid foundation in computer science fundamentals
                • Programming experience in C#, C++, or JavaScript
                • Strong problem-solving skills
                • Passion for technology and innovation
                
                Responsibilities:
                • Design and develop features for Microsoft products
                • Write and test code in an agile environment
                • Collaborate with experienced engineers
                • Present ideas and solutions to technical problems
                """,
                is_active=True
            )
        ]
        
        db.add_all(jobs)
        db.commit()
        
        logger.info(f"Created {len(companies)} companies and {len(jobs)} jobs")
    
    finally:
        db.close()

def main():
    """Main CLI entrypoint"""
    parser = argparse.ArgumentParser(description="Janus CLI Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Scraper command
    scraper_parser = subparsers.add_parser("scrape", help="Run scraper manually")
    
    # ML processor command
    ml_parser = subparsers.add_parser("process", help="Run ML processor manually")
    
    # Seed command
    seed_parser = subparsers.add_parser("seed", help="Seed database with sample data")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run command
    if args.command == "scrape":
        asyncio.run(run_scraper())
    elif args.command == "process":
        asyncio.run(run_ml_processor())
    elif args.command == "seed":
        asyncio.run(seed_sample_data())
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()