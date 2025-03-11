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

logger = logging.getLogger("company-scraper")


class CompanyScraper(BaseScraper):
    """Scraper for company career pages."""

    async def crawl(self, session: aiohttp.ClientSession) -> Tuple[int, int]:
        """
        Crawl a company's career page.

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

        logger.info(f"Starting company scraper for {company.name}")

        # Get the company's career page URL
        career_page_url = company.career_page_url
        if not career_page_url:
            logger.error(f"No career page URL for company: {company.name}")
            return (0, 0)

        # Fetch the career page
        html = await self.fetch(session, career_page_url)
        if not html:
            logger.error(f"Failed to fetch career page: {career_page_url}")
            return (0, 0)

        # Parse the career page
        jobs_found = 0
        jobs_new = 0

        # Use a flexible approach to handle different career page formats
        try:
            # Parse job listings using BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Look for common job listing patterns
            job_listings = []

            # Method 1: Look for job listings in tables
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    # Check if this might be a job listing row
                    cells = row.find_all("td")
                    links = row.find_all("a")

                    if len(cells) >= 2 and len(links) >= 1:
                        # This could be a job listing row
                        job_title = links[0].text.strip()
                        job_link = links[0].get("href", "")

                        # Make sure the link is absolute
                        if job_link and not job_link.startswith(
                            ("http://", "https://")
                        ):
                            job_link = urljoin(career_page_url, job_link)

                        # Only add if it looks like a job title and has a link
                        if (
                            job_title
                            and job_link
                            and self._looks_like_job_title(job_title)
                        ):
                            job_listings.append(
                                {
                                    "title": job_title,
                                    "link": job_link,
                                    "source": "table",
                                }
                            )

            # Method 2: Look for job listings in list items
            lists = soup.find_all(["ul", "ol"])
            for list_elem in lists:
                items = list_elem.find_all("li")
                for item in items:
                    links = item.find_all("a")
                    if links:
                        job_title = links[0].text.strip()
                        job_link = links[0].get("href", "")

                        # Make sure the link is absolute
                        if job_link and not job_link.startswith(
                            ("http://", "https://")
                        ):
                            job_link = urljoin(career_page_url, job_link)

                        # Only add if it looks like a job title and has a link
                        if (
                            job_title
                            and job_link
                            and self._looks_like_job_title(job_title)
                        ):
                            job_listings.append(
                                {"title": job_title, "link": job_link, "source": "list"}
                            )

            # Method 3: Look for job listings in divs with common job listing class names
            job_containers = soup.find_all(
                "div",
                class_=re.compile(
                    r"job|career|position|opening|listing", re.IGNORECASE
                ),
            )
            for container in job_containers:
                links = container.find_all("a")
                for link in links:
                    job_title = link.text.strip()
                    job_link = link.get("href", "")

                    # Make sure the link is absolute
                    if job_link and not job_link.startswith(("http://", "https://")):
                        job_link = urljoin(career_page_url, job_link)

                    # Only add if it looks like a job title and has a link
                    if job_title and job_link and self._looks_like_job_title(job_title):
                        job_listings.append(
                            {"title": job_title, "link": job_link, "source": "div"}
                        )

            # Method 4: Look for job listings in common job board widgets
            # Greenhouse
            greenhouse_jobs = soup.find_all("div", class_=re.compile(r"greenhouse|ghr"))
            for job_elem in greenhouse_jobs:
                links = job_elem.find_all("a")
                for link in links:
                    job_title = link.text.strip()
                    job_link = link.get("href", "")

                    # Make sure the link is absolute
                    if job_link and not job_link.startswith(("http://", "https://")):
                        job_link = urljoin(career_page_url, job_link)

                    # Only add if it looks like a job title and has a link
                    if job_title and job_link and self._looks_like_job_title(job_title):
                        job_listings.append(
                            {
                                "title": job_title,
                                "link": job_link,
                                "source": "greenhouse",
                            }
                        )

            # Workday
            workday_jobs = soup.find_all("div", class_=re.compile(r"workday|wd"))
            for job_elem in workday_jobs:
                links = job_elem.find_all("a")
                for link in links:
                    job_title = link.text.strip()
                    job_link = link.get("href", "")

                    # Make sure the link is absolute
                    if job_link and not job_link.startswith(("http://", "https://")):
                        job_link = urljoin(career_page_url, job_link)

                    # Only add if it looks like a job title and has a link
                    if job_title and job_link and self._looks_like_job_title(job_title):
                        job_listings.append(
                            {"title": job_title, "link": job_link, "source": "workday"}
                        )

            # Process found job listings
            logger.info(
                f"Found {len(job_listings)} potential job listings on {company.name} career page"
            )

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

                # Extract location if present in the title
                location = self._extract_location(job["title"])

                # Set posting date to now since we don't have that information
                posting_date = datetime.now(pytz.utc)

                # Create job data as a dictionary with all required fields
                job_data: Dict[str, Any] = {
                    "company_id": company.id,
                    "title": job["title"],
                    "link": job["link"],
                    "posting_date": posting_date,
                    "category": category,
                    "description": "",  # Will fetch detailed description later if needed
                    "is_active": True,
                    "job_source": "company_website",
                    "location": location,
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
            logger.error(f"Error parsing career page for {company.name}: {str(e)}")

        logger.info(
            f"Company scraper for {company.name} found {jobs_found} jobs, {jobs_new} new"
        )
        return (jobs_found, jobs_new)

    def _looks_like_job_title(self, text: str) -> bool:
        """
        Check if a text looks like a job title.

        Args:
            text: Text to check

        Returns:
            bool: True if it looks like a job title, False otherwise
        """
        # Remove common noise words
        noise_words = [
            "view",
            "apply",
            "details",
            "learn more",
            "read more",
            "click here",
        ]
        text_lower = text.lower()

        for word in noise_words:
            if text_lower == word:
                return False

        # Check text length (job titles are usually not too short or too long)
        if len(text) < 5 or len(text) > 100:
            return False

        # Check for common job title keywords
        job_keywords = [
            "engineer",
            "developer",
            "programmer",
            "analyst",
            "manager",
            "associate",
            "intern",
            "specialist",
            "architect",
            "lead",
            "software",
            "hardware",
            "systems",
            "data",
            "network",
            "web",
            "frontend",
            "backend",
            "full stack",
            "qa",
            "devops",
            "sre",
            "support",
            "technician",
            "administrator",
            "ops",
            "designer",
        ]

        return any(keyword in text_lower for keyword in job_keywords)

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

    def _extract_location(self, job_title: str) -> str:
        """
        Try to extract location from job title if present.

        Args:
            job_title: Job title

        Returns:
            str: Extracted location or empty string
        """
        # Common patterns for location in job titles
        # Pattern 1: "Job Title - Location"
        pattern1 = re.search(r"\s-\s([^-]+)$", job_title)
        if pattern1:
            return pattern1.group(1).strip()

        # Pattern 2: "Job Title (Location)"
        pattern2 = re.search(r"\(([^)]+)\)$", job_title)
        if pattern2:
            return pattern2.group(1).strip()

        # Pattern 3: "Job Title | Location"
        pattern3 = re.search(r"\|\s*([^|]+)$", job_title)
        if pattern3:
            return pattern3.group(1).strip()

        return ""