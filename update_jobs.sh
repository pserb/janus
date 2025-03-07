#!/bin/bash

echo "=== Janus Job Update Script ==="
echo "Starting job update process at $(date)"

echo "Step 1: Running scrapers to fetch new jobs..."
docker compose exec backend python -m app.cli scrape

echo "Step 2: Ensuring all jobs have properly formatted requirements..."
docker compose exec backend python -m app.cli process

echo "Job update complete at $(date)"
echo "=== Done ==="
