#!/bin/bash

echo "=== Seeding Janus Database ==="
echo "Starting at $(date)"

# Check if backend is running
if ! docker compose ps backend | grep -q "Up"; then
    echo "⚠️ Backend service is not running."
    echo "Starting backend service..."
    docker compose up -d backend
    sleep 5
fi

echo "Running database seed command..."
docker compose exec backend python -m app.cli seed

echo "Seeding completed at $(date)"
echo "=== Done ==="
