FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bfih_*.py ./
COPY setup_vector_store.py ./

# Create data directory
RUN mkdir -p ./data/analyses ./data/scenarios ./data/status ./logs

# Default port (Railway overrides with $PORT)
ENV PORT=8000
EXPOSE $PORT

# Health check (uses PORT env variable)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; import requests; requests.get(f'http://localhost:{os.environ.get(\"PORT\", 8000)}/api/health')"

# Run server (Railway provides PORT, defaults to 8000 locally)
CMD python -m uvicorn bfih_api_server:app --host 0.0.0.0 --port $PORT
