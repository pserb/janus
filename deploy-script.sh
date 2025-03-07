#!/bin/bash
# Deployment script for Janus Internship Tracker

set -e

echo "=== Janus Deployment Script ==="
echo "This script will deploy the Janus application."

# Check if Docker is installed
if ! [ -x "$(command -v docker)" ]; then
  echo "Error: Docker is not installed." >&2
  exit 1
fi

# Check if Docker Compose is installed
if ! [ -x "$(command -v docker-compose)" ]; then
  echo "Error: Docker Compose is not installed." >&2
  exit 1
fi

# Pull latest changes if in a Git repository
if [ -d .git ]; then
  echo "=== Pulling latest changes ==="
  git pull
fi

# Build and start the application
echo "=== Building and starting the application ==="
docker-compose build
docker-compose up -d

# Wait for the backend to start
echo "=== Waiting for the backend to start ==="
sleep 5

# Seed the database if specified
if [ "$1" == "--seed" ]; then
  echo "=== Seeding the database ==="
  docker-compose exec backend python -m app.cli seed
fi

echo "=== Deployment Complete ==="
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"