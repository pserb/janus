#!/bin/bash

echo "=== Restarting Backend Service ==="
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
    echo "Rebuilding backend container..."
    docker compose build backend
fi

echo "Stopping backend container..."
docker compose stop backend

echo "Starting backend container..."
docker compose up -d backend

echo "Checking backend status..."
sleep 3
if docker compose ps backend | grep -q "Up"; then
    echo "✅ Backend service is running."
    echo "API available at: http://localhost:8000"
    echo "API Documentation: http://localhost:8000/docs"
else
    echo "⚠️ Backend service failed to start."
    echo "Checking logs for errors:"
    docker compose logs backend
fi

echo "Restarted at $(date)"
echo "=== Done ==="
