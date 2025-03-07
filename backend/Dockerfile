# Backend Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -sSf https://astral.sh/uv/install.sh | bash

# Copy pyproject.toml 
COPY backend/pyproject.toml ./

# Install dependencies
RUN /root/.cargo/bin/uv pip install -e .

# Install Playwright browsers
RUN pip install playwright && playwright install chromium

# Copy source code
COPY backend/app ./app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_URL="postgresql://postgres:postgres@db:5432/janus"

# Expose the port
EXPOSE 8000

# Set entrypoint
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers"]