#!/bin/bash

echo "=== Processing Job Requirements ==="
echo "Starting at $(date)"

# Check if backend is running
if ! docker compose ps backend | grep -q "Up"; then
    echo "⚠️ Backend service is not running."
    echo "Starting backend service..."
    docker compose up -d backend
    sleep 5
fi

echo "Processing job requirements..."
docker compose exec backend python -m app.cli process --all

echo "Processing completed at $(date)"
echo "=== Done ==="
