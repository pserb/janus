#!/bin/bash

echo "=== Setting Up ML-Based Scraping and Processing Pipeline ==="
echo "Starting setup at $(date)"

# Ensure we have the required directories
echo "Making sure ml directory exists..."
mkdir -p ml_pipeline

# Create the ML processor
echo "Creating ML job processor..."
cat ml-job-processor.py > ml_pipeline/ml_job_processor.py

# Create the ML-based scraper manager
echo "Creating ML-based scraper manager..."
cat ml-scraper-manager.py > ml_pipeline/ml_manager.py

# Create the ML CLI command
echo "Creating ML CLI command..."
cat ml-cli-command.py > ml_pipeline/cli_ml.py

# Create Dockerfile for installing ML dependencies
echo "Creating Dockerfile for ML dependencies..."
cat << 'EOF' > ml_pipeline/Dockerfile.ml
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install ML dependencies
RUN pip install --no-cache-dir \
    tensorflow \
    transformers[tf] \
    sentence-transformers \
    torch \
    scikit-learn \
    nltk \
    numpy

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Create app directory
WORKDIR /app

CMD ["bash"]
EOF

# Create script to install ML dependencies in the existing container
echo "Creating script to install ML dependencies..."
cat << 'EOF' > ml_pipeline/install_dependencies.sh
#!/bin/bash

# Stop the backend container
docker compose stop backend

# Create a temporary container to install dependencies
echo "Creating temporary container to install ML dependencies..."
docker build -t janus-ml-deps -f ml_pipeline/Dockerfile.ml .
docker create --name ml-temp janus-ml-deps

# Copy ML files to the backend container
echo "Copying ML files to backend container..."
BACKEND_CONTAINER=$(docker compose ps -q backend)
docker cp ml_pipeline/ml_job_processor.py $BACKEND_CONTAINER:/app/app/ml/
docker cp ml_pipeline/ml_manager.py $BACKEND_CONTAINER:/app/app/scraper/
docker cp ml_pipeline/cli_ml.py $BACKEND_CONTAINER:/app/app/

# Install ML dependencies in the backend container
echo "Installing ML dependencies in the backend container..."
docker compose exec -T backend pip install tensorflow transformers torch sentence-transformers scikit-learn nltk
docker compose exec -T backend python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Restart the backend container
echo "Restarting backend container..."
docker compose start backend

# Clean up
docker rm ml-temp
docker rmi janus-ml-deps

echo "ML dependencies installed successfully"
EOF

# Make install script executable
chmod +x ml_pipeline/install_dependencies.sh

# Create a README
echo "Creating README..."
cat << 'EOF' > ml_pipeline/README.md
# ML-Based Processing Pipeline for Janus

This directory contains a complete ML-based solution for processing job listings without regex or pattern matching.

## Components

1. `ml_job_processor.py` - Pure ML-based job processor using:
   - Transformer models for text classification
   - Sentence embeddings for semantic similarity
   - Zero-shot classification for requirement categorization
   - NLP techniques for text extraction

2. `ml_manager.py` - ML-based scraper manager that integrates with existing scrapers

3. `cli_ml.py` - CLI command to run the ML pipeline

## Installation

Run the installation script to set up the ML dependencies:

```bash
./install_dependencies.sh
```

This will:
1. Install required ML libraries in the backend container
2. Copy ML scripts to the appropriate locations

## Usage

After installation, you can use the ML pipeline with:

```bash
# Run the ML-based scraper
docker compose exec backend python -m app.cli_ml scrape

# Reprocess all existing jobs with ML
docker compose exec backend python -m app.cli_ml process

# Reprocess jobs for a specific company
docker compose exec backend python -m app.cli_ml company "Apple"
```

## How It Works

Unlike the regex-based approach, this pipeline uses ML to:

1. Extract requirements sections based on semantic similarity
2. Classify jobs as software/hardware using zero-shot classification
3. Categorize requirements using transformer models
4. Format summaries with ML-detected structure

The ML models automatically adapt to different input formats without needing hard-coded patterns.
EOF

# Create a script to run the ML pipeline
echo "Creating run script..."
cat << 'EOF' > run_ml_pipeline.sh
#!/bin/bash

echo "=== Running ML-Based Pipeline ==="
echo "Starting at $(date)"

# Run ML-based scraper
echo "Running ML-based scraper..."
docker compose exec backend python -m app.cli_ml scrape

echo "ML pipeline completed at $(date)"
echo "=== Done ==="
EOF

chmod +x run_ml_pipeline.sh

echo "ML pipeline setup completed at $(date)"
echo "To install dependencies, run: ./ml_pipeline/install_dependencies.sh"
echo "To run the ML pipeline, run: ./run_ml_pipeline.sh"
echo "=== Done ==="
