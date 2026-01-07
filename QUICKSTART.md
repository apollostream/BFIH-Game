# QUICK START: BFIH Backend Implementation

**Get up and running in 5 minutes**

---

## ⚡ TL;DR (60 seconds)

```bash
# 1. Clone and setup
git clone <repo> && cd bfih-backend
./setup_local.sh

# 2. Set your OpenAI API key
nano .env  # Add OPENAI_API_KEY=sk-proj-...

# 3. Initialize vector store
python setup_vector_store.py

# 4. Start server
uvicorn bfih_api_server:app --reload

# 5. Test it
curl http://localhost:8000/api/health
```

---

## 📦 Step 1: Installation (2 min)

### Option A: Local Development

```bash
# Setup (automatic)
chmod +x setup_local.sh
./setup_local.sh

# Or manual setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir -p data/{analyses,scenarios,status} logs
```

### Option B: Docker

```bash
# Just requires Docker and API key
docker-compose up -d
```

---

## 🔑 Step 2: API Key & Vector Store (2 min)

### Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy it

### Configure Backend

```bash
# Edit .env
OPENAI_API_KEY=sk-proj-your-key-here

# Initialize vector store (interactive)
python setup_vector_store.py
# Choose option 1, select PDF to upload, done!
```

---

## 🚀 Step 3: Start Server (1 min)

### Local

```bash
source venv/bin/activate
uvicorn bfih_api_server:app --reload

# Opens at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Docker

```bash
docker-compose up -d bfih-api
docker-compose logs -f bfih-api
```

---

## ✅ Step 4: Verify & Test (30 sec)

```bash
# Health check
curl http://localhost:8000/api/health

# Response should be:
# {"status":"healthy","timestamp":"...","service":"BFIH Analysis API"}
```

---

## 🎮 Step 5: First Analysis (5-60 sec)

### Python

```python
import asyncio
from bfih_client import BFIHClient

async def main():
    client = BFIHClient("http://localhost:8000")
    
    scenario_config = {
        "paradigms": [
            {"id": "K1", "name": "Paradigm A", "description": "View 1"},
            {"id": "K2", "name": "Paradigm B", "description": "View 2"}
        ],
        "hypotheses": [
            {"id": "H1", "name": "Cause A", "domains": [], "associated_paradigms": ["K1"]},
            {"id": "H2", "name": "Cause B", "domains": [], "associated_paradigms": ["K2"]}
        ],
        "priors_by_paradigm": {
            "K1": {"H1": 0.7, "H2": 0.3},
            "K2": {"H1": 0.3, "H2": 0.7}
        }
    }
    
    result = await client.submit_analysis(
        scenario_id="test_001",
        proposition="Which cause is more likely?",
        scenario_config=scenario_config,
        poll=True
    )
    
    print("Report:", result['report'][:200])
    print("Posteriors:", result['posteriors'])

asyncio.run(main())
```

### cURL

```bash
curl -X POST http://localhost:8000/api/bfih-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "test_001",
    "proposition": "Which cause is more likely?",
    "scenario_config": {
      "paradigms": [
        {"id": "K1", "name": "A", "description": "View A"}
      ],
      "hypotheses": [
        {"id": "H1", "name": "Cause A", "domains": [], "associated_paradigms": ["K1"]}
      ],
      "priors_by_paradigm": {"K1": {"H1": 1.0}}
    }
  }'

# Response:
# {
#   "analysis_id": "uuid-here",
#   "status": "processing",
#   "estimated_seconds": 45
# }

# Get result
curl http://localhost:8000/api/bfih-analysis/uuid-here
```

---

## 📋 File Structure

```
bfih-backend/
├── bfih_orchestrator.py    ← Main BFIH engine (don't touch, it works!)
├── bfih_api_server.py      ← REST API (don't touch, it works!)
├── bfih_storage.py         ← Data storage (don't touch, it works!)
├── bfih_client.py          ← Python client SDK (use this!)
├── setup_vector_store.py   ← Initialize vector store (run once)
├── test_bfih_backend.py    ← Tests (run: pytest)
├── .env                    ← Your secrets (EDIT THIS: add API key)
├── .env.example            ← Template (don't edit)
├── requirements.txt        ← Dependencies (don't touch)
├── Dockerfile              ← Docker config (don't touch)
├── docker-compose.yml      ← Multi-container (don't touch)
├── README.md               ← Full documentation
└── data/                   ← Analysis results (auto-created)
```

**Key files to know:**
- `.env` - Add your OpenAI API key here
- `bfih_client.py` - Use to integrate with your game
- `setup_vector_store.py` - Run once to initialize

---

## 🔗 Integration with Game Frontend

### React Example

```javascript
// Call from your React game
async function analyzeHypothesis(scenario, proposition) {
  const response = await fetch('http://localhost:8000/api/bfih-analysis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scenario_id: scenario.id,
      proposition: proposition,
      scenario_config: scenario.config
    })
  });
  
  const { analysis_id } = await response.json();
  
  // Poll for result
  let result;
  while (!result) {
    const statusRes = await fetch(`http://localhost:8000/api/analysis-status/${analysis_id}`);
    const status = await statusRes.json();
    
    if (status.status === 'completed') {
      const resultRes = await fetch(`http://localhost:8000/api/bfih-analysis/${analysis_id}`);
      result = await resultRes.json();
    }
    
    await new Promise(r => setTimeout(r, 2000)); // Check every 2s
  }
  
  return result;
}
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `OPENAI_API_KEY not found` | Add to .env: `OPENAI_API_KEY=sk-proj-...` |
| `Vector store not found` | Run: `python setup_vector_store.py` |
| `Connection refused` | Run: `uvicorn bfih_api_server:app --reload` |
| `Port 8000 in use` | Use different port: `--port 8001` |
| `ModuleNotFoundError: openai` | Run: `pip install -r requirements.txt` |

---

## 📚 Next Steps

1. **Read Full Docs** → `README.md`
2. **Run Tests** → `pytest test_bfih_backend.py`
3. **Explore API** → http://localhost:8000/docs (Swagger UI)
4. **Integrate Frontend** → Use `bfih_client.py` or REST calls
5. **Deploy** → Use `docker-compose` for production

---

## ⚙️ Common Commands

```bash
# Start server (local)
uvicorn bfih_api_server:app --reload

# Start server (Docker)
docker-compose up -d

# Stop services (Docker)
docker-compose down

# Check logs (Docker)
docker-compose logs -f bfih-api

# Run tests
pytest test_bfih_backend.py -v

# Setup vector store
python setup_vector_store.py

# Interactive Python shell with client
python -c "from bfih_client import BFIHClientSync; client = BFIHClientSync(); print(client.health_check())"
```

---

## 💡 Tips

✅ **Check health before submitting analyses:**
```python
client = BFIHClient()
if await client.health_check():
    result = await client.submit_analysis(...)
```

✅ **Use the API docs:**
- Local: http://localhost:8000/docs
- Swagger UI is interactive - try endpoints here first

✅ **Save scenario configs:**
```python
# Store once, reuse many times
client.store_scenario(scenario_config)
saved = client.get_scenario("s_001")
```

✅ **Async > Sync:**
- Use `BFIHClient` (async) in production
- Use `BFIHClientSync` (sync) for scripts/testing

---

## 🎉 That's it!

You now have a fully functional BFIH backend. Start submitting analyses to your game!

**Need help?** Check `README.md` for full documentation or see code comments in Python files.
