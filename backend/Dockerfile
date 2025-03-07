# Backend Dockerfile
FROM python:3.12

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxi6 libxtst6 libnss3 libcups2 libxss1 libxrandr2 \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 libpangocairo-1.0-0 \
    libgtk-3-0 libgbm1 libxshmfence1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml 
COPY backend/pyproject.toml ./

# Install dependencies
RUN pip install -e .

# Install Playwright browsers
RUN pip install playwright scikit-learn && playwright install chromium

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
