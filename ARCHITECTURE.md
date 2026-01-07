# Architecture & Deployment Reference

## System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        GAME FRONTEND (React/Web)                           │
│                                                                             │
│  ┌─────────────────┐      ┌──────────────────┐      ┌────────────────┐    │
│  │  Scenario UI    │      │  Tournament Game │      │  Results View  │    │
│  └────────┬────────┘      └────────┬─────────┘      └────────┬───────┘    │
│           │                       │                         │              │
│           └───────────────────────┼─────────────────────────┘              │
│                                   │ HTTPS                                   │
└───────────────────────────────────┼──────────────────────────────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │   BFIH API Server (FastAPI)    │
                    │   Port 8000 / Load Balancer    │
                    │                                │
                    │  ┌──────────────────────────┐  │
                    │  │ Endpoints:               │  │
                    │  │ POST   /api/bfih-...     │  │
                    │  │ GET    /api/bfih-.../{id}│  │
                    │  │ GET    /api/health       │  │
                    │  │ POST   /api/scenario     │  │
                    │  └──────────────────────────┘  │
                    └───────────────┬────────────────┘
                                    │
                    ┌───────────────┴─────────────────┬──────────────────┐
                    │                                 │                  │
        ┌───────────▼──────────┐        ┌────────────▼─────────┐   ┌───▼────────┐
        │  BFIH Orchestrator   │        │  Storage Manager    │   │  Logging   │
        │                      │        │                     │   │            │
        │ • Web Search Tool    │        │ • File Storage      │   │ • Errors   │
        │ • File Search Tool   │        │ • PostgreSQL        │   │ • Metrics  │
        │ • Code Execution     │        │ • Redis Cache       │   │ • Traces   │
        │                      │        └──────────┬──────────┘   └───────────┘
        └───────────┬──────────┘                   │
                    │                              │
        ┌───────────▼──────────────────────────────▼──────────┐
        │                                                       │
        │      OpenAI API (Responses API - gpt-4o)            │
        │                                                       │
        │  ┌─────────────────┐  ┌──────────────┐  ┌─────────┐│
        │  │ Web Search Tool │  │File Search   │  │ Code    ││
        │  │ (Real-time)     │  │Tool (Vector) │  │Executor ││
        │  └─────────────────┘  └──────────────┘  └─────────┘│
        │                                                       │
        └───────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┬──────────────┐
        │           │           │              │
     ┌──▼──┐   ┌───▼──┐   ┌───▼────┐   ┌────▼──┐
     │ Web │   │Treat-│   │Scenario│   │Vector │
     │Data │   │ise   │   │Config  │   │Store  │
     │     │   │ PDF  │   │ JSON   │   │       │
     └─────┘   └──────┘   └────────┘   └───────┘
```

## Component Responsibilities

### BFIH Orchestrator
- **Input**: Scenario config + proposition
- **Process**: 
  1. Build orchestration prompt
  2. Call OpenAI Responses API with 3 tools
  3. Tools execute autonomously (web search → file search → code execution)
  4. LLM integrates results into BFIH report
- **Output**: Markdown report + posteriors + metadata

### API Server (FastAPI)
- **Input**: HTTP requests
- **Process**:
  1. Validate request
  2. Queue analysis to background task
  3. Store request metadata
  4. Return analysis_id immediately
- **Output**: JSON responses

### Storage Manager
- **Input**: Analysis results, scenario configs
- **Process**: Persist to file or database
- **Output**: Reliable retrieval

### Client SDK
- **Input**: Analysis parameters
- **Process**: 
  1. Submit via REST API
  2. Poll for status
  3. Fetch result when ready
- **Output**: Python dict with report

## Data Flow Example

```
User Request:
{
  "scenario_id": "s_001",
  "proposition": "Why did Startup X succeed?",
  "scenario_config": {
    "paradigms": [...],
    "hypotheses": [...],
    "priors_by_paradigm": {...}
  }
}
    ↓
FastAPI validates & queues to background task
    ↓
BFIHOrchestrator.conduct_analysis() called
    ↓
Build orchestration prompt with all requirements
    ↓
OpenAI Responses API called with tools:
  - web_search (find evidence)
  - file_search (retrieve forcing functions)
  - code_execution (compute posteriors)
    ↓
LLM orchestrates tools sequentially:
  1. Web search → evidence items
  2. File search → methodology  
  3. Code execution → posterior probabilities
    ↓
Integrate all into BFIH report (markdown)
    ↓
StorageManager.store_analysis_result()
    ↓
User polls GET /api/bfih-analysis/{id}
    ↓
Return full report + posteriors + metadata
```

## Deployment Topology

### Development (1 Server)

```
┌─────────────────────────────────┐
│      Laptop / Desktop           │
├─────────────────────────────────┤
│  • Python venv                  │
│  • FastAPI (localhost:8000)     │
│  • SQLite or File storage       │
│  • Redis (optional)             │
└─────────────────────────────────┘
```

### Staging (Docker Compose)

```
┌──────────────────────────────────────────────┐
│          Docker Host / VM                    │
├──────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────┐  ┌─────────┐ │
│  │ bfih-api     │  │ postgres │  │ redis   │ │
│  │ :8000        │  │ :5432    │  │ :6379   │ │
│  └──────────────┘  └──────────┘  └─────────┘ │
│  ┌──────────────────────────────────────────┐ │
│  │  docker-compose network                  │ │
│  └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

