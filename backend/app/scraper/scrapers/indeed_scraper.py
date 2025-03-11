import logging
import aiohttp
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import pytz
from typing import Tuple
from pydantic import ValidationError
import json

from ...schemas import JobCreate
from ... import crud
from ..base import BaseScraper

logger = logging.getLogger("indeed-scraper")


class IndeedScraper(BaseScraper):
    """Scraper for Indeed job listings."""

    async def crawl(self, session: aiohttp.ClientSession) -> Tuple[int, int]:
        """
        Crawl Indeed job listings.

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

        logger.info(f"Starting Indeed scraper for {source.name}")

        # Base URL for Indeed job search
        base_url = "https://www.indeed.com/jobs"

        # Search parameters for software and hardware engineering internships
        search_params = [
            {"q": "software engineer intern", "explvl": "entry_level"},
            {"q": "software developer intern", "explvl": "entry_level"},
            {"q": "hardware engineer intern", "explvl": "entry_level"},
            {"q": "software engineer entry level", "explvl": "entry_level"},
            {"q": "software developer new grad", "explvl": "entry_level"},
            {"q": "hardware engineer new grad", "explvl": "entry_level"},
        ]

        jobs_found = 0
        jobs_new = 0

        for params in search_params:
            # Construct search URL
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            search_url = f"{base_url}?{query_string}&sort=date"  # Sort by date

            # Fetch search results
            html = await self.fetch(session, search_url)
            if not html:
                continue

            # Parse job listings
            soup = BeautifulSoup(html, "html.parser")

            # Indeed uses a JavaScript-rendered page, so we need to extract data from script tags
            # Look for the mosaic-provider-jobcards script that contains job data
            script_tags = soup.find_all(
                "script", {"id": re.compile(r"mosaic-provider-jobcards")}
            )

            job_data_list = []
            for script in script_tags:
                try:
                    # Extract JSON data from script content
                    script_content = script.string
                    if not script_content:
                        continue

                    # Find JSON data in the script content
                    json_match = re.search(
                        r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*({.*?});',
                        script_content,
                        re.DOTALL,
                    )
                    if not json_match:
                        continue

                    json_data = json_match.group(1)
                    data = json.loads(json_data)

                    # Extract job listings from the data
                    if (
                        "metaData" in data
                        and "mosaicProviderJobCardsModel" in data["metaData"]
                    ):
                        job_cards = data["metaData"]["mosaicProviderJobCardsModel"][
                            "results"
                        ]
                        job_data_list.extend(job_cards)

                except Exception as e:
                    logger.error(f"Error parsing Indeed script data: {str(e)}")
                    continue

            # Process each job
            for job_data in job_data_list:
                try:
                    # Extract job details
                    job_title = job_data.get("title", "")

                    # Skip if not relevant to software or hardware engineering
                    if not self._is_relevant_job(job_title):
                        continue

                    company_name = job_data.get("company", "")

                    # Find or create company
                    company = crud.get_company_by_name(db=self.db, name=company_name)
                    if not company:
                        # Create new company
                        company_data = {
                            "name": company_name,
                            "career_page_url": f"https://www.indeed.com/cmp/{company_name.lower().replace(' ', '-')}/jobs",
                            "is_active": True,
                        }
                        company = crud.create_company(db=self.db, company=company_data)

                    # Extract job link
                    job_link = f"https://www.indeed.com/viewjob?jk={job_data.get('jobkey', '')}"

                    # Extract posting date
                    date_text = job_data.get("formattedRelativeTime", "")
                    posting_date = self._parse_indeed_date(date_text)

                    # Extract location
                    location = job_data.get("formattedLocation", "")

                    # Extract salary info if available
                    salary_info = job_data.get("salarySnippet", {}).get("text", "")

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
                        description=job_data.get("snippet", ""),
                        is_active=True,
                        job_source="indeed",
                        source_job_id=job_data.get("jobkey", ""),
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
                    logger.error(f"Error processing Indeed job: {str(e)}")
                    continue

        logger.info(f"Indeed scraper found {jobs_found} jobs, {jobs_new} new")
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

    def _parse_indeed_date(self, date_text: str) -> datetime:
        """
        Parse Indeed date format.

        Args:
            date_text: Date text from Indeed (e.g., "3 days ago")

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

        if "just posted" in date_text.lower() or "today" in date_text.lower():
            return now

        # Default to current time
        return now
