# ml/processor.py
import asyncio
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database import SessionLocal
from app.models import Job
from app.ml.summarizer import summarize_job_requirements

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLProcessor:
    """Processes job descriptions using ML models"""
    
    def __init__(self):
        self.is_running = False
        self.db = None
    
    async def start(self):
        """Start the processor"""
        if self.is_running:
            logger.warning("ML processor is already running")
            return
        
        self.is_running = True
        logger.info("Starting ML processor")
        
        try:
            while self.is_running:
                # Get database session
                self.db = SessionLocal()
                
                # Process unprocessed jobs
                processed_count = await self._process_jobs()
                
                if processed_count > 0:
                    logger.info(f"Processed {processed_count} jobs")
                else:
                    logger.info("No jobs to process")
                
                # Close database session
                if self.db:
                    self.db.close()
                    self.db = None
                
                # Sleep for a while before checking again
                await asyncio.sleep(60 * 10)  # Check every 10 minutes
        
        except Exception as e:
            logger.error(f"Error in ML processor: {str(e)}")
            self.is_running = False
            if self.db:
                self.db.close()
    
    def stop(self):
        """Stop the processor"""
        logger.info("Stopping ML processor")
        self.is_running = False
        if self.db:
            self.db.close()
            self.db = None
    
    async def _process_jobs(self) -> int:
        """
        Process jobs without requirement summaries
        
        Returns:
            int: Number of jobs processed
        """
        # Get jobs that need processing
        jobs = self.db.query(Job).filter(
            Job.requirements_summary.is_(None),
            Job.description.isnot(None)
        ).limit(50).all()
        
        processed_count = 0
        
        for job in jobs:
            try:
                # Summarize requirements
                summary = summarize_job_requirements(job.description)
                
                # Update job with summary
                job.requirements_summary = summary
                self.db.commit()
                
                processed_count += 1
                
                # Prevent CPU overload
                await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Error processing job {job.id}: {str(e)}")
                self.db.rollback()
        
        return processed_count


async def run_ml_processor():
    """Run the ML processor as a standalone process"""
    processor = MLProcessor()
    await processor.start()


if __name__ == "__main__":
    asyncio.run(run_ml_processor())