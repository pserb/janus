import logging
import aiohttp
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import pytz
from typing import Tuple
from pydantic import ValidationError

from ...schemas import JobCreate
from ... import crud
from ..base import BaseScraper

logger = logging.getLogger("glassdoor-scraper")


class GlassdoorScraper(BaseScraper):
    """Scraper for Glassdoor job listings."""

    async def crawl(self, session: aiohttp.ClientSession) -> Tuple[int, int]:
        """
        Crawl Glassdoor job listings.

        Args:
            session: aiohttp ClientSession

        Returns:
            Tuple[int, int]: (jobs_found, jobs_new)
        """
        # Get source info
        source = crud.get_source(db=self.db, source_id=self.source_id)
        if not source:
            logger.error(f"Source not found: {self.source_id}")
            return (0, 0)

        logger.info(f"Starting Glassdoor scraper for {source.name}")

        # Base URL for Glassdoor job search
        base_url = "https://www.glassdoor.com/Job/jobs.htm"

        # Glassdoor requires specific headers to avoid bot detection
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            "TE": "Trailers",
            "Referer": "https://www.glassdoor.com/",
        }

        # Search parameters for software and hardware engineering internships
        search_params = [
            {"sc.keyword": "software engineer intern", "jobType": "internship"},
            {"sc.keyword": "software developer intern", "jobType": "internship"},
            {"sc.keyword": "hardware engineer intern", "jobType": "internship"},
            {"sc.keyword": "software engineer entry", "sc.jobType": "fulltime"},
            {"sc.keyword": "software developer new grad", "sc.jobType": "fulltime"},
            {"sc.keyword": "hardware engineer new grad", "sc.jobType": "fulltime"},
        ]

        jobs_found = 0
        jobs_new = 0

        for params in search_params:
            # Construct search URL
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            search_url = f"{base_url}?{query_string}&fromAge=14&sortBy=date_desc"  # Last 14 days, sorted by date

            # Fetch search results
            html = await self.fetch(session, search_url, headers=headers)
            if not html:
                continue

            # Parse job listings using BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Find all job listings
            job_listings = soup.select("li.react-job-listing")

            for job_listing in job_listings:
                try:
                    # Extract job data attributes
                    job_id = job_listing.get("data-id", "")
                    employer_id = job_listing.get("data-employer-id", "")

                    # Extract job title
                    job_title_elem = job_listing.select_one("a.jobLink")
                    if not job_title_elem:
                        continue

                    job_title = job_title_elem.text.strip()

                    # Skip if not relevant to software or hardware engineering
                    if not self._is_relevant_job(job_title):
                        continue

                    # Extract company name
                    company_elem = job_listing.select_one(
                        "div.jobHeader a.employerName"
                    )
                    if not company_elem:
                        continue

                    company_name = company_elem.text.strip()

                    # Find or create company
                    company = crud.get_company_by_name(db=self.db, name=company_name)
                    if not company:
                        # Create new company
                        company_data = {
                            "name": company_name,
                            "career_page_url": f"https://www.glassdoor.com/Jobs/{company_name.replace(' ', '-')}-Jobs-E{employer_id}.htm",
                            "is_active": True,
                        }
                        company = crud.create_company(db=self.db, company=company_data)

                    # Extract job link
                    job_link = f"https://www.glassdoor.com/job-listing/{job_id}"

                    # Extract location
                    location_elem = job_listing.select_one("span.loc")
                    location = location_elem.text.strip() if location_elem else ""

                    # Extract posting date
                    date_elem = job_listing.select_one("div.listing-age")
                    date_text = date_elem.text.strip() if date_elem else ""
                    posting_date = self._parse_glassdoor_date(date_text)

                    # Determine job category
                    category = "software"
                    if (
                        "hardware" in job_title.lower()
                        or "fpga" in job_title.lower()
                        or "asic" in job_title.lower()
                    ):
                        category = "hardware"

                    # Get salary if available
                    salary_elem = job_listing.select_one("span.salary-estimate")
                    salary_info = salary_elem.text.strip() if salary_elem else ""

                    # Create job data
                    job_data = JobCreate(
                        company_id=company.id,
                        title=job_title,
                        link=job_link,
                        posting_date=posting_date,
                        category=category,
                        description="",  # Will fetch detailed description later if needed
                        is_active=True,
                        job_source="glassdoor",
                        source_job_id=job_id,
                        location=location,
                        salary_info=salary_info,
                    )

                    # Create job if it doesn't exist
                    is_new = self.create_job(job_data.dict())

                    if is_new:
                        jobs_new += 1

                    jobs_found += 1

                except ValidationError as e:
                    logger.error(f"Validation error creating job: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing Glassdoor job: {str(e)}")
                    continue

        logger.info(f"Glassdoor scraper found {jobs_found} jobs, {jobs_new} new")
        return (jobs_found, jobs_new)

    def _is_relevant_job(self, job_title: str) -> bool:
        """
        Check if a job title is relevant for software or hardware engineering.

        Args:
            job_title: Job title to check

        Returns:
            bool: True if relevant, False otherwise
        """
        job_title_lower = job_title.lower()

        # Keywords that indicate relevant positions
        relevant_keywords = [
            "software",
            "developer",
            "engineer",
            "programming",
            "coder",
            "frontend",
            "backend",
            "full stack",
            "hardware",
            "fpga",
            "asic",
            "embedded",
            "systems",
            "firmware",
            "coding",
            "web developer",
        ]

        # Check for internship or entry-level indicators
        level_indicators = [
            "intern",
            "internship",
            "entry",
            "junior",
            "graduate",
            "new grad",
        ]

        # Must have at least one relevant keyword
        has_relevant_keyword = any(
            keyword in job_title_lower for keyword in relevant_keywords
        )

        # Must have at least one level indicator
        has_level_indicator = any(
            indicator in job_title_lower for indicator in level_indicators
        )

        return has_relevant_keyword and has_level_indicator

    def _parse_glassdoor_date(self, date_text: str) -> datetime:
        """
        Parse Glassdoor date format.

        Args:
            date_text: Date text from Glassdoor (e.g., "3d ago")

        Returns:
            datetime: Parsed date
        """
        now = datetime.now(pytz.utc)

        if not date_text or date_text.lower() == "just posted":
            return now

        try:
            # Extract number and unit (e.g., "3d" -> ("3", "d"))
            match = re.match(r"(\d+)([dhm])", date_text.lower())
            if not match:
                return now

            amount, unit = match.groups()
            amount = int(amount)

            if unit == "m":  # Minutes
                return now - timedelta(minutes=amount)
            elif unit == "h":  # Hours
                return now - timedelta(hours=amount)
            elif unit == "d":  # Days
                return now - timedelta(days=amount)
            else:
                return now

        except Exception as e:
            logger.error(f"Error parsing Glassdoor date '{date_text}': {str(e)}")
            return now
