#!/bin/bash

echo "=== Running Janus Job Scrapers ==="
echo "Starting at $(date)"

# Check if backend is running
if ! docker compose ps backend | grep -q "Up"; then
    echo "⚠️ Backend service is not running."
    echo "Starting backend service..."
    docker compose up -d backend
    sleep 5
fi

echo "Running job scrapers..."
docker compose exec backend python -m app.cli scrape

echo "Scraping completed at $(date)"
echo "=== Done ==="
