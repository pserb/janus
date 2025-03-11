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

logger = logging.getLogger("linkedin-scraper")


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job listings."""

    async def crawl(self, session: aiohttp.ClientSession) -> Tuple[int, int]:
        """
        Crawl LinkedIn job listings.

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

        logger.info(f"Starting LinkedIn scraper for {source.name}")

        # Base URL for LinkedIn job search
        base_url = "https://www.linkedin.com/jobs/search/"

        # Search parameters for software and hardware engineering internships
        search_params = [
            {"keywords": "software engineer intern", "f_tp": "1"},  # Internships
            {"keywords": "software developer intern", "f_tp": "1"},
            {"keywords": "hardware engineer intern", "f_tp": "1"},
            {"keywords": "software engineer entry", "f_E": "1"},  # Entry level
            {"keywords": "software developer entry", "f_E": "1"},
            {"keywords": "hardware engineer entry", "f_E": "1"},
        ]

        jobs_found = 0
        jobs_new = 0

        for params in search_params:
            # Construct search URL
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            search_url = f"{base_url}?{query_string}&sortBy=DD"  # Sort by date

            # Fetch search results
            html = await self.fetch(session, search_url)
            if not html:
                continue

            # Parse job listings
            soup = BeautifulSoup(html, "html.parser")
            job_cards = soup.select(".job-search-card")

            for job_card in job_cards:
                try:
                    # Extract job details
                    job_title_elem = job_card.select_one(".job-search-card__title")
                    if not job_title_elem:
                        continue

                    job_title = job_title_elem.text.strip()

                    # Skip if not relevant to software or hardware engineering
                    if not self._is_relevant_job(job_title):
                        continue

                    # Extract company name
                    company_name_elem = job_card.select_one(
                        ".job-search-card__subtitle a"
                    )
                    if not company_name_elem:
                        continue

                    company_name = company_name_elem.text.strip()

                    # Find or create company
                    company = crud.get_company_by_name(db=self.db, name=company_name)
                    if not company:
                        # Create new company
                        company_data = {
                            "name": company_name,
                            "career_page_url": f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '-')}/jobs/",
                            "is_active": True,
                        }
                        company = crud.create_company(db=self.db, company=company_data)

                    # Extract job link
                    job_link_elem = job_card.select_one(".job-search-card__title a")
                    if not job_link_elem or "href" not in job_link_elem.attrs:
                        continue

                    job_link = job_link_elem["href"]

                    # Extract posting date
                    date_elem = job_card.select_one(".job-search-card__listdate")
                    posting_date = self._parse_linkedin_date(
                        date_elem.text.strip() if date_elem else ""
                    )

                    # Extract location
                    location_elem = job_card.select_one(".job-search-card__location")
                    location = location_elem.text.strip() if location_elem else ""

                    # Determine job category
                    category = "software"
                    if (
                        "hardware" in job_title.lower()
                        or "fpga" in job_title.lower()
                        or "asic" in job_title.lower()
                    ):
                        category = "hardware"

                    # Create job data
                    job_data = JobCreate(
                        company_id=company.id,
                        title=job_title,
                        link=job_link,
                        posting_date=posting_date,
                        category=category,
                        description="",  # Will be fetched later
                        is_active=True,
                        job_source="linkedin",
                        location=location,
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
                    logger.error(f"Error processing job card: {str(e)}")
                    continue

        logger.info(f"LinkedIn scraper found {jobs_found} jobs, {jobs_new} new")
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

    def _parse_linkedin_date(self, date_text: str) -> datetime:
        """
        Parse LinkedIn date format.

        Args:
            date_text: Date text from LinkedIn

        Returns:
            datetime: Parsed date
        """
        now = datetime.now(pytz.utc)

        if not date_text:
            return now

        if "hour" in date_text or "minute" in date_text:
            # Posted today
            return now

        if "day" in date_text:
            # Posted X days ago
            try:
                days = int(re.search(r"(\d+)", date_text).group(1))
                return now - timedelta(days=days)
            except:
                return now

        if "week" in date_text:
            # Posted X weeks ago
            try:
                weeks = int(re.search(r"(\d+)", date_text).group(1))
                return now - timedelta(weeks=weeks)
            except:
                return now

        if "month" in date_text:
            # Posted X months ago
            try:
                months = int(re.search(r"(\d+)", date_text).group(1))
                # Approximate months as 30 days
                return now - timedelta(days=30 * months)
            except:
                return now

        # Default to current time
        return now
