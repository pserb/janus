import logging
import aiohttp
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
import pytz
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import random
from urllib.parse import urlparse

from ..models import Company
from .. import crud

logger = logging.getLogger("janus-scraper")


class BaseScraper(ABC):
    """Base class for all scrapers to inherit from."""

    def __init__(
        self,
        db: Session,
        source_id: Optional[int] = None,
        company_id: Optional[int] = None,
    ):
        self.db = db
        self.source_id = source_id
        self.company_id = company_id
        self.crawl_log_id = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
        ]

    async def start(self):
        """Start the scraper."""
        # Create crawl log entry
        crawl_log = crud.create_crawl_log(
            db=self.db, source_id=self.source_id, company_id=self.company_id
        )
        self.crawl_log_id = crawl_log.id

        try:
            # Initialize HTTP session
            async with aiohttp.ClientSession() as session:
                # Perform crawling
                jobs_found, jobs_new = await self.crawl(session)

                # Update crawl log with success
                crud.update_crawl_log(
                    db=self.db,
                    log_id=self.crawl_log_id,
                    status="completed",
                    jobs_found=jobs_found,
                    jobs_new=jobs_new,
                )

                # Update source or company last crawled timestamp
                if self.source_id:
                    source_update = {"last_crawled": datetime.now(pytz.utc)}
                    crud.update_source(
                        db=self.db, source_id=self.source_id, source=source_update
                    )

                if self.company_id:
                    company_update = {"last_scraped": datetime.now(pytz.utc)}
                    crud.update_company(
                        db=self.db, company_id=self.company_id, company=company_update
                    )

                return jobs_found, jobs_new

        except Exception as e:
            logger.error(f"Error in scraper: {str(e)}", exc_info=True)

            # Update crawl log with failure
            crud.update_crawl_log(
                db=self.db,
                log_id=self.crawl_log_id,
                status="failed",
                error_message=str(e),
            )

            # Re-raise the exception
            raise

    @abstractmethod
    async def crawl(self, session: aiohttp.ClientSession) -> tuple:
        """
        Implement the crawling logic in subclasses.

        Args:
            session: aiohttp ClientSession for making HTTP requests

        Returns:
            tuple: (jobs_found, jobs_new)
        """
        pass

    async def fetch(
        self, session: aiohttp.ClientSession, url: str, headers: Dict = None
    ) -> str:
        """
        Fetch a URL with proper rate limiting and error handling.

        Args:
            session: aiohttp ClientSession
            url: URL to fetch
            headers: Optional headers dictionary

        Returns:
            str: HTML content
        """
        if not headers:
            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
            }

        # Add random delay for rate limiting (1-3 seconds)
        await asyncio.sleep(random.uniform(1, 3))

        try:
            # Get the domain from the URL
            domain = urlparse(url).netloc
            logger.info(f"Fetching URL: {url} (domain: {domain})")

            async with session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429:
                    # Too many requests, add a longer delay
                    logger.warning(f"Rate limited for {domain}, waiting 30 seconds...")
                    await asyncio.sleep(30)
                    return await self.fetch(session, url, headers)
                else:
                    logger.error(f"Failed to fetch {url}: HTTP {response.status}")
                    return ""
        except asyncio.TimeoutError:
            logger.error(f"Timeout for {url}")
            return ""
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return ""

    def create_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Create a job if it doesn't exist already.

        Args:
            job_data: Job data dictionary

        Returns:
            bool: True if a new job was created, False if it already existed
        """
        # Check if job already exists
        company_id = job_data.get("company_id")
        link = job_data.get("link")

        if not company_id or not link:
            logger.error("Job data missing company_id or link")
            return False

        # Query the database for jobs with the same company_id and link
        existing_jobs = (
            self.db.query(Company.id)
            .filter(Company.id == company_id)
            .join(Company.jobs)
            .filter_by(link=link)
            .count()
        )

        if existing_jobs > 0:
            # Job already exists
            return False

        # Create new job
        try:
            crud.create_job(db=self.db, job=job_data)
            return True
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            return False