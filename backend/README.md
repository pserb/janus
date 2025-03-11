# Janus Backend

This is the backend service for Janus, a high-performance job tracking application designed specifically for software and hardware engineering roles.

## Features

- Fast and efficient web scraping of job listings from multiple sources
- Structured data storage with PostgreSQL
- RESTful API for job retrieval with filtering and pagination
- Real-time updates via WebSockets
- ML-based job requirement summarization
- Company logo acquisition
- Command-line interface for management tasks

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (if running locally without Docker)

### Running with Docker

The simplest way to run the backend is using Docker Compose:

```bash
# From the project root directory
docker compose up -d backend
```

This will start the backend service on port 8000, along with the required PostgreSQL database.

### Running Locally

If you prefer to run the backend locally:

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload
```

### Initializing the Database

After starting the backend service, you'll want to seed the database with some initial data:

```bash
# With Docker
docker compose exec backend python -m app.cli seed

# Locally
python -m app.cli seed
```

## CLI Tool

The Janus backend includes a command-line interface (CLI) for common management tasks:

```bash
# To see all available commands
python -m app.cli --help

# Run job scrapers
python -m app.cli scrape

# Process job requirements
python -m app.cli process

# Fetch company logos
python -m app.cli logos

# View job statistics
python -m app.cli stats

# Seed the database with sample data
python -m app.cli seed

# Clear database data
python -m app.cli clear --jobs  # Clear all jobs
python -m app.cli clear --all   # Clear all data
```

## API Endpoints

The backend exposes the following RESTful API endpoints:

### Jobs

- `GET /api/jobs`: List jobs with filtering and pagination
  - Query parameters: page, page_size, category, company_id, is_active, since, search

- `GET /api/jobs/{job_id}`: Get a specific job by ID

- `GET /api/jobs/recent/since`: Get jobs discovered after a specific timestamp

### Companies

- `GET /api/companies`: List companies
  - Query parameters: page, page_size, is_active

- `GET /api/companies/{company_id}`: Get a specific company by ID

- `GET /api/companies/{company_id}/jobs`: Get all jobs for a specific company

### Statistics

- `GET /api/stats`: Get job statistics

## WebSocket API

The backend also provides a WebSocket API for real-time updates:

- `ws://localhost:8000/ws`: WebSocket endpoint

Events:
- `jobs:new`: Sent when new jobs are discovered

## Architecture

The backend follows a modular architecture with the following components:

- **API Layer**: FastAPI endpoints for job retrieval
- **Database Layer**: SQLAlchemy models and CRUD operations with PostgreSQL
- **Scraper Module**: Web scraping components for job discovery
- **ML Module**: Job requirement extraction and summarization
- **WebSocket Module**: Real-time updates for clients

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
