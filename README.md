# BFIH Backend Implementation Guide

**Complete implementation of Option A: OpenAI Responses API backend for AI-Assisted Hypothesis Tournament Game**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Backend](#running-the-backend)
6. [API Reference](#api-reference)
7. [Integration Examples](#integration-examples)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This backend implementation provides:

✅ **BFIH Analysis Engine** - Bayesian Framework for Intellectual Honesty analysis using GPT-4o    
✅ **OpenAI Responses API Integration** - Web search, file search, code execution orchestrated autonomously    
✅ **REST API** - FastAPI service for game backend integration    
✅ **Production-Ready** - Storage, caching, error handling, logging    
✅ **Scalable** - Background task processing, database support, Docker deployment

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Game Frontend (React/Web App)                              │
└────────────────┬────────────────────────────────────────────┘
                 │ HTTP REST Calls
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  BFIH API Server (FastAPI)                                  │
│  • /api/bfih-analysis (POST)                                │
│  • /api/bfih-analysis/{id} (GET)                            │
│  • /api/scenario (POST/GET)                                 │
│  • /api/health                                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├─────────────────────────────────────────┐
                 │                                         │
                 ▼                                         ▼
        ┌────────────────────┐            ┌──────────────────────┐
        │ BFIH Orchestrator  │            │ Storage Manager      │
        │                    │            │                      │
        │ • Web Search       │            │ • File Storage (MVP) │
        │ • File Search      │            │ • PostgreSQL         │
        │ • Code Execution   │            │ • Redis Cache        │
        └────────────────────┘            └──────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ OpenAI Responses   │
        │ API (gpt-4o)       │
        │                    │
        │ ┌────────────────┐ │
        │ │ Web Search     │ │
        │ │ Tool           │ │
        │ └────────────────┘ │
        │ ┌────────────────┐ │
        │ │ File Search    │ │
        │ │ Tool           │ │
        │ └────────────────┘ │
        │ ┌────────────────┐ │
        │ │ Code           │ │
        │ │ Execution      │ │
        │ └────────────────┘ │
        └────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.9+
- OpenAI API key (get at https://platform.openai.com)
- Docker & Docker Compose (for containerized deployment)

### Local Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd bfih-backend

# 2. Run setup script
chmod +x setup_local.sh
./setup_local.sh

# 3. This will:
#    - Create Python virtual environment
#    - Install dependencies
#    - Create data directories
#    - Prompt for vector store setup
```

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Create data directories
mkdir -p data/analyses data/scenarios data/status logs
```

---

## Configuration

### 1. Set Your OpenAI API Key

Edit `.env`:

```bash
# Get your key from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### 2. Initialize Vector Store

The vector store holds your treatise and scenario templates.

```bash
# Interactive setup (recommended)
python setup_vector_store.py

# Follow prompts to:
# 1. Create new vector store
# 2. Upload treatise PDF
# 3. Upload scenario templates
# 4. Save vector store ID to .env
```

### 3. Verify Configuration

```bash
# Check that .env is properly set
cat .env | grep -E "OPENAI_API_KEY|TREATISE_VECTOR_STORE_ID"
```

---

## Running the Backend

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate

# Start API server
uvicorn bfih_api_server:app --reload

# Server will start at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### With Docker Compose

```bash
# Start all services (API, PostgreSQL, Redis, Adminer)
docker-compose up -d

# Check logs
docker-compose logs -f bfih-api

# Stop services
docker-compose down
```

### Run Tests

```bash
# Run all tests
pytest test_bfih_backend.py -v

# Run with coverage
pytest test_bfih_backend.py --cov=bfih --cov-report=html

# Run specific test
pytest test_bfih_backend.py::TestBFIHOrchestrator -v
```

---

## API Reference

### Health Check

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-06T12:00:00",
  "service": "BFIH Analysis API"
}
```

### Submit Analysis

```http
POST /api/bfih-analysis
Content-Type: application/json

{
  "scenario_id": "s_001_startup_success",
  "proposition": "Why did Startup X succeed?",
  "scenario_config": {
    "paradigms": [...],
    "hypotheses": [...],
    "priors_by_paradigm": {...}
  },
  "user_id": "user_123"
}
```

**Response:**
```json
{
  "analysis_id": "uuid-here",
  "status": "processing",
  "estimated_seconds": 45,
  "scenario_id": "s_001_startup_success"
}
```

### Get Analysis Result

```http
GET /api/bfih-analysis/{analysis_id}
```

**Response:**
```json
{
  "analysis_id": "uuid-here",
  "scenario_id": "s_001_startup_success",
  "proposition": "Why did Startup X succeed?",
  "status": "completed",
  "report": "# BFIH Analysis Report\n\n...",
  "posteriors": {
    "K1": {"H0": 0.10, "H1": 0.65, "H2": 0.25},
    "K2": {"H0": 0.10, "H1": 0.20, "H2": 0.70}
  },
  "metadata": {
    "model": "gpt-4o",
    "web_searches": 5,
    "file_searches": 2,
    "code_executions": 1
  },
  "created_at": "2026-01-06T12:00:00"
}
```

### Store Scenario

```http
POST /api/scenario
Content-Type: application/json

{
  "scenario_id": "s_001_startup_success",
  "title": "Startup Success Analysis",
  "domain": "business",
  "difficulty_level": "medium",
  "scenario_config": {...}
}
```

**Response:**
```json
{
  "scenario_id": "s_001_startup_success",
  "status": "stored",
  "created_at": "2026-01-06T12:00:00"
}
```

### Get Scenario

```http
GET /api/scenario/{scenario_id}
```

### List Scenarios

```http
GET /api/scenarios/list?limit=50&offset=0
```

### Analysis Status

```http
GET /api/analysis-status/{analysis_id}
```

**Response:**
```json
{
  "analysis_id": "uuid-here",
  "status": "processing",  // or "completed", "failed"
  "timestamp": "2026-01-06T12:00:00"
}
```

---

## Integration Examples

### JavaScript/React Frontend

```javascript
// Call BFIH analysis from React
async function submitBFIHAnalysis(scenario, proposition) {
  try {
    // 1. Submit analysis request
    const submitResponse = await fetch('http://localhost:8000/api/bfih-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario_id: scenario.id,
        proposition: proposition,
        scenario_config: scenario.config,
        user_id: currentUser.id
      })
    });
    
    const { analysis_id } = await submitResponse.json();
    
    // 2. Poll for result
    let result = null;
    let attempts = 0;
    while (!result && attempts < 60) {
      const statusResponse = await fetch(
        `http://localhost:8000/api/analysis-status/${analysis_id}`
      );
      const status = await statusResponse.json();
      
      if (status.status === 'completed') {
        const resultResponse = await fetch(
          `http://localhost:8000/api/bfih-analysis/${analysis_id}`
        );
        result = await resultResponse.json();
        break;
      }
      
      await new Promise(r => setTimeout(r, 1000)); // Wait 1 second
      attempts++;
    }
    
    return result;
  } catch (error) {
    console.error('BFIH analysis failed:', error);
    throw error;
  }
}
```

### Python Integration

```python
import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8000"

