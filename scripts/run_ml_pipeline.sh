#!/bin/bash

echo "=== Running ML-Based Pipeline ==="
echo "Starting at $(date)"

# Run ML-based scraper
echo "Running ML-based scraper..."
docker compose exec backend python -m app.cli_ml scrape

echo "ML pipeline completed at $(date)"
echo "=== Done ==="
