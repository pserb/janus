#!/bin/bash

echo "================================================================"
echo "🚀 JANUS COMPLETE DEPLOYMENT SCRIPT"
echo "================================================================"
echo "This script handles the entire deployment process in one command:"
echo "• Building all containers"
echo "• Starting services"
echo "• Creating database schema"
echo "• Initializing companies and job sources"
echo "• Running scrapers"
echo "• Processing requirements"
echo "• Fetching logos"
echo "================================================================"
echo "Starting deployment at $(date)"
echo ""

# Make all scripts executable
chmod +x scripts/*.sh &>/dev/null

# Step 1: Check if Docker is running
echo "▶️ Step 1: Verifying Docker is running..."
if ! docker info > /dev/null 2>&1; then
    echo "⚠️ Docker is not running. Please start Docker and try again."
    exit 1
fi
echo "✅ Docker is running."
echo ""

# Step 2: Build and start the containers
echo "▶️ Step 2: Building and starting containers..."
docker compose down
docker compose build
docker compose up -d
echo "✅ Containers started."
echo ""

# Step 3: Wait for services to be up
echo "▶️ Step 3: Waiting for services to initialize..."
echo "   This may take a moment..."
sleep 15

# Check if services are up
if ! docker compose ps backend | grep -q "Up"; then
    echo "⚠️ Backend service failed to start. Checking logs:"
    docker compose logs backend
    exit 1
fi

if ! docker compose ps frontend | grep -q "Up"; then
    echo "⚠️ Frontend service failed to start. Checking logs:"
    docker compose logs frontend
    exit 1
fi

if ! docker compose ps db | grep -q "Up"; then
    echo "⚠️ Database service failed to start. Checking logs:"
    docker compose logs db
    exit 1
fi
echo "✅ All services are running properly."
echo ""

# Step 4: Initialize the database schema
echo "▶️ Step 4: Creating database schema..."
docker compose exec -T backend python -c "
import logging
from sqlalchemy import inspect
from app.database import engine, Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('db-init')

# Create tables
logger.info('Creating database tables...')
Base.metadata.create_all(bind=engine)

# Verify tables were created
inspector = inspect(engine)
existing_tables = inspector.get_table_names()
logger.info(f'Tables created: {existing_tables}')

expected_tables = ['companies', 'jobs', 'sources', 'crawl_logs', 'sync_info']
for table in expected_tables:
    if table not in existing_tables:
        logger.error(f'❌ Table {table} is missing!')
    else:
        logger.info(f'✓ Table {table} exists')

success = all(table in existing_tables for table in expected_tables)
print(f'Database initialization {"successful" if success else "FAILED"}')
print(f'Created tables: {len(existing_tables)}')
"
echo "✅ Database schema initialized."
echo ""

# Step 5: Initialize company data sources
echo "▶️ Step 5: Initializing top tech companies and job sources..."
docker compose exec -T backend python -c "
from app.database import SessionLocal
from app import crud, models, schemas

# Real tech companies for internships
TECH_COMPANIES = [
    {\"name\": \"Google\", \"website\": \"https://www.google.com\", \"career_page_url\": \"https://careers.google.com/jobs/results/?degree=BACHELORS&degree=MASTERS&employment_type=INTERN&employment_type=FULL_TIME&jex=ENTRY_LEVEL\", \"ticker\": \"GOOGL\"},
    {\"name\": \"Microsoft\", \"website\": \"https://www.microsoft.com\", \"career_page_url\": \"https://careers.microsoft.com/students/us/en/search-results?keywords=Intern%20OR%20%22New%20Grad%22\", \"ticker\": \"MSFT\"},
    {\"name\": \"Apple\", \"website\": \"https://www.apple.com\", \"career_page_url\": \"https://jobs.apple.com/en-us/search?team=internships-STDNT-INTRN\", \"ticker\": \"AAPL\"},
    {\"name\": \"Amazon\", \"website\": \"https://www.amazon.com\", \"career_page_url\": \"https://www.amazon.jobs/en/teams/internships-for-students\", \"ticker\": \"AMZN\"},
    {\"name\": \"Meta\", \"website\": \"https://www.meta.com\", \"career_page_url\": \"https://www.metacareers.com/jobs/?roles[0]=intern\", \"ticker\": \"META\"},
    {\"name\": \"Netflix\", \"website\": \"https://www.netflix.com\", \"career_page_url\": \"https://jobs.netflix.com/search?q=intern\", \"ticker\": \"NFLX\"},
    {\"name\": \"NVIDIA\", \"website\": \"https://www.nvidia.com\", \"career_page_url\": \"https://www.nvidia.com/en-us/about-nvidia/careers/university-recruiting/\", \"ticker\": \"NVDA\"},
    {\"name\": \"IBM\", \"website\": \"https://www.ibm.com\", \"career_page_url\": \"https://www.ibm.com/employment/students/\", \"ticker\": \"IBM\"},
    {\"name\": \"Intel\", \"website\": \"https://www.intel.com\", \"career_page_url\": \"https://jobs.intel.com/en/search-jobs/Intern/599/1\", \"ticker\": \"INTC\"},
    {\"name\": \"AMD\", \"website\": \"https://www.amd.com\", \"career_page_url\": \"https://jobs.amd.com/go/Students/2567200/\", \"ticker\": \"AMD\"}
]

# Set up job boards
JOB_BOARDS = [
    {\"name\": \"LinkedIn Software\", \"url\": \"https://www.linkedin.com/jobs/search/?keywords=software%20intern\", \"crawler_type\": \"linkedin\", \"crawl_frequency_minutes\": 60, \"priority\": 1},
    {\"name\": \"LinkedIn Hardware\", \"url\": \"https://www.linkedin.com/jobs/search/?keywords=hardware%20intern\", \"crawler_type\": \"linkedin\", \"crawl_frequency_minutes\": 60, \"priority\": 1},
    {\"name\": \"Indeed Software\", \"url\": \"https://www.indeed.com/jobs?q=software+intern\", \"crawler_type\": \"indeed\", \"crawl_frequency_minutes\": 120, \"priority\": 2},
    {\"name\": \"Glassdoor Software\", \"url\": \"https://www.glassdoor.com/Job/software-intern-jobs-SRCH_KO0,15.htm\", \"crawler_type\": \"glassdoor\", \"crawl_frequency_minutes\": 180, \"priority\": 2}
]

db = SessionLocal()
try:
    # Add companies
    companies_added = 0
    for company_data in TECH_COMPANIES:
        existing = db.query(models.Company).filter(models.Company.name == company_data['name']).first()
        if not existing:
            crud.create_company(db, schemas.CompanyCreate(**company_data))
            companies_added += 1
    
    # Add job boards
    sources_added = 0
    for source_data in JOB_BOARDS:
        existing = db.query(models.Source).filter(models.Source.name == source_data['name']).first()
        if not existing:
            crud.create_source(db, schemas.SourceCreate(**source_data))
            sources_added += 1
    
    print(f'✅ Added {companies_added} companies and {sources_added} job sources')
finally:
    db.close()
"
echo "✅ Companies and job sources initialized."
echo ""

# Step 6: Run the scrapers to get REAL job listings
echo "▶️ Step 6: Running job scrapers to fetch real job listings..."
echo "   This may take a few minutes..."
docker compose exec -T backend python -m app.cli scrape 2>/dev/null || true
echo "✅ Job scraping completed."
echo ""

# Step 7: Process job requirements
echo "▶️ Step 7: Processing job requirements..."
docker compose exec -T backend python -m app.cli process --all 2>/dev/null || true
echo "✅ Job requirements processed."
echo ""

# Step 8: Fetch company logos
echo "▶️ Step 8: Fetching company logos..."
# First make sure the models import is fixed in logo_fetcher.py
docker compose exec -T backend bash -c "sed -i 's/from \.\. import crud/from \.\. import crud, models/' /app/app/ml/logo_fetcher.py"
docker compose exec -T backend python -m app.cli logos --all 2>/dev/null || true
echo "✅ Company logos fetched."
echo ""

# Step 9: Display stats
echo "▶️ Step 9: Displaying current job statistics..."
docker compose exec -T backend python -m app.cli stats 2>/dev/null || echo "No jobs found yet. Run scrapers again later to find jobs."
echo ""

# Final output
echo "================================================================"
echo "🚀 JANUS DEPLOYMENT SUCCESSFULLY COMPLETED!"
echo "================================================================"
echo ""
echo "Your Janus application is now running at:"
echo "• Frontend: http://localhost:3000"
echo "• Backend API: http://localhost:8000"
echo "• API Documentation: http://localhost:8000/docs"
echo ""
echo "What's next:"
echo "1. Visit the frontend at http://localhost:3000 to see any jobs found"
echo "2. You can manually run scrapers again later: ./scripts/scrape.sh"
echo "3. To restart the system: docker compose restart"
echo ""
echo "Deployment completed at $(date)"
echo "================================================================"
