#!/bin/bash

echo "=== Janus Production Launch ==="
echo "Starting production launch at $(date)"
echo "This script will build, start, and run the real production pipeline with NO fake data."

# Make sure all scripts are executable
chmod +x scripts/*.sh

# Step 1: Check if Docker is running
echo "Step 1: Verifying Docker is running..."
if ! docker info > /dev/null 2>&1; then
    echo "⚠️ Docker is not running. Please start Docker and try again."
    exit 1
fi
echo "✅ Docker is running."

# Step 2: Build and start the containers
echo "Step 2: Building and starting containers..."
docker compose down
docker compose build
docker compose up -d
echo "✅ Containers started."

# Step 3: Wait for services to be up
echo "Step 3: Waiting for services to initialize..."
sleep 10

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

# Step 4: Initialize company sources (real companies, not sample data)
echo "Step 4: Initializing company data sources..."
docker compose exec -T backend python -m app.cli init_sources
echo "✅ Company sources initialized."

# Step 5: Run the scrapers to get REAL job listings
echo "Step 5: Running job scrapers to fetch latest REAL job listings..."
docker compose exec -T backend python -m app.cli scrape
echo "✅ Job scraping completed."

# Step 6: Process job requirements
echo "Step 6: Processing job requirements..."
docker compose exec -T backend python -m app.cli process --all
echo "✅ Job requirements processed."

# Step 7: Fetch company logos
echo "Step 7: Fetching company logos..."
docker compose exec -T backend python -m app.cli logos --all
echo "✅ Company logos fetched."

# Step 8: Display stats
echo "Step 8: Displaying job statistics..."
docker compose exec -T backend python -m app.cli stats

# Final output
echo ""
echo "===================================================="
echo "🚀 JANUS PRODUCTION PIPELINE SUCCESSFULLY LAUNCHED!"
echo "===================================================="
echo ""
echo "Access your application at:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"
echo ""
echo "Production launch finished at $(date)"
echo "=== Done ==="
