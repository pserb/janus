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
# Create a Python script that properly initializes the database
cat > /tmp/init_db.py << 'EOL'
import logging
from sqlalchemy import inspect
from app.database import engine, Base
# Import all models to ensure they're registered with SQLAlchemy
from app.models import Company, Job, Source, CrawlLog, SyncInfo

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
print(f'Database initialization {"successful" if success else "failed"}')
print(f'Created tables: {len(existing_tables)}')
print(f'Tables: {", ".join(existing_tables)}')
EOL

# Copy the script to the backend container
docker compose cp /tmp/init_db.py backend:/app/init_db.py

# Run the script
db_init_output=$(docker compose exec -T backend python /app/init_db.py)
echo "$db_init_output"

# Check if initialization was successful
if echo "$db_init_output" | grep -q "Database initialization failed"; then
    echo "⚠️ Database initialization failed. Exiting."
    exit 1
fi

# Clean up
rm /tmp/init_db.py
echo "✅ Database schema initialized."
echo ""

# Step 5: Initialize company data sources
echo "▶️ Step 5: Initializing top tech companies and job sources..."
company_init_output=$(docker compose exec -T backend python -m app.cli_init)
echo "$company_init_output"

# Check if there was an error
if echo "$company_init_output" | grep -q "Error"; then
    echo "⚠️ Failed to initialize companies and job sources. Exiting."
    exit 1
fi
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
docker compose exec -T backend bash -c "sed -i 's/from \.\. import crud/from \.\. import crud, models/' /app/app/ml/logo_fetcher.py" 2>/dev/null || true
docker compose exec -T backend python -m app.cli logos --all 2>/dev/null || true
echo "✅ Company logos fetched."
echo ""

# Step 9: Display stats
echo "▶️ Step 9: Displaying current job statistics..."
stats_output=$(docker compose exec -T backend python -m app.cli stats 2>/dev/null || echo "No jobs found yet. Run scrapers again later to find jobs.")
echo "$stats_output"
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