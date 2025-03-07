# scheduler.py
import asyncio
import logging
from datetime import datetime, timedelta
import time
from sqlalchemy.orm import Session
from typing import Optional

from app.database import SessionLocal
from app.scraper.manager import run_scrapers
from app.models import Company

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScraperScheduler:
    """Scheduler for running scrapers at regular intervals"""
    
    def __init__(self):
        self.is_running = False
        self.db: Optional[Session] = None
    
    async def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        logger.info("Starting scraper scheduler")
        
        try:
            while self.is_running:
                # Get database session
                self.db = SessionLocal()
                
                # Check for companies that need to be scraped
                companies_to_scrape = self._get_companies_to_scrape()
                
                if companies_to_scrape:
                    logger.info(f"Found {len(companies_to_scrape)} companies to scrape")
                    await run_scrapers(self.db)
                else:
                    logger.info("No companies to scrape at this time")
                
                # Close database session
                if self.db:
                    self.db.close()
                    self.db = None
                
                # Sleep for a while before checking again
                await asyncio.sleep(60 * 15)  # Check every 15 minutes
        
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}")
            self.is_running = False
            if self.db:
                self.db.close()
    
    def stop(self):
        """Stop the scheduler"""
        logger.info("Stopping scraper scheduler")
        self.is_running = False
        if self.db:
            self.db.close()
            self.db = None
    
    def _get_companies_to_scrape(self):
        """Get companies that are due for scraping"""
        now = datetime.utcnow()
        
        # Get all companies
        companies = self.db.query(Company).all()
        
        # Filter companies that need to be scraped
        companies_to_scrape = []
        for company in companies:
            # If never scraped, or if it's time to scrape again
            if not company.last_scrape_timestamp or (
                company.last_scrape_timestamp + 
                timedelta(hours=company.scrape_frequency_hours) < now
            ):
                companies_to_scrape.append(company)
        
        return companies_to_scrape


async def run_scheduler():
    """Run the scheduler as a standalone process"""
    scheduler = ScraperScheduler()
    await scheduler.start()


if __name__ == "__main__":
    asyncio.run(run_scheduler())