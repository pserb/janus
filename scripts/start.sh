#!/bin/bash

echo "=== Starting Janus Application ==="
echo "Starting at $(date)"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start the containers
echo "Building and starting Docker containers..."
docker compose build
docker compose up -d

# Wait for services to be fully up
echo "Waiting for services to initialize..."
sleep 5

# Check if services are up
if ! docker compose ps backend | grep -q "Up"; then
    echo "⚠️ Backend service failed to start."
    echo "Checking logs for errors:"
    docker compose logs backend
    echo "Try running: ./scripts/restart_backend.sh --rebuild"
else
    echo "✅ Backend service is running."
fi

if ! docker compose ps frontend | grep -q "Up"; then
    echo "⚠️ Frontend service failed to start."
    echo "Checking logs for errors:"
    docker compose logs frontend
    echo "Try running: ./scripts/restart_frontend.sh --rebuild"
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
echo ""
echo "To see logs: ./scripts/logs.sh"
echo "To seed the database: ./scripts/seed.sh"

echo "Started at $(date)"
echo "=== Done ==="

# Make all scripts executable
chmod +x scripts/*.sh
