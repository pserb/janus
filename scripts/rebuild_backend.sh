#!/bin/bash

echo "rebuilding backend..."
docker compose down
docker compose build backend
docker compose up -d
echo "backend rebuilt."