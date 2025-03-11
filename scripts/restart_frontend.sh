#!/bin/bash

echo "=== Restarting Frontend Service ==="
echo "Starting at $(date)"

# Parse arguments
REBUILD=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --rebuild) REBUILD=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

if [ "$REBUILD" = true ]; then
    echo "Rebuilding frontend container..."
    docker compose build frontend
fi

echo "Stopping frontend container..."
docker compose stop frontend

echo "Starting frontend container..."
docker compose up -d frontend

echo "Checking frontend status..."
sleep 3
if docker compose ps frontend | grep -q "Up"; then
    echo "✅ Frontend service is running."
    echo "Frontend available at: http://localhost:3000"
else
    echo "⚠️ Frontend service failed to start."
    echo "Checking logs for errors:"
    docker compose logs frontend
fi

echo "Restarted at $(date)"
echo "=== Done ==="
