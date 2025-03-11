import logging
from sqlalchemy.orm import Session
from typing import Tuple
import traceback

from .. import crud
from .base import BaseScraper

logger = logging.getLogger("janus-scraper-manager")


class ScraperManager:
    """
    Manager for running scrapers according to their schedules.
    """

    def __init__(self, db: Session):
        self.db = db
        self.scrapers = {}
        self._load_scrapers()

    def _load_scrapers(self):
        """
        Dynamically load scraper classes from the scraper module.
        """
        try:
            # Import the scrapers package
            from . import scrapers

            # Get all scraper modules
            scraper_modules = [
                getattr(scrapers, name)
                for name in dir(scrapers)
                if not name.startswith("_")
            ]

            # Register scrapers
            for module in scraper_modules:
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseScraper)
                        and attr is not BaseScraper
                    ):

                        # Get scraper type from class name (e.g., LinkedInScraper -> linkedin)
                        scraper_type = attr.__name__.replace("Scraper", "").lower()
                        self.scrapers[scraper_type] = attr
                        logger.info(
                            f"Registered scraper: {scraper_type} -> {attr.__name__}"
                        )

            logger.info(f"Loaded {len(self.scrapers)} scrapers")

        except Exception as e:
            logger.error(f"Error loading scrapers: {str(e)}")
            traceback.print_exc()

    async def run_source_scrapers(self) -> Tuple[int, int]:
        """
        Run scrapers for all sources that are due for crawling.

        Returns:
            Tuple[int, int]: (total_jobs_found, total_new_jobs)
        """
        sources = crud.get_sources_for_crawling(db=self.db)

        if not sources:
            logger.info("No sources due for crawling")
            return (0, 0)

        logger.info(f"Found {len(sources)} sources due for crawling")

        total_jobs_found = 0
        total_new_jobs = 0

        for source in sources:
            # Get the appropriate scraper class
            if source.crawler_type not in self.scrapers:
                logger.warning(f"No scraper found for type: {source.crawler_type}")
                continue

            scraper_class = self.scrapers[source.crawler_type]

            try:
                # Create and run the scraper
                scraper = scraper_class(db=self.db, source_id=source.id)
                jobs_found, new_jobs = await scraper.start()

                total_jobs_found += jobs_found
                total_new_jobs += new_jobs

                logger.info(
                    f"Completed scraper for {source.name}: {jobs_found} jobs found, {new_jobs} new jobs"
                )

            except Exception as e:
                logger.error(f"Error running scraper for {source.name}: {str(e)}")
                traceback.print_exc()

        return (total_jobs_found, total_new_jobs)

    async def run_company_scrapers(self) -> Tuple[int, int]:
        """
        Run scrapers for all companies that are due for crawling.

        Returns:
            Tuple[int, int]: (total_jobs_found, total_new_jobs)
        """
        companies = crud.get_companies_for_crawling(db=self.db)

        if not companies:
            logger.info("No companies due for crawling")
            return (0, 0)

        logger.info(f"Found {len(companies)} companies due for crawling")

        total_jobs_found = 0
        total_new_jobs = 0

        for company in companies:
            # For company career pages, we use a generic company scraper
            if "companyscraper" not in self.scrapers:
                logger.warning("No CompanyScraper found")
                continue

            scraper_class = self.scrapers["companyscraper"]

            try:
                # Create and run the scraper
                scraper = scraper_class(db=self.db, company_id=company.id)
                jobs_found, new_jobs = await scraper.start()

                total_jobs_found += jobs_found
                total_new_jobs += new_jobs

                logger.info(
                    f"Completed scraper for {company.name}: {jobs_found} jobs found, {new_jobs} new jobs"
                )

            except Exception as e:
                logger.error(f"Error running scraper for {company.name}: {str(e)}")
                traceback.print_exc()

        return (total_jobs_found, total_new_jobs)

    async def run_all_scrapers(self) -> Tuple[int, int]:
        """
        Run all scrapers that are due.

        Returns:
            Tuple[int, int]: (total_jobs_found, total_new_jobs)
        """
        source_results = await self.run_source_scrapers()
        company_results = await self.run_company_scrapers()

        total_jobs_found = source_results[0] + company_results[0]
        total_new_jobs = source_results[1] + company_results[1]

        return (total_jobs_found, total_new_jobs)

    async def run_specific_source(self, source_id: int) -> Tuple[int, int]:
        """
        Run scraper for a specific source.

        Args:
            source_id: ID of the source to crawl

        Returns:
            Tuple[int, int]: (jobs_found, new_jobs)
        """
        source = crud.get_source(db=self.db, source_id=source_id)
        if not source:
            logger.error(f"Source not found: {source_id}")
            return (0, 0)

        if source.crawler_type not in self.scrapers:
            logger.error(f"No scraper found for type: {source.crawler_type}")
            return (0, 0)

        scraper_class = self.scrapers[source.crawler_type]

        try:
            # Create and run the scraper
            scraper = scraper_class(db=self.db, source_id=source.id)
            jobs_found, new_jobs = await scraper.start()

            logger.info(
                f"Completed scraper for {source.name}: {jobs_found} jobs found, {new_jobs} new jobs"
            )

            return (jobs_found, new_jobs)

        except Exception as e:
            logger.error(f"Error running scraper for {source.name}: {str(e)}")
            traceback.print_exc()
            return (0, 0)

    async def run_specific_company(self, company_id: int) -> Tuple[int, int]:
        """
        Run scraper for a specific company.

        Args:
            company_id: ID of the company to crawl

        Returns:
            Tuple[int, int]: (jobs_found, new_jobs)
        """
        company = crud.get_company(db=self.db, company_id=company_id)
        if not company:
            logger.error(f"Company not found: {company_id}")
            return (0, 0)

        if "companyscraper" not in self.scrapers:
            logger.error("No CompanyScraper found")
            return (0, 0)

        scraper_class = self.scrapers["companyscraper"]

        try:
            # Create and run the scraper
            scraper = scraper_class(db=self.db, company_id=company.id)
            jobs_found, new_jobs = await scraper.start()

            logger.info(
                f"Completed scraper for {company.name}: {jobs_found} jobs found, {new_jobs} new jobs"
            )

            return (jobs_found, new_jobs)

        except Exception as e:
            logger.error(f"Error running scraper for {company.name}: {str(e)}")
            traceback.print_exc()
            return (0, 0)
