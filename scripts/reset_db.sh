#!/bin/bash

echo "=== Reset Janus Database ==="
echo "WARNING: This will delete all your data!"
echo "Press CTRL+C to cancel or ENTER to continue..."
read

# Stop the containers
echo "Stopping containers..."
docker compose down

# Remove the PostgreSQL volume
echo "Removing PostgreSQL volume..."
docker volume rm janus_postgres_data || true

# Start the containers again
echo "Starting containers..."
docker compose up -d

echo "Database has been reset."
echo "You may want to run './scripts/seed.sh' to populate with sample data."
echo "=== Done ==="
