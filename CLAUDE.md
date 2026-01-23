# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BFIH (Bayesian Framework for Intellectual Honesty) Backend - An AI-assisted hypothesis analysis system that uses OpenAI's Responses API to conduct rigorous Bayesian analysis on propositions. The system generates paradigms, hypotheses, gathers evidence via web search, computes posteriors, and produces structured analysis reports.

## Key Commands

```bash
# Activate virtual environment (required for all Python commands)
source venv/bin/activate

# Run the orchestrator directly (autonomous analysis)
python3 bfih_orchestrator_fixed.py

# Start API server
uvicorn bfih_api_server:app --reload

# Run tests
pytest test_bfih_backend.py -v

# Initialize vector store (one-time setup)
python setup_vector_store.py
```

## Architecture

### Core Analysis Flow

The main entry point is `BFIHOrchestrator.analyze_topic()` in `bfih_orchestrator_fixed.py`:

```
analyze_topic(proposition)
├── Phase 0a: Generate Paradigms (2-4 epistemic stances)
├── Phase 0b: Generate Hypotheses + Forcing Functions
│   ├── Ontological Scan (verify 7 domains)
│   ├── Ancestral Check (historical solutions)
│   ├── Paradigm Inversion (inverse hypotheses)
│   └── MECE Synthesis (unified hypothesis set)
├── Phase 0c: Assign Priors (per paradigm)
├── Build & save scenario_config JSON
│
└── conduct_analysis(request)
    ├── Phase 1: Retrieve Methodology (file_search → vector store)
    ├── Phase 2: Gather Evidence (web_search → structured JSON)
    ├── Phase 3: Assign Likelihoods (reasoning → clusters)
    ├── Phase 4: Bayesian Computation (code_interpreter)
    └── Phase 5: Generate Report (markdown)
```

### Key Files

- **`bfih_orchestrator_fixed.py`** - Main orchestrator with `BFIHOrchestrator` class. This is the primary file for analysis logic.
- **`bfih_api_server.py`** - FastAPI REST endpoints
- **`bfih_storage.py`** - Storage abstraction (file/PostgreSQL/Redis)
- **`bfih_client.py`** - Python SDK for API integration

### Output Files

Each analysis produces:
- `analysis_result.json` - Full result with report, posteriors, metadata
- `scenario_config_{scenario_id}.json` - Generated config with paradigms, hypotheses, priors, evidence

### Structured Data Extraction

The orchestrator uses marker-based JSON extraction for reliable parsing:
- `EVIDENCE_JSON_START` / `EVIDENCE_JSON_END` - Evidence items with APA citations and URLs
- `CLUSTERS_JSON_START` / `CLUSTERS_JSON_END` - Evidence clusters with likelihoods
- `BFIH_JSON_OUTPUT_START` / `BFIH_JSON_OUTPUT_END` - Bayesian computation results

## Configuration

Required environment variables in `.env`:
```
OPENAI_API_KEY=sk-proj-...
TREATISE_VECTOR_STORE_ID=vs_...
```

Use `load_dotenv(override=True)` to ensure `.env` takes precedence over shell environment.

## Domain Concepts

- **Paradigm (K)**: Epistemic stance/worldview (e.g., K1=Technocratic, K2=Cultural)
- **Hypothesis (H)**: Possible explanation (H0 is catch-all)
- **MECE**: Mutually Exclusive, Collectively Exhaustive hypothesis set
- **Forcing Functions**: Methodology checks (Ontological Scan, Ancestral Check, Paradigm Inversion)
- **Posteriors**: P(H|E,K) - probability of hypothesis given evidence under paradigm
- **WoE**: Weight of Evidence in decibans (10 * log10(LR))

## GCS Storage & Local Report Generation

Completed analyses are stored in Google Cloud Storage and can be accessed for local processing.

### GCS Bucket Structure

```
gs://bfih-scenarios/bfih/
├── analyses/{scenario_id}.json     # Full analysis results with report
├── scenarios/{scenario_id}.json    # Scenario configs (paradigms, hypotheses, priors)
└── status/{analysis_id}.txt        # Analysis status files
```

Public URL pattern: `https://storage.googleapis.com/bfih-scenarios/bfih/analyses/{scenario_id}.json`

### Fetching Analysis Data from GCS

```python
import requests

def fetch_gcs_analysis(scenario_id: str) -> dict:
    url = f"https://storage.googleapis.com/bfih-scenarios/bfih/analyses/{scenario_id}.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# The returned dict contains:
# - analysis_id, scenario_id, proposition
# - report (full markdown BFIH report)
# - evidence_items, evidence_clusters
# - paradigms, hypotheses, priors, posteriors
```

### Generating Reports/Synopses Locally

When an analysis completes but you need to regenerate reports or generate synopses:

```python
from dotenv import load_dotenv
load_dotenv(override=True)

from bfih_orchestrator_fixed import BFIHOrchestrator

# Fetch completed analysis from GCS
analysis_data = fetch_gcs_analysis("auto_9f9320e9")
report = analysis_data['report']

# Initialize orchestrator (requires OPENAI_API_KEY)
orchestrator = BFIHOrchestrator()

# Generate magazine-style synopsis (uses GPT-5.2, takes ~2 minutes)
synopsis = orchestrator.generate_magazine_synopsis(
    report=report,
    scenario_id="auto_9f9320e9",
    style="gawande"  # or "atlantic" for corrective K0-primacy style
)
# Saves to: {scenario_id}_magazine_synopsis.md
```

### Key Orchestrator Functions for Post-Processing

- `generate_magazine_synopsis(report, scenario_id, style)` - Convert BFIH report to magazine article
- `cleanup_bibliography(report)` - Deduplicate and renumber citations
- `generate_evidence_flow_dot(result)` - Create Graphviz visualization
- `_run_phase_5_report(...)` - Regenerate full report from raw data (requires evidence_items, clusters, posteriors)
