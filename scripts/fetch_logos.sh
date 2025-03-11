#!/bin/bash

echo "=== Fetching Company Logos ==="
echo "Starting at $(date)"

# Check if backend is running
if ! docker compose ps backend | grep -q "Up"; then
    echo "⚠️ Backend service is not running."
    echo "Starting backend service..."
    docker compose up -d backend
    sleep 5
fi

echo "Fetching company logos..."
docker compose exec backend python -m app.cli logos --all

echo "Logo fetching completed at $(date)"
echo "=== Done ==="
