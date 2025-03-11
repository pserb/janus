#!/bin/bash

echo "=== Janus Job Statistics ==="

# Check if backend is running
if ! docker compose ps backend | grep -q "Up"; then
    echo "⚠️ Backend service is not running."
    echo "Starting backend service..."
    docker compose up -d backend
    sleep 5
fi

echo "Fetching job statistics..."
docker compose exec backend python -m app.cli stats

echo "=== Done ==="