### Production (Cloud)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Cloud Provider (GCP/AWS/Azure)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    CDN (CloudFlare)                      │   │
│  │              (Static assets, caching)                    │   │
│  └────────────────────────┬─────────────────────────────────┘   │
│                           │                                      │
│  ┌────────────────────────▼──────────────────────────────────┐  │
│  │              Load Balancer (HTTPS)                        │  │
│  │          (Port 443 → 8000, auto-scaling)                 │  │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                      │
│  ┌────────────────────────▼──────────────────────────────────┐  │
│  │        Container Orchestration (Kubernetes/ECS)          │  │
│  │                                                          │  │
│  │  Pod 1: bfih-api      Pod 2: bfih-api      Pod N: ... │  │
│  │  ┌──────────────┐     ┌──────────────┐               │  │
│  │  │ FastAPI      │     │ FastAPI      │               │  │
│  │  │ :8000        │     │ :8000        │               │  │
│  │  └──────────────┘     └──────────────┘               │  │
│  │                  (Auto-scales on demand)              │  │
│  └────────────────────────┬───────────────────────────────┘  │
│                           │                                    │
│      ┌────────────────────┼────────────────────┐              │
│      │                    │                    │              │
│  ┌───▼────┐       ┌──────▼──┐         ┌───────▼──┐            │
│  │Cloud SQL│       │Memstore │         │Cloud    │            │
│  │Postgres │       │Redis    │         │Storage  │            │
│  │(managed)│       │(managed)│         │Backup   │            │
│  └────────┘       └─────────┘         └─────────┘            │
│                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Scaling Strategy

### Concurrent Analysis Handling

```
Request Rate: 10-100 req/sec

Level 1: Single Pod
  └─ Can handle: 1-10 req/sec
     Latency: Normal

Level 2: 3 Pods + Load Balancer
  └─ Can handle: 10-30 req/sec
     Latency: Good

Level 3: 10 Pods + Horizontal Scaling + Database Optimization
  └─ Can handle: 30-100 req/sec
     Latency: Good

Level 4: Global Load Balancing + Regional Replicas
  └─ Can handle: 100+ req/sec globally
     Latency: Excellent
```

### Database Scaling

```
SQLite/File Storage
  └─ Good for: <1000 analyses/day
  
PostgreSQL (Single)
  └─ Good for: <10,000 analyses/day
  
PostgreSQL + Read Replicas
  └─ Good for: <100,000 analyses/day
  
PostgreSQL + Sharding
  └─ Good for: >100,000 analyses/day
```

### Cache Strategy

```
No Cache
  └─ Analysis time: 40-60s per request

Redis Cache (5 min TTL)
  └─ Analysis time: 40-60s (first time)
                   <100ms (cached)
  └─ Hit rate: ~70% for typical usage

Multi-level Cache
  └─ Redis (hot data)
  └─ CDN (results)
  └─ Reduces OpenAI API calls by 80%
```

## Performance Benchmarks

### Single Request Performance
- Submit: <100ms
- Poll (first time): ~50 seconds
- Poll (cached): <100ms
- Total: 50-60 seconds

### Throughput
- 1 pod: 0.5-1 analysis/second
- 5 pods: 2.5-5 analyses/second
- 20 pods: 10-20 analyses/second

### Costs per Analysis
- OpenAI API: $0.60
- Database: $0.01
- Compute: $0.05
- **Total: $0.66**

## Monitoring & Observability

### Metrics to Track
- Request latency (p50, p95, p99)
- Analysis success rate
- OpenAI API calls per analysis
- Cache hit rate
- Error rate by type
- Database connection pool usage
- Memory usage per pod

### Alerting Rules
- Analysis timeout > 120s
- Error rate > 5%
- Database connection pool > 80%
- API latency > 30s (p95)
- OpenAI API quota exceeded

### Logs to Collect
- All API requests (endpoint, latency, status)
- BFIH analysis start/completion/errors
- Storage operations
- External API calls (OpenAI)
- System errors and exceptions

## Disaster Recovery

### Backup Strategy
- Database: Daily automated backups to cloud storage
- Results: Stored in object storage (GCS/S3)
- Code: Version control (Git)

### Recovery Time Objective (RTO): 1 hour
### Recovery Point Objective (RPO): 1 hour

### Failover Process
1. Detect outage (health check)
2. Trigger backup database restoration
3. Restart container instances
4. Verify functionality
5. Restore traffic

## Security Checklist

- [ ] HTTPS/TLS enabled
- [ ] API authentication (API key or OAuth)
- [ ] Rate limiting enabled
- [ ] CORS configured for specific domains
- [ ] Database encryption at rest
- [ ] Database encryption in transit
- [ ] Secrets management (no hardcoding)
- [ ] Regular dependency updates
- [ ] Security scanning (SAST/DAST)
- [ ] Access logs and audit trails
- [ ] DDoS protection
- [ ] WAF rules

---

**For detailed deployment instructions, see README.md and QUICKSTART.md**
