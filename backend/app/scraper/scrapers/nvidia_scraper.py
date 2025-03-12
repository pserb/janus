import logging
import aiohttp
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pytz
from typing import Tuple, Dict, Any
from pydantic import ValidationError
from urllib.parse import urljoin

from ...schemas import JobCreate
from ... import crud
from ..base import BaseScraper

logger = logging.getLogger("nvidia-scraper")


class NVIDIAScraper(BaseScraper):
    """Dedicated scraper for NVIDIA job listings."""

    async def crawl(self, session: aiohttp.ClientSession) -> Tuple[int, int]:
        """
        Crawl NVIDIA career page with specific URL for interns and new grads.

        Args:
            session: aiohttp ClientSession

        Returns:
            Tuple[int, int]: (jobs_found, jobs_new)
        """
        # Get company info
        company = crud.get_company(db=self.db, company_id=self.company_id)
        if not company:
            logger.error(f"Company not found: {self.company_id}")
            return (0, 0)

        # Verify this is indeed NVIDIA
        if "nvidia" not in company.name.lower():
            logger.error(f"This scraper is for NVIDIA only, got: {company.name}")
            return (0, 0)

        logger.info(f"Starting dedicated NVIDIA scraper for {company.name}")

        # Use specific URL for interns and new grads in the US
        nvidia_url = "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/jobs?workerSubType=0c40f6bd1d8f10adf6dae42e46d44a17&workerSubType=ab40a98049581037a3ada55b087049b7&locationHierarchy1=2fcb99c455831013ea52fb338f2932d8"
        
        logger.info(f"NVIDIA scraper using URL: {nvidia_url}")

        # Fetch the career page
        html = await self.fetch(session, nvidia_url)
        if not html:
            logger.error(f"Failed to fetch NVIDIA career page: {nvidia_url}")
            return (0, 0)

        # Parse the career page
        jobs_found = 0
        jobs_new = 0

        try:
            # Parse job listings using BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Log the page title to verify we got the right page
            page_title = soup.title.text if soup.title else "No title"
            logger.info(f"NVIDIA page title: {page_title}")

            # Specific parsing for Workday-based job listings (which NVIDIA uses)
            job_listings = []
            
            # Look for job cards - Workday typically uses specific class names
            job_cards = soup.select('li[data-automation-id="jobCard"]')
            logger.info(f"Found {len(job_cards)} job cards on NVIDIA page")
            
            for card in job_cards:
                try:
                    # Extract job title
                    title_elem = card.select_one('a[data-automation-id="jobTitle"]')
                    if not title_elem:
                        continue
                        
                    job_title = title_elem.text.strip()
                    
                    # Extract job link
                    job_link = title_elem.get('href', '')
                    if job_link and not job_link.startswith(('http://', 'https://')):
                        job_link = urljoin(nvidia_url, job_link)
                    
                    # Extract location if available
                    location_elem = card.select_one('[data-automation-id="locationRow"]')
                    location = location_elem.text.strip() if location_elem else ""
                    
                    # Extract posting date if available
                    date_elem = card.select_one('[data-automation-id="postedOn"]')
                    date_text = date_elem.text.strip() if date_elem else ""
                    posting_date = self._parse_workday_date(date_text)
                    
                    job_listings.append({
                        "title": job_title,
                        "link": job_link,
                        "location": location,
                        "posting_date": posting_date
                    })
                    logger.info(f"Found NVIDIA job: {job_title}")
                    
                except Exception as e:
                    logger.error(f"Error parsing job card: {str(e)}")
            
            # Process found job listings
            logger.info(f"Found {len(job_listings)} potential job listings on NVIDIA career page")

            for job in job_listings:
                # Filter for relevant engineering jobs only
                if not self._is_relevant_job(job["title"]):
                    continue

                # Determine job category
                category = "software"
                if (
                    "hardware" in job["title"].lower()
                    or "fpga" in job["title"].lower()
                    or "asic" in job["title"].lower()
                ):
                    category = "hardware"

                # Create job data
                job_data = {
                    "company_id": company.id,
                    "title": job["title"],
                    "link": job["link"],
                    "posting_date": job.get("posting_date", datetime.now(pytz.utc)),
                    "category": category,
                    "description": "",  # Will fetch detailed description later if needed
                    "is_active": True,
                    "job_source": "nvidia_website",
                    "location": job.get("location", ""),
                }

                # Create job if it doesn't exist
                try:
                    is_new = self.create_job(job_data)
                    if is_new:
                        jobs_new += 1
                    jobs_found += 1
                except Exception as e:
                    logger.error(f"Error creating job: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing NVIDIA career page: {str(e)}")

        logger.info(f"NVIDIA scraper found {jobs_found} jobs, {jobs_new} new")
        return (jobs_found, jobs_new)

    def _parse_workday_date(self, date_text: str) -> datetime:
        """
        Parse Workday date format.
        
        Args:
            date_text: Date text from Workday (e.g., "Posted 3 Days Ago")
            
        Returns:
            datetime: Parsed date
        """
        now = datetime.now(pytz.utc)
        
        if not date_text or "just posted" in date_text.lower():
            return now
            
        try:
            # Extract numbers from text like "Posted X Days Ago"
            days_match = re.search(r'(\d+)\s*day', date_text.lower())
            if days_match:
                days = int(days_match.group(1))
                return now - timedelta(days=days)
                
            # Extract numbers from text like "Posted X Weeks Ago"    
            weeks_match = re.search(r'(\d+)\s*week', date_text.lower())
            if weeks_match:
                weeks = int(weeks_match.group(1))
                return now - timedelta(weeks=weeks)
                
            # Extract numbers from text like "Posted X Months Ago"
            months_match = re.search(r'(\d+)\s*month', date_text.lower())
            if months_match:
                months = int(months_match.group(1))
                # Approximate months as 30 days
                return now - timedelta(days=30 * months)
                
        except Exception as e:
            logger.error(f"Error parsing date '{date_text}': {str(e)}")
            
        return now

    def _is_relevant_job(self, job_title: str) -> bool:
        """
        Check if a job title is relevant for software or hardware engineering internships.
        For NVIDIA, we're more permissive since we're already filtering by intern/new grad in the URL.
        
        Args:
            job_title: Job title to check
            
        Returns:
            bool: True if relevant, False otherwise
        """
        job_title_lower = job_title.lower()
        
        # Since we're already filtering for intern/new grad positions in the URL,
        # we just need to check for engineering relevance
        relevant_keywords = [
            "software", "developer", "engineer", "programming", "coder",
            "frontend", "backend", "full stack", "hardware", "fpga", "asic",
            "embedded", "systems", "firmware", "coding", "web", "app", 
            "algorithm", "ml", "ai", "data", "gpu", "cuda", "compiler",
            "graphics", "game", "gaming", "compute", "parallel", "architecture",
            "design", "verification", "validation", "test", "qa", "sqa"
        ]
        
        # Check if any relevant keyword is present
        return any(keyword in job_title_lower for keyword in relevant_keywords)