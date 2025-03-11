#!/bin/bash

echo "=== Restarting All Janus Services ==="
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
    echo "Rebuilding all containers..."
    docker compose build
fi

echo "Stopping all containers..."
docker compose down

echo "Starting all containers..."
docker compose up -d

echo "Checking service status..."
sleep 5

if ! docker compose ps backend | grep -q "Up"; then
    echo "⚠️ Backend service failed to start."
    echo "Checking logs for errors:"
    docker compose logs backend
else
    echo "✅ Backend service is running."
fi

if ! docker compose ps frontend | grep -q "Up"; then
    echo "⚠️ Frontend service failed to start."
    echo "Checking logs for errors:"
    docker compose logs frontend
else
    echo "✅ Frontend service is running."
fi

if ! docker compose ps db | grep -q "Up"; then
    echo "⚠️ Database service failed to start."
    echo "Checking logs for errors:"
    docker compose logs db
else
    echo "✅ Database service is running."
fi

echo ""
echo "Application services:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- API Documentation: http://localhost:8000/docs"

echo "Restarted at $(date)"
echo "=== Done ==="