# Submit analysis
def submit_analysis(scenario_id, proposition, scenario_config):
    response = requests.post(
        f"{BACKEND_URL}/api/bfih-analysis",
        json={
            "scenario_id": scenario_id,
            "proposition": proposition,
            "scenario_config": scenario_config
        }
    )
    return response.json()

# Poll for result
def get_analysis_result(analysis_id, timeout=120):
    start = time.time()
    
    while time.time() - start < timeout:
        status_response = requests.get(
            f"{BACKEND_URL}/api/analysis-status/{analysis_id}"
        )
        status = status_response.json()
        
        if status['status'] == 'completed':
            result_response = requests.get(
                f"{BACKEND_URL}/api/bfih-analysis/{analysis_id}"
            )
            return result_response.json()
        
        time.sleep(1)
    
    raise TimeoutError(f"Analysis {analysis_id} timed out")

# Usage
scenario = {
    "id": "s_001",
    "config": {
        "paradigms": [...],
        "hypotheses": [...],
        "priors_by_paradigm": {...}
    }
}

result = submit_analysis("s_001", "Why did X succeed?", scenario["config"])
analysis_id = result["analysis_id"]

report = get_analysis_result(analysis_id)
print(report["report"])
```

---

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in environment
- [ ] Use strong, unique database password
- [ ] Configure CORS origins to specific domains
- [ ] Set up monitoring and alerting
- [ ] Enable HTTPS/TLS
- [ ] Set up automated backups
- [ ] Configure rate limiting
- [ ] Use environment-specific .env files

### Deploy to Production

```bash
# 1. Build Docker image
docker build -t bfih-backend:latest .

# 2. Start with docker-compose
docker-compose -f docker-compose.yml up -d

# 3. Run migrations (if using database)
docker-compose exec bfih-api python -m alembic upgrade head

# 4. Check logs
docker-compose logs -f bfih-api

# 5. Verify health
curl http://localhost:8000/api/health
```

### Environment-Specific Configuration

```bash
# Development
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
docker-compose -f docker-compose.yml up

# Staging
export ENVIRONMENT=staging
export LOG_LEVEL=INFO
docker-compose -f docker-compose.yml up

# Production
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
docker-compose -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

### Issue: "OPENAI_API_KEY not set"

**Solution:**
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Set it if missing
echo "OPENAI_API_KEY=sk-proj-your-key" >> .env

# Reload
source .env
```

### Issue: Vector store not found

**Solution:**
```bash
# Run setup script
python setup_vector_store.py

# Or manually set
echo "TREATISE_VECTOR_STORE_ID=vs_xxxxx" >> .env
```

### Issue: API returns 500 error

**Solution:**
```bash
# Check logs
docker-compose logs bfih-api

# Or local logs
tail -f logs/bfih_backend.log

# Verify OpenAI API is accessible
python -c "from openai import OpenAI; print(OpenAI(api_key='...').models.list())"
```

### Issue: Analysis takes too long

**Solution:**
- Check OpenAI API status (https://status.openai.com)
- Increase `ANALYSIS_TIMEOUT_SECONDS` in .env
- Reduce number of web searches in prompt

### Issue: Vector store file not uploading

**Solution:**
```bash
# Check file exists and is readable
ls -la Intellectual-Honesty_rev-4.pdf

# Try uploading manually
python setup_vector_store.py

# Check file size (should be <512MB)
du -h Intellectual-Honesty_rev-4.pdf
```

---

## File Structure

```
bfih-backend/
├── bfih_orchestrator.py         # Main BFIH analysis engine
├── bfih_api_server.py           # FastAPI REST API
├── bfih_storage.py              # Storage abstraction layer
├── setup_vector_store.py        # Vector store initialization
├── test_bfih_backend.py         # Comprehensive tests
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container definition
├── docker-compose.yml           # Multi-container setup
├── setup_local.sh               # Local setup script
├── README.md                    # This file
├── data/
│   ├── analyses/               # Analysis results (JSON)
│   ├── scenarios/              # Scenario configs (JSON)
│   └── status/                 # Analysis status tracking
└── logs/
    └── bfih_backend.log        # Application logs
```

---

## Support & Documentation

- **OpenAI API Docs:** https://platform.openai.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Responses API:** https://platform.openai.com/docs/guides/responses

---

## License

[Your License Here]

---

**Generated:** January 2026  
**Version:** 1.0.0  
**Status:** Production Ready
