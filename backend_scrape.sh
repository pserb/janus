#!/bin/bash

echo "scraping..."
docker compose exec backend python -m app.cli scrape
echo "scraping done."