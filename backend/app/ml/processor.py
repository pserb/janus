# ml/processor.py
import asyncio
import logging
import re
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from sqlalchemy import or_, and_, func

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
    
    def _is_poorly_formatted(self, summary: str) -> bool:
        """Check if a summary is poorly formatted"""
        if not summary:
            return True
            
        # Check if summary contains HTML or website artifacts
        html_indicators = [
            "Sign In", "Submit Resume", "Back to search results", "Add to Favorites",
            "Removed from favorites", "Create one now", "password", "view your favorites",
            "QualificationsKey", "RequirementsAdditional", "Education & Experience",
            "apple.account", "closeto", "preferred qualifications"
        ]
        
        for indicator in html_indicators:
            if indicator.lower() in summary.lower():
                return True
        
        # Check if summary contains bullet points that aren't properly formatted
        if "•" in summary:
            # Good summaries have spaces after bullet points
            if "• " not in summary:
                return True
                
            # Good summaries have reasonable bullet point content
            bullet_points = re.findall(r'•\s+(.*?)(?:\n|$)', summary)
            if bullet_points and any(len(point) < 10 or len(point) > 300 for point in bullet_points):
                return True
        
        # Check if summary has a good structure with "Key Requirements:" header
        if not summary.startswith("Key Requirements:"):
            return True
            
        # Check if summary contains excessive line breaks or bad formatting
        if summary.count('\n') > 30:  # Too many line breaks
            return True
            
        return False
    
    async def _process_jobs(self) -> int:
        """
        Process jobs that need requirements summarization
        
        Returns:
            int: Number of jobs processed
        """
        try:
            # Get all jobs that meet criteria for processing
            query = self.db.query(Job).filter(
                Job.description.isnot(None),
                Job.description != ""
            )
            
            # Apply filter conditions for jobs that need processing
            query = query.filter(
                or_(
                    # No summary
                    Job.requirements_summary.is_(None),
                    Job.requirements_summary == "",
                    
                    # Generic summary
                    Job.requirements_summary == "No specific requirements extracted.",
                    Job.requirements_summary == "Failed to summarize requirements.",
                    Job.requirements_summary.like("No specific requirements%"),
                    
                    # Poor quality summary (custom function can't be used directly in query)
                    # We'll check these cases manually after fetching
                    
                    # Overly long summaries (likely contain HTML)
                    func.length(Job.requirements_summary) > 1000,
                    
                    # Likely HTML content
                    Job.requirements_summary.like("%Submit Resume%"),
                    Job.requirements_summary.like("%Sign In%"),
                    Job.requirements_summary.like("%Apple Account%"),
                    
                    # Bad formatting patterns
                    Job.requirements_summary.like("%Key QualificationsKey Qualifications%"),
                    Job.requirements_summary.like("%Education & ExperienceEducation & Experience%"),
                    Job.requirements_summary.like("%Additional RequirementsAdditional Requirements%")
                )
            ).limit(50).all()
            
            jobs_to_process = []
            
            # Double-check with custom logic for others
            for job in query:
                if job.requirements_summary and not self._is_poorly_formatted(job.requirements_summary):
                    # Skip jobs that have good summaries
                    continue
                jobs_to_process.append(job)
            
            logger.info(f"Found {len(jobs_to_process)} jobs that need requirement summarization")
            
            processed_count = 0
            
            for job in jobs_to_process:
                try:
                    # Log what we're processing
                    logger.info(f"Processing job {job.id}: {job.title} ({job.company_name if hasattr(job, 'company_name') else 'Unknown Company'})")
                    
                    # If there's an existing summary, log its characteristics
                    if job.requirements_summary:
                        logger.info(f"Original summary: Length={len(job.requirements_summary)}, First 50 chars: {job.requirements_summary[:50]}...")
                    
                    # Summarize requirements
                    summary = summarize_job_requirements(job.description)
                    
                    # Skip if summary is too short or generic
                    if (not summary or 
                        len(summary) < 30 or
                        summary == "No specific requirements extracted." or
                        summary == "Failed to summarize requirements."):
                        
                        logger.warning(f"Generated summary for job {job.id} is too short or generic: '{summary}'")
                        
                        # Try one more time with a larger chunk of the description
                        if job.description and len(job.description) > 100:
                            logger.info(f"Retrying with full description for job {job.id}")
                            summary = summarize_job_requirements(job.description)
                    
                    # Log the new summary
                    logger.info(f"New summary: Length={len(summary)}, First 50 chars: {summary[:50]}...")
                    
                    # Update job with summary
                    job.requirements_summary = summary
                    self.db.commit()
                    
                    processed_count += 1
                    logger.info(f"Successfully processed job {job.id}")
                    
                    # Prevent CPU overload
                    await asyncio.sleep(0.1)
                
                except Exception as e:
                    logger.error(f"Error processing job {job.id}: {str(e)}")
                    self.db.rollback()
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Error in _process_jobs: {str(e)}")
            if self.db:
                self.db.rollback()
            return 0


async def run_ml_processor():
    """Run the ML processor as a standalone process"""
    processor = MLProcessor()
    await processor.start()


if __name__ == "__main__":
    asyncio.run(run_ml_processor())