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

# Copy treatise PDF for user vector store setup
COPY Intellectual-Honesty_rev-4.pdf ./assets/

# Create data directory
RUN mkdir -p ./data/analyses ./data/scenarios ./data/status ./logs ./assets

# Default port (Cloud Run/Railway override with $PORT)
ENV PORT=8000
EXPOSE $PORT

# ============================================================================
# USER SETUP FLOW:
# ============================================================================
# 1. User visits the deployed app URL
# 2. First-time users see a setup modal asking for their OpenAI API key
# 3. Backend creates a vector store using the user's API key
# 4. Backend uploads the bundled treatise PDF to their vector store
# 5. Credentials are saved in the user's browser (localStorage)
# 6. User is ready to use the app!
#
# The treatise PDF is bundled in ./assets/ and used for all user setups.
# ============================================================================

# Health check (uses PORT env variable)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; import requests; requests.get(f'http://localhost:{os.environ.get(\"PORT\", 8000)}/api/health')"

# Run server (Cloud Run/Railway provides PORT, defaults to 8000 locally)
CMD python -m uvicorn bfih_api_server:app --host 0.0.0.0 --port $PORT
