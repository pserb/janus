# app/ml/processor.py
import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import traceback

from app.database import SessionLocal
from app.models import Job
from app.ml.processors.job_classifier import classify_job_category
from app.ml.processors.requirements_extractor import extract_requirements_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLProcessor:
    """
    Main ML processor that handles job classification and requirements summarization
    
    This processor identifies jobs that need processing and applies ML models to:
    1. Classify jobs as software or hardware
    2. Extract and summarize key requirements from job descriptions
    """
    
    def __init__(self):
        """Initialize the ML processor"""
        self.is_running = False
        self.db = None
        logger.info("ML processor initialized")
        
    async def start(self):
        """Start the processor service loop"""
        if self.is_running:
            logger.warning("ML processor is already running")
            return
        
        self.is_running = True
        logger.info("Starting ML processor service")
        
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
            logger.error(traceback.format_exc())
            self.is_running = False
            if self.db:
                self.db.close()
    
    def stop(self):
        """Stop the processor service"""
        logger.info("Stopping ML processor service")
        self.is_running = False
        if self.db:
            self.db.close()
            self.db = None
    
    def _get_jobs_needing_processing(self) -> List[Job]:
        """
        Get jobs that need ML processing
        
        Returns jobs that:
        1. Have a description but no requirements summary
        2. Have a description but poor-quality requirements summary
        3. Have an unclassified category
        """
        try:
            query = self.db.query(Job).filter(
                Job.description.isnot(None),  # Must have a description
                Job.description != "",        # Description can't be empty
            ).filter(
                # Missing or poor requirements summary
                (Job.requirements_summary.is_(None)) |
                (Job.requirements_summary == "") |
                (Job.requirements_summary == "No specific requirements extracted.") |
                (Job.requirements_summary == "Failed to summarize requirements.") |
                (Job.requirements_summary.like("No specific requirements%"))
            ).limit(50)  # Process in batches
            
            return query.all()
        
        except Exception as e:
            logger.error(f"Error getting jobs for processing: {str(e)}")
            return []
    
    async def _process_jobs(self) -> int:
        """
        Process jobs that need ML processing
        
        Returns:
            int: Number of jobs processed
        """
        if not self.db:
            logger.error("Database session not available")
            return 0
            
        try:
            # Get jobs that need processing
            jobs_to_process = self._get_jobs_needing_processing()
            logger.info(f"Found {len(jobs_to_process)} jobs that need processing")
            
            processed_count = 0
            
            for job in jobs_to_process:
                try:
                    logger.info(f"Processing job {job.id}: {job.title}")
                    
                    # Check if category needs classification
                    if not job.category or job.category not in ['software', 'hardware']:
                        logger.info(f"Classifying job {job.id}")
                        job.category = classify_job_category(job.title, job.description)
                    
                    # Extract requirements summary
                    logger.info(f"Extracting requirements summary for job {job.id}")
                    job.requirements_summary = extract_requirements_summary(job.description)
                    
                    # Commit changes
                    self.db.commit()
                    processed_count += 1
                    logger.info(f"Successfully processed job {job.id}")
                    
                    # Prevent CPU overload
                    await asyncio.sleep(0.1)
                
                except Exception as e:
                    logger.error(f"Error processing job {job.id}: {str(e)}")
                    logger.error(traceback.format_exc())
                    self.db.rollback()
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Error in _process_jobs: {str(e)}")
            logger.error(traceback.format_exc())
            if self.db:
                self.db.rollback()
            return 0

async def process_single_batch():
    """Run the processor for a single batch"""
    processor = MLProcessor()
    processor.db = SessionLocal()
    
    try:
        processed = await processor._process_jobs()
        logger.info(f"Processed {processed} jobs")
        return processed
    finally:
        if processor.db:
            processor.db.close()

async def run_ml_processor():
    """Run the ML processor as a standalone service"""
    processor = MLProcessor()
    await processor.start()

if __name__ == "__main__":
    asyncio.run(run_ml_processor())