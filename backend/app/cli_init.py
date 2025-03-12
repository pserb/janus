import logging

from .database import SessionLocal
from . import crud, schemas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("janus-cli-init")

# Real companies that are good sources for internships and entry-level positions
REAL_TECH_COMPANIES = [
    {
        "name": "Google",
        "website": "https://www.google.com",
        "career_page_url": "https://careers.google.com/jobs/results/?degree=BACHELORS&degree=MASTERS&distance=50&employment_type=INTERN&employment_type=FULL_TIME&jex=ENTRY_LEVEL",
        "ticker": "GOOGL",
    },
    {
        "name": "Microsoft",
        "website": "https://www.microsoft.com",
        "career_page_url": "https://careers.microsoft.com/students/us/en/search-results?keywords=Intern%20OR%20%22New%20Grad%22",
        "ticker": "MSFT",
    },
    {
        "name": "Apple",
        "website": "https://www.apple.com",
        "career_page_url": "https://jobs.apple.com/en-us/search?team=internships-STDNT-INTRN",
        "ticker": "AAPL",
        "scrape_frequency_hours": 12.0,  # Check twice a day
    },
    {
        "name": "Amazon",
        "website": "https://www.amazon.com",
        "career_page_url": "https://www.amazon.jobs/en/teams/internships-for-students",
        "ticker": "AMZN",
    },
    {
        "name": "Meta",
        "website": "https://www.meta.com",
        "career_page_url": "https://www.metacareers.com/jobs/?roles[0]=intern&is_leadership=0",
        "ticker": "META",
    },
    {
        "name": "NVIDIA",
        "website": "https://www.nvidia.com",
        "career_page_url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
        "ticker": "NVDA",
        "scrape_frequency_hours": 12.0,  # Check twice a day
    },
    {
        "name": "IBM",
        "website": "https://www.ibm.com",
        "career_page_url": "https://www.ibm.com/employment/students/",
        "ticker": "IBM",
    },
    {
        "name": "Intel",
        "website": "https://www.intel.com",
        "career_page_url": "https://jobs.intel.com/en/search-jobs/Intern/599/1",
        "ticker": "INTC",
    },
    {
        "name": "AMD",
        "website": "https://www.amd.com",
        "career_page_url": "https://jobs.amd.com/go/Students/2567200/",
        "ticker": "AMD",
    },
    {
        "name": "Salesforce",
        "website": "https://www.salesforce.com",
        "career_page_url": "https://www.salesforce.com/company/careers/university-recruiting/",
        "ticker": "CRM",
    },
    # Adding more top tech companies for internships
    {
        "name": "Adobe",
        "website": "https://www.adobe.com",
        "career_page_url": "https://www.adobe.com/careers/university.html",
        "ticker": "ADBE",
    },
    {
        "name": "Qualcomm",
        "website": "https://www.qualcomm.com",
        "career_page_url": "https://www.qualcomm.com/company/careers/students",
        "ticker": "QCOM",
    },
    {
        "name": "Oracle",
        "website": "https://www.oracle.com",
        "career_page_url": "https://www.oracle.com/corporate/careers/students-grads/",
        "ticker": "ORCL",
    },
    {
        "name": "Cisco",
        "website": "https://www.cisco.com",
        "career_page_url": "https://www.cisco.com/c/en/us/about/careers/working-at-cisco/students-and-new-graduate-programs.html",
        "ticker": "CSCO",
    },
    {
        "name": "Texas Instruments",
        "website": "https://www.ti.com",
        "career_page_url": "https://careers.ti.com/job-search?from=0&s=1&rk=29",
        "ticker": "TXN",
    },
]

# Job board sources that are good for finding tech internships
JOB_BOARD_SOURCES = [
    {
        "name": "LinkedIn Software Internships",
        "url": "https://www.linkedin.com/jobs/search/?keywords=software%20intern&sortBy=DD",
        "crawler_type": "linkedin",
        "crawl_frequency_minutes": 60,
        "priority": 1,
    },
    {
        "name": "LinkedIn Hardware Internships",
        "url": "https://www.linkedin.com/jobs/search/?keywords=hardware%20intern&sortBy=DD",
        "crawler_type": "linkedin",
        "crawl_frequency_minutes": 60,
        "priority": 1,
    },
    {
        "name": "Indeed Software Internships",
        "url": "https://www.indeed.com/jobs?q=software+intern&sort=date",
        "crawler_type": "indeed",
        "crawl_frequency_minutes": 120,
        "priority": 2,
    },
    {
        "name": "Indeed Hardware Internships",
        "url": "https://www.indeed.com/jobs?q=hardware+intern&sort=date",
        "crawler_type": "indeed",
        "crawl_frequency_minutes": 120,
        "priority": 2,
    },
    {
        "name": "Glassdoor Software Internships",
        "url": "https://www.glassdoor.com/Job/software-intern-jobs-SRCH_KO0,15.htm?sortBy=date_desc",
        "crawler_type": "glassdoor",
        "crawl_frequency_minutes": 180,
        "priority": 2,
    },
    {
        "name": "LinkedIn Software New Grad",
        "url": "https://www.linkedin.com/jobs/search/?keywords=software%20new%20grad&sortBy=DD",
        "crawler_type": "linkedin",
        "crawl_frequency_minutes": 60,
        "priority": 1,
    },
    {
        "name": "LinkedIn Hardware New Grad",
        "url": "https://www.linkedin.com/jobs/search/?keywords=hardware%20new%20grad&sortBy=DD",
        "crawler_type": "linkedin",
        "crawl_frequency_minutes": 60,
        "priority": 1,
    },
]


def init_sources():
    """
    Initialize the database with real company and job board sources.
    No fake job data is added.
    """
    db = SessionLocal()
    try:
        # Add real tech companies
        companies_added = 0
        for company_data in REAL_TECH_COMPANIES:
            # Check if company already exists
            existing_company = crud.get_company_by_name(db, company_data["name"])
            if existing_company:
                logger.info(f"Updating existing company: {company_data['name']}")
                # Update company with new data
                crud.update_company(db, existing_company.id, company_data)
                continue

            # Create company
            company = crud.create_company(db, schemas.CompanyCreate(**company_data))
            companies_added += 1
            logger.info(f"Added company: {company.name}")

        # Add job board sources
        sources_added = 0
        for source_data in JOB_BOARD_SOURCES:
            # Check if source already exists
            existing_source = crud.get_source_by_name(db, source_data["name"])
            if existing_source:
                logger.info(f"Source already exists: {source_data['name']}")
                continue

            # Create source
            source = crud.create_source(db, schemas.SourceCreate(**source_data))
            sources_added += 1
            logger.info(f"Added source: {source.name}")

        logger.info(
            f"Initialization complete. Added {companies_added} companies and {sources_added} sources."
        )
        return companies_added, sources_added

    finally:
        db.close()


if __name__ == "__main__":
    init_sources()