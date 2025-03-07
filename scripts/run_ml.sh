#!/bin/bash

echo "=== Janus ML Pipeline Script ==="
echo "Starting ML pipeline at $(date)"

# Check if backend container is running
CONTAINER_RUNNING=$(docker compose ps -q backend)
if [ -z "$CONTAINER_RUNNING" ]; then
    echo "⚠️ Backend container is not running. Starting it now..."
    docker compose up -d backend
    
    # Wait for container to be fully up
    echo "Waiting for backend to start..."
    sleep 10
fi

echo "Running ML processing on unprocessed jobs..."
docker compose exec -T backend python3 -c "
import asyncio
from app.ml.processor import process_single_batch

async def run():
    count = await process_single_batch()
    print(f'Processed {count} jobs')

asyncio.run(run())
"

if [ $? -ne 0 ]; then
    echo "❌ ML processing failed"
    echo "Check the backend logs for more details:"
    echo "  docker compose logs backend"
else
    echo "✅ ML processing completed successfully"
fi

# Optionally run scraper to get new jobs
if [ "$1" == "--with-scrape" ]; then
    echo "Running job scraper to fetch new listings..."
    docker compose exec -T backend python -m app.cli scrape
    
    if [ $? -ne 0 ]; then
        echo "❌ Scraper run failed"
    else
        echo "✅ Scraper run completed successfully"
    fi
fi

echo "ML pipeline completed at $(date)"
echo "=== Done ==="