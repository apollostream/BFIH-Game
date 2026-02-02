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

# Run single test class or function
pytest test_bfih_backend.py::TestBFIHOrchestrator -v
pytest test_bfih_backend.py::test_function_name -v

# Run calibration tests
pytest test_calibrated_likelihoods.py -v

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
├── Phase 0c: Assign Priors (per paradigm) + Occam's complexity penalty
├── Build & save scenario_config JSON
│
└── conduct_analysis(request)
    ├── Phase 1: Retrieve Methodology (file_search → vector store)
    ├── Phase 2: Gather Evidence (web_search → structured JSON)
    ├── Phase 3: Assign Likelihoods (calibrated elicitation → clusters)
    ├── Phase 4: Bayesian Computation (code_interpreter)
    └── Phase 5: Generate Report (markdown, parallelized sections)
```

### Key Files

- **`bfih_orchestrator_fixed.py`** - Main orchestrator (~350KB). Contains `BFIHOrchestrator` class with all analysis phases, cost tracking, and report generation.
- **`bfih_api_server.py`** - FastAPI REST endpoints for `/api/bfih-analysis`, `/api/scenario`, `/api/health`
- **`bfih_storage.py`** - Storage abstraction (FileStorageBackend, GCSStorageBackend, PostgreSQL optional)
- **`bfih_schemas.py`** - Pydantic models for OpenAI structured outputs (Paradigm, Hypothesis, Evidence, etc.)
- **`bfih_client.py`** - Python SDK for API integration

### Hermeneutic Multi-Analysis System

For complex philosophical investigations spanning multiple analyses:

```
bfih_hermeneutic.py --project project.yaml
├── Phase 1: Component Analyses (via HermeneuticRunner)
├── Phase 2: Cross-Analysis Integration (tensions/reinforcements)
├── Phase 3: Meta-Analysis (treat conclusions as evidence)
└── Phase 4: Narrative Synthesis (unified philosophical work)
```

Related files:
- **`bfih_hermeneutic.py`** - CLI orchestrator for multi-analysis projects
- **`bfih_hermeneutic_runner.py`** - Runs component analyses in dependency order
- **`bfih_cross_analysis.py`** - Extracts UnifiedFindings, identifies tensions/reinforcements
- **`bfih_meta_analysis.py`** - Meta-level BFIH treating component conclusions as evidence
- **`bfih_narrative_synthesis.py`** - Generates SynthesisDocument from all analyses
- **`hermeneutic_config_schema.py`** - YAML schema for project configs

### Calibrated Likelihood Elicitation (Phase 3b)

The system uses calibrated elicitation to combat hedging bias (`_run_phase_3b_calibrated`):
1. **Causal clustering** groups evidence by root causal source (not source type)
2. For each cluster: identify H_max (highest likelihood hypothesis) and H_min (lowest)
3. Choose LR_range from calibrated scale (3, 6, 10, 18, 30)
4. Apply Occam's Razor complexity penalty for compound hypotheses
5. Parallel execution via ThreadPoolExecutor

**Causal Independence Principle:** Evidence clustering is based on the actual real-world generative process, not source type (media, academic, government). Derivative evidence (e.g., news article citing a study, think tank report using government data) is clustered with its root source and contributes only ONCE to the likelihood assessment. Key fields:
- `root_causal_source`: The actual measurement/study/dataset that generated the data
- `derivative_chain`: Citation relationships showing which items derive from others
- `effective_weight`: Usually 1.0; >1 only for genuinely independent replications

### Output Files

Each analysis produces:
- `analysis_result.json` - Full result with report, posteriors, metadata
- `scenario_config_{scenario_id}.json` - Generated config with paradigms, hypotheses, priors, evidence, calibration_info

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

Optional:
```
BFIH_REASONING_MODEL=gpt-5.2  # Default reasoning model (options: o3-mini, o3, o4-mini, gpt-5, gpt-5.2)
BFIH_LOG_FILE=bfih_analysis.log
```

Use `load_dotenv(override=True)` to ensure `.env` takes precedence over shell environment.

## Domain Concepts

- **Paradigm (K)**: Epistemic stance/worldview. K0 is privileged (empirical baseline), K1-Kn are biased stances
- **Hypothesis (H)**: Possible explanation. H0 is catch-all ("none of the above")
- **MECE**: Mutually Exclusive, Collectively Exhaustive hypothesis set
- **Forcing Functions**: Methodology checks (Ontological Scan, Ancestral Check, Paradigm Inversion)
- **Posteriors**: P(H|E,K) - probability of hypothesis given evidence under paradigm
- **LR (Likelihood Ratio)**: P(E|H)/P(E|¬H) - how much evidence supports hypothesis
- **WoE**: Weight of Evidence in decibans (10 * log10(LR))
- **Calibration anchors**: LR=3 (weak), LR=6 (moderate), LR=10 (strong), LR=18 (very strong), LR=30 (overwhelming)

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
# - evidence_items, evidence_clusters (with calibration_info)
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

# Generate magazine-style synopsis (uses GPT-5.2)
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
- `_run_phase_5_report(...)` - Regenerate full report from raw data

## Probability Bounds

The system enforces Cromwell's Rule - probabilities are clamped to [0.001, 0.999] to prevent mathematical errors (log(0), division by zero) and ensure Bayesian updating remains valid. See `clamp_probability()` and `PROB_EPSILON` in orchestrator.

## Cost Tracking

`CostTracker` class monitors API costs per phase. Pricing defined in `MODEL_PRICING` dict. Budget limits can halt analysis if exceeded.
