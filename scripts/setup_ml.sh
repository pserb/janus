#!/bin/bash

echo "=== Janus ML Setup Script ==="
echo "Starting setup at $(date)"

# Ensure necessary directories exist
if [ ! -d "backend/app/ml" ]; then
    echo "Creating ML directories..."
    mkdir -p backend/app/ml/models
    mkdir -p backend/app/ml/processors
    mkdir -p backend/app/ml/utils
fi

echo "Stopping backend container if running..."
docker compose stop backend || true

echo "Rebuilding backend container with ML support..."
docker compose build backend

echo "Starting backend container..."
docker compose up -d backend

echo "Verifying ML dependencies in container..."
docker compose exec -T backend python3 -c "
try:
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    print('✓ NLTK successfully installed and data downloaded')
except ImportError:
    print('✗ NLTK not installed')
    exit(1)

try:
    import sklearn
    print('✓ scikit-learn successfully installed')
except ImportError:
    print('✗ scikit-learn not installed')
    exit(1)

try:
    import torch
    print('✓ PyTorch successfully installed')
except ImportError:
    print('✗ PyTorch not installed')
    print('Warning: Some advanced ML features will be unavailable')

try:
    import transformers
    print('✓ Transformers successfully installed')
except ImportError:
    print('✗ Transformers not installed')
    print('Warning: Some advanced ML features will be unavailable')
"

if [ $? -ne 0 ]; then
    echo "❌ ML dependencies verification failed"
    echo "You can still use the system with reduced ML functionality"
else
    echo "✅ ML dependencies successfully installed"
fi

echo "Testing ML processor..."
docker compose exec -T backend python3 -c "
import asyncio
from app.ml.processor import process_single_batch

async def test():
    try:
        await process_single_batch()
        print('✓ ML processor test successful')
    except Exception as e:
        print(f'✗ ML processor test failed: {str(e)}')
        exit(1)

asyncio.run(test())
"

if [ $? -ne 0 ]; then
    echo "❌ ML processor test failed"
    echo "Please check the backend logs for more details"
else
    echo "✅ ML processor test successful"
fi

echo "ML setup completed at $(date)"
echo "=== Done ==="