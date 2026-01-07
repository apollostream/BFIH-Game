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
