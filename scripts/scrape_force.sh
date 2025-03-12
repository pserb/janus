#!/bin/bash

echo "=== Force Scraping Selected Companies ==="
echo "Starting at $(date)"

# Check if backend is running
if ! docker compose ps backend | grep -q "Up"; then
    echo "⚠️ Backend service is not running."
    echo "Starting backend service..."
    docker compose up -d backend
    sleep 5
fi

# Get company IDs
echo "Getting company IDs..."

# Function to get company ID by name
get_company_id() {
    local company_name=$1
    docker compose exec -T backend python -c "
from app.database import SessionLocal
from app import models
db = SessionLocal()
company = db.query(models.Company).filter(models.Company.name == '$company_name').first()
print(company.id if company else 'Not found')
db.close()
"
}

# Get IDs for specific companies
NVIDIA_ID=$(get_company_id "NVIDIA")
APPLE_ID=$(get_company_id "Apple")
GOOGLE_ID=$(get_company_id "Google")
MICROSOFT_ID=$(get_company_id "Microsoft")
AMAZON_ID=$(get_company_id "Amazon")

echo "Company IDs:"
echo "- NVIDIA: $NVIDIA_ID"
echo "- Apple: $APPLE_ID"
echo "- Google: $GOOGLE_ID"
echo "- Microsoft: $MICROSOFT_ID"
echo "- Amazon: $AMAZON_ID"

# Force scrape each company by directly calling their scraper
force_scrape_company() {
    local company_id=$1
    local company_name=$2
    local module_name=$3
    local class_name=$4
    
    if [[ "$company_id" == "Not found" ]]; then
        echo "⚠️ $company_name not found in database. Skipping."
        return
    fi
    
    echo "Force scraping $company_name (ID: $company_id) using $class_name scraper..."
    
    docker compose exec -T backend python -c "
import asyncio
from app.database import SessionLocal
from app.scraper.scrapers.$module_name import $class_name
db = SessionLocal()
async def run_scraper():
    scraper = $class_name(db=db, company_id=$company_id)
    result = await scraper.start()
    print(f'Found {result[0]} jobs, {result[1]} new')
asyncio.run(run_scraper())
"
}

# Force scrape selected companies
echo "Starting forced scraping..."

if [[ "$NVIDIA_ID" != "Not found" ]]; then
    force_scrape_company "$NVIDIA_ID" "NVIDIA" "nvidia_scraper" "NVIDIAScraper"
fi

if [[ "$APPLE_ID" != "Not found" && -f "backend/app/scraper/scrapers/apple_scraper.py" ]]; then
    force_scrape_company "$APPLE_ID" "Apple" "apple_scraper" "AppleScraper"
else
    echo "⚠️ Apple scraper not yet implemented, using generic CompanyScraper instead"
    if [[ "$APPLE_ID" != "Not found" ]]; then
        force_scrape_company "$APPLE_ID" "Apple" "company_scraper" "CompanyScraper"
    fi
fi

if [[ "$GOOGLE_ID" != "Not found" ]]; then
    force_scrape_company "$GOOGLE_ID" "Google" "company_scraper" "CompanyScraper"
fi

if [[ "$MICROSOFT_ID" != "Not found" ]]; then
    force_scrape_company "$MICROSOFT_ID" "Microsoft" "company_scraper" "CompanyScraper"
fi

if [[ "$AMAZON_ID" != "Not found" ]]; then
    force_scrape_company "$AMAZON_ID" "Amazon" "company_scraper" "CompanyScraper"
fi

echo "Force scraping completed at $(date)"
echo "=== Done ==="
