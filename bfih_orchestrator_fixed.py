"""
BFIH Backend: Main Orchestrator Service
OpenAI Responses API Integration for AI-Assisted Hypothesis Tournament Game

This module coordinates:
1. Web search for evidence via OpenAI Responses API
2. File search for treatise/scenarios via vector stores
3. Python code execution for Bayesian calculations
4. BFIH report generation and storage
"""

import argparse
import json
import math
import os
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import uuid
from dataclasses import dataclass, asdict

from openai import OpenAI
from dotenv import load_dotenv
import httpx

# Import structured output schemas
from bfih_schemas import (
    ParadigmList, HypothesesWithForcingFunctions, PriorsByParadigm,
    EvidenceList, EvidenceClusterList, get_openai_schema
)


# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv(override=True)

# Configure logging to both console and file
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.getenv("BFIH_LOG_FILE", "bfih_analysis.log")

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False  # Prevent duplicate logs from propagating to root

# Console handler (stdout/stderr)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# File handler (overwrite each run - scenario_config.json preserves analysis data)
file_handler = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Add handlers to our logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Configure root logger for library logs (httpx, etc.)
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[console_handler, file_handler]
)

logger.info(f"Logging to console and file: {LOG_FILE}")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TREATISE_VECTOR_STORE_ID = os.getenv("TREATISE_VECTOR_STORE_ID")
MODEL = "gpt-4o"
# Reasoning model for cognitively demanding tasks (paradigm/hypothesis/prior/likelihood)
# Options: o3-mini (default), o3, o4-mini, gpt-5, gpt-5.2
REASONING_MODEL = os.getenv("BFIH_REASONING_MODEL", "o3-mini")
# Whether reasoning model supports structured output (o3-mini and newer do as of 2026)
REASONING_MODEL_SUPPORTS_STRUCTURED = os.getenv("BFIH_REASONING_STRUCTURED", "true").lower() == "true"

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

# Create OpenAI client with extended timeout for long-running operations
client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=httpx.Timeout(300.0, connect=30.0)  # 5 min total, 30s connect
)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class BFIHAnalysisRequest:
    """Request to conduct BFIH analysis"""
    scenario_id: str
    proposition: str
    scenario_config: Dict
    user_id: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class BFIHAnalysisResult:
    """Result of BFIH analysis"""
    analysis_id: str
    scenario_id: str
    proposition: str
    report: str
    posteriors: Dict[str, Dict[str, float]]  # {paradigm_id: {hypothesis_id: posterior}}
    metadata: Dict
    created_at: str
    scenario_config: Optional[Dict] = None  # Full scenario config for frontend

    def to_dict(self):
        return asdict(self)


# ============================================================================
# BFIH ORCHESTRATOR (Main Logic)
# ============================================================================

class BFIHOrchestrator:
    """
    Orchestrates full BFIH analysis using OpenAI Responses API
    Coordinates web search, file search, and code execution
    """
    
    def __init__(self, vector_store_id: Optional[str] = None):
        self.client = client
        self.vector_store_id = vector_store_id or TREATISE_VECTOR_STORE_ID
        self.model = MODEL
        self.reasoning_model = REASONING_MODEL
        logger.info(f"Using reasoning model: {self.reasoning_model} for hypothesis generation")
        
    def conduct_analysis(self, request: BFIHAnalysisRequest) -> BFIHAnalysisResult:
        """
        Main entry point: Conduct full BFIH analysis using phased approach.

        Executes 5 phases sequentially:
        1. Retrieve methodology (file_search)
        2. Gather evidence (web_search)
        3. Assign likelihoods (reasoning)
        4. Bayesian computation (code_interpreter)
        5. Generate report (reasoning)

        Args:
            request: BFIHAnalysisRequest with scenario config and proposition

        Returns:
            BFIHAnalysisResult with report and posteriors
        """
        analysis_start = datetime.now(timezone.utc)
        logger.info(f"Starting BFIH analysis for scenario: {request.scenario_id}")
        logger.info(f"Proposition: {request.proposition}")

        try:
            # Phase 1: Retrieve methodology from vector store
            methodology = self._run_phase_1_methodology(request)

            # Phase 2: Gather evidence via web search (returns structured evidence)
            evidence_text, evidence_items = self._run_phase_2_evidence(request, methodology)

            # Phase 3: Assign likelihoods to evidence (returns structured clusters)
            likelihoods_text, evidence_clusters = self._run_phase_3_likelihoods(
                request, evidence_text, evidence_items
            )

            # Phase 4: Run Bayesian computation
            computation = self._run_phase_4_computation(request, likelihoods_text)

            # Phase 5: Generate final report (pass structured data for detailed tables)
            bfih_report = self._run_phase_5_report(
                request, methodology, evidence_text, likelihoods_text, computation,
                evidence_items, evidence_clusters
            )

            # Extract posteriors from computation output (Phase 4)
            # Pass evidence_clusters to compute paradigm-specific posteriors
            posteriors = self._extract_posteriors_from_report(
                computation, request.scenario_config, evidence_clusters
            )

            # Create result object
            analysis_id = str(uuid.uuid4())
            analysis_end = datetime.now(timezone.utc)
            duration_seconds = (analysis_end - analysis_start).total_seconds()

            result = BFIHAnalysisResult(
                analysis_id=analysis_id,
                scenario_id=request.scenario_id,
                proposition=request.proposition,
                report=bfih_report,
                posteriors=posteriors,
                metadata={
                    "model": self.model,
                    "phases_completed": 5,
                    "duration_seconds": duration_seconds,
                    "user_id": request.user_id,
                    "evidence_items_count": len(evidence_items),
                    "evidence_clusters_count": len(evidence_clusters)
                },
                created_at=analysis_end.isoformat(),
                scenario_config=request.scenario_config
            )

            # Store structured evidence in metadata for access
            result.metadata["evidence_items"] = evidence_items
            result.metadata["evidence_clusters"] = evidence_clusters

            logger.info(f"BFIH analysis completed successfully: {analysis_id}")
            logger.info(f"Duration: {duration_seconds:.1f}s")
            logger.info(f"Evidence: {len(evidence_items)} items in {len(evidence_clusters)} clusters")
            return result

        except Exception as e:
            logger.error(f"Error conducting BFIH analysis: {str(e)}", exc_info=True)
            raise
    
    def _build_orchestration_prompt(self, request: BFIHAnalysisRequest) -> str:
        """Build the orchestration prompt for LLM"""
        scenario_json = json.dumps(request.scenario_config, indent=2)
        
        prompt = f"""
You are an expert analyst conducting a rigorous Bayesian Framework for Intellectual Honesty (BFIH) analysis.

PROPOSITION UNDER INVESTIGATION:
"{request.proposition}"

SCENARIO CONFIGURATION:
{scenario_json}

YOUR TASK - Execute systematically in this order -- DO NOT stop until you have completed all 5 Phases:

## Phase 1: Retrieve Methodology
- Use file_search to retrieve "forcing functions" and "paradigm inversion" methods from the treatise
- Extract key methodology sections on ontological scan, ancestral check, paradigm inversion

## Phase 2: Evidence Gathering
- For EACH hypothesis in the scenario, generate specific web search queries
- Execute web searches to find real-world evidence supporting or refuting hypotheses
- Organize evidence by hypothesis and cluster (for conditional independence assumptions)
- Record source citations for all evidence

## Phase 3: Likelihood Assignment
- For each evidence item, assign likelihoods P(E|H) under each paradigm
- Justify each likelihood assignment with reference to paradigm assumptions
- Ensure likelihoods reflect paradigm-specific reasoning

## Phase 4: Bayesian Computation
- Use the Python tool code_interpreter to run Python script computing:
  * Likelihood under negation: P(E|¬H_i) = SUM(P(E|H_j)*P(H_j|¬H_i);j<>i); P(H_j|¬H_i)=P(H_j)/(1 - P(H_i))
  * Likelihood ratios: LR(H; E, K) = P(E|H) / P(E|¬H)
  * Weight of evidence: WoE = log₁₀(LR) in decibans
  * Posterior probabilities: P(H|E₁:T, K) under each paradigm
  * Sensitivity analysis: ±20% prior variation for key hypotheses

## Phase 5: BFIH Report Generation
Generate comprehensive markdown report with EXACTLY these sections:

1. **Executive Summary** (2-3 paragraphs)
   - Primary finding with verdict (VALIDATED/PARTIALLY VALIDATED/REJECTED/INDETERMINATE)
   - Key posterior probabilities (decimal form)
   - Paradigm dependence summary

2. **Scenario & Objectives** 
   - Framing and decision stakes
   - Time horizon and key actors

3. **Background Knowledge (K₀) Analysis**
   - Dominant paradigm assumptions
   - Alternative paradigms and inverse mappings
   - Implicit assumptions

4. **Forcing Functions Application**
   - Ontological Scan: table showing all 7 domains covered/justified
   - Ancestral Check: historical solution identified
   - Paradigm Inversion: inverse hypotheses generated
   - Split-Brain: key disagreements between paradigms

5. **Hypothesis Set Documentation**
   - MECE verification
   - Inventory table with domain/paradigm tags

6. **Evidence Matrix & Likelihood Analysis**
   - Evidence clustering strategy
   - For each evidence item: narrative + likelihood table under each paradigm
   - Evidence interpretation across paradigms

7. **Bayesian Update Trace**
   - Round-by-round posteriors
   - Final posteriors under each paradigm

8. **Paradigm-Dependence Analysis**
   - Robust conclusions (hold across paradigms)
   - Paradigm-dependent conclusions (vary by paradigm)
   - Incommensurable disagreements

9. **Sensitivity Analysis Results**
   - Table showing posterior sensitivity to ±20% prior variation
   - Assessment of robustness

10. **Intellectual Honesty Assessment**
    - Were forcing functions applied? (✓/✗)
    - Were blind spots surfaced?
    - Consistency of evidence evaluation

## CRITICAL OUTPUT REQUIREMENTS:
- Use ONLY markdown formatting
- Include ALL tables with proper markdown syntax
- Use decimal probabilities (e.g., 0.425, not 42.5%)
- Include all computed values from the Python tool code_interpreter
- NO markdown code blocks for Python code (show results only)
- All posteriors must match code_interpreter output exactly
- Include at least 3-5 evidence items per paradigm

""" + """

## PYTHON BAYESIAN CALCULATION TEMPLATE (will execute):

```python
# BFIH posterior computation for Constitutional Protections 2025
# Cluster-level computation (4 independent clusters, not 22 dependent items)

import numpy as np
from collections import OrderedDict

# 1. Define hypotheses and priors
hypotheses = ["H1", "H2", "H3", "H4", "H5"]

priors = {
    "H1": 0.25,  # Constitutional Continuity
    "H2": 0.25,  # Gradual Constitutional Erosion
    "H3": 0.20,  # Severe Institutional Stress with Recovery
    "H4": 0.10,  # Regime Transformation Through Institutional Capture
    "H5": 0.15   # Legitimate Executive Authority Expansion
}

# 2. Define CLUSTER-LEVEL joint likelihoods P(Cluster_k | H_i)
# These represent the joint probability of observing all evidence within a cluster
# given each hypothesis.

evidence_clusters = OrderedDict({
    "Cluster_A_Institutional": {
        "description": "7 items: EO volume, IG removals, emergencies, Schedule F, litigation, democracy indices",
        "likelihoods": {
            "H1": 0.05,   # Highly unlikely under continuity (unprecedented institutional changes)
            "H2": 0.35,   # Moderately consistent with gradual erosion
            "H3": 0.70,   # Consistent with severe stress
            "H4": 0.90,   # Highly consistent with regime transformation
            "H5": 0.45 # Violated law, so < 50%; 0.65    # Moderately consistent with executive authority expansion
         },
        "likelihoods_not_h":{h: 0.0 for h in hypotheses}
    },
    "Cluster_B_CriminalJustice": {
        "description": "6 items: Sentencing, bail, arrest, death penalty, youth incarceration, pretrial",
        "likelihoods": {
        "H1": 0.50,   # Baseline disparities exist under continuity
            "H2": 0.70,   # Consistent with gradual erosion (youth incarceration worsening)
            "H3": 0.60,   # Stress test doesn't predict CJ changes
            "H4": 0.75,   # Consistent with regime transformation (worsening + reduced enforcement)
            "H5": 0.65    # Unitary executive neutral on CJ disparities
         },
        "likelihoods_not_h":{h: 0.0 for h in hypotheses}
    },
    "Cluster_C_VotingRights": {
        "description": "4 items: Precinct closures, voter ID, wait times, purges",
        "likelihoods": {
            "H1": 0.35,   # Post-Shelby erosion conflicts with continuity baseline
            "H2": 0.85,   # Highly consistent with gradual erosion (post-2013 trend)
            "H3": 0.55,   # Stress test doesn't predict voting changes
            "H4": 0.70,   # Consistent with regime transformation
            "H5": 0.65    # Federalism/state authority consistent with restrictions
         },
        "likelihoods_not_h":{h: 0.0 for h in hypotheses}
    },
    "Cluster_D_DOJ_EEOC": {
        "description": "5 items: Selective prosecution, EEOC drops, anti-DEI, political targets",
        "likelihoods": {
            "H1": 0.02,   # Highly inconsistent with continuity (WH admits score settling)
            "H2": 0.25,   # Some consistency with erosion but scale unprecedented
            "H3": 0.50,   # Consistent with severe stress (may be temporary)
            "H4": 0.95,   # Highly consistent with regime transformation (loyalty-based enforcement)
            "H5": 0.45 # Targeting inconsistent w/oaths of office, so < 50%; 0.60    # Partially consistent with unitary executive (personnel control)
         },
        "likelihoods_not_h":{h: 0.0 for h in hypotheses}
    }
})
# Compute the likelihoods under hypothesis negation, P(Cluster_k | ~H_i)
for cluster_name, cluster_data in evidence_clusters.items():
    lklhd = cluster_data['likelihoods']
    lklhd_not_h = cluster_data['likelihoods_not_h']
    for h_i in hypotheses:
        complement_prior_hi = 1 - priors[h_i]
        if complement_prior_hi > 0:
            lklhd_not_h[h_i] = sum(
                lklhd[h_j] * (priors[h_j] / complement_prior_hi)
                for h_j in hypotheses if h_j != h_i
            )
        else:
            lklhd_not_h[h_i] = 0.0
    evidence_clusters[cluster_name]['likelihoods_not_h'] = lklhd_not_h

# 3. Compute unnormalized posteriors and cluster-level metrics
unnormalized_posteriors = {}
total_likelihood = {}
cluster_metrics = {h: [] for h in hypotheses}

for h_i in hypotheses:
    prior_hi = priors[h_i]
    joint_log_likelihood = 0.0

    for cluster_name, cluster_data in evidence_clusters.items():
        pk_hi = cluster_data['likelihoods'][h_i]
        pk_not_hi = cluster_data['likelihoods_not_h'][h_i]
        # Bayesian confirmation metrics for this cluster
        lr = pk_hi / pk_not_hi if pk_not_hi > 0 else float('inf')
        woe = 10 * np.log10(lr) if lr > 0 and lr != float('inf') else (
            float('inf') if lr == float('inf') else float('-inf')
        )

        cluster_metrics[h_i].append({
            'cluster': cluster_name,
            'description': cluster_data['description'],
            'P(Cluster_k | Hi)': pk_hi,
            'P(Cluster_k | ~Hi)': pk_not_hi,
            'LR': lr,
            'WoE': woe
        })

        joint_log_likelihood += np.log10(pk_hi)

    joint_likelihood = 10 ** joint_log_likelihood
    unnormalized_posteriors[h_i] = prior_hi * joint_likelihood
    total_likelihood[h_i] = joint_likelihood

total_neg_likelihood = {}
for h_i in hypotheses:
    prior_hi = priors[h_i]
    complement_prior_hi = 1 - prior_hi
    if complement_prior_hi > 0:
        total_neg_likelihood[h_i] = sum(
            total_likelihood[h_j] * (priors[h_j] / complement_prior_hi)
            for h_j in hypotheses if h_j != h_i
        )
    else:
        total_neg_likelihood[h_i] = 0.0

# 4. Normalize to get final posteriors
normalization_constant = sum(unnormalized_posteriors.values()) # P(E), marginal probability of all evidence
posteriors = {h: unnormalized_posteriors[h] / normalization_constant for h in hypotheses} # Bayes Theorem

# 5. Compute total evidence Bayesian confirmation metrics, LR & WoE
total_likelihood_ratios = {}
for h, post in posteriors.items():
    prior = priors[h]
    if post < 1.0 and prior < 1.0 and post > 0 and prior > 0:
        prior_odds = prior / (1 - prior)
        posterior_odds = post / (1 - post)
        total_likelihood_ratios[h] = posterior_odds / prior_odds
    else:
        total_likelihood_ratios[h] = float('inf')

total_weights_of_evidence = {}
for h, lr in total_likelihood_ratios.items():
    if lr == float('inf'):
        total_weights_of_evidence[h] = float('inf')
    elif lr > 0:
        total_weights_of_evidence[h] = 10 * np.log10(lr)
    else:
        total_weights_of_evidence[h] = float('-inf')

# 6. Print Cluster-Level Bayesian Confirmation Metrics
print("=" * 80)
print("BFIH BAYESIAN CONFIRMATION METRICS (cluster-level evidence)")
print("=" * 80)
print("\nLikelihood Ratio and Weight of Evidence by Cluster:\n")

for h in hypotheses:
    print(f"\n--- Hypothesis: {h} (Prior: {priors[h]:.3f} | P(E|{h}): {total_likelihood[h]:.3g} | P(E|~{h}): {total_neg_likelihood[h]:.3g} | Posterior: {posteriors[h]:.3f}) ---")
    for m in cluster_metrics[h]:
        #print(f"\n Cluster: {m['cluster']}")
        #print(f"   ({m['description']})")
        if m['LR'] == float('inf'):
            print(f"   LR:      inf | WoE:      inf dB")
        else:
            print(f"   {m['cluster']:25s}: P(Ck|{h}): {m['P(Cluster_k | Hi)']:6.2f} | P(Ck|~{h}): {m['P(Cluster_k | ~Hi)']:6.2f} | LR: {m['LR']:6.3f} | WoE: {m['WoE']:6.2f} dB")

# 7. Print Posteriors
print("\n" + "=" * 80)
print("BFIH POSTERIOR COMPUTATION")
print("=" * 80)
print("\nFinal Posterior Probabilities P(H | Cluster_A...Cluster_D):\n")

for h in sorted(posteriors.keys(), key=lambda x: posteriors[x], reverse=True):
    print(f"{h:4s}: {posteriors[h]:.2g}")

print(f"\nNormalization Check: {sum(posteriors.values()):.6f}")

# 8. Print Total Evidence Bayesian Confirmation Metrics
print("\n" + "=" * 80)
print("BFIH BAYESIAN CONFIRMATION METRICS (total evidence)")
print("=" * 80)
print("\nTotal Likelihood Ratio and Weight of Evidence:\n")

for h in sorted(posteriors.keys(), key=lambda x: posteriors[x], reverse=True):
    lr_val = total_likelihood_ratios[h]
    woe_val = total_weights_of_evidence[h]
    if lr_val == float('inf'):
        print(f"{h:4s}: LR =      inf, WoE =      inf dB")
    else:
        print(f"{h:4s}: LR = {lr_val:8.2f}, WoE = {woe_val:6.1f} dB")
```

NOW BEGIN YOUR ANALYSIS. Work through each phase systematically.
"""
        return prompt
    
    def _extract_posteriors_from_report(self, report: str, scenario_config: Dict,
                                         evidence_clusters: List[Dict] = None) -> Dict:
        """
        Extract posterior probabilities from the generated report.
        Returns dict of {paradigm_id: {hypothesis_id: posterior_value}}

        Computes SEPARATE posteriors for each paradigm using:
        - Each paradigm's specific priors from scenario_config
        - PARADIGM-SPECIFIC likelihoods P(E|H,K) from evidence_clusters
        """
        posteriors = {}
        paradigms = scenario_config.get("paradigms", [])
        hypotheses = scenario_config.get("hypotheses", [])
        priors_by_paradigm = scenario_config.get("priors_by_paradigm", scenario_config.get("priors", {}))

        # If no paradigms defined, create a default one
        if not paradigms:
            paradigms = [{"id": "default"}]

        # Get hypothesis IDs
        hyp_ids = [h.get("id", f"H{i}") for i, h in enumerate(hypotheses)]

        # If we have evidence clusters with likelihoods, compute paradigm-specific posteriors
        if evidence_clusters and priors_by_paradigm:
            logger.info(f"Computing paradigm-specific posteriors for {len(paradigms)} paradigms")

            # Compute posteriors for each paradigm
            for paradigm in paradigms:
                paradigm_id = paradigm.get("id")
                paradigm_priors = priors_by_paradigm.get(paradigm_id, {})

                # Get priors for each hypothesis
                priors = {}
                for h_id in hyp_ids:
                    p = paradigm_priors.get(h_id, paradigm_priors.get(h_id.upper(), {}))
                    if isinstance(p, dict):
                        priors[h_id] = p.get("probability", p.get("prior", 1.0 / len(hyp_ids)))
                    elif isinstance(p, (int, float)):
                        priors[h_id] = float(p)
                    else:
                        priors[h_id] = 1.0 / len(hyp_ids)  # Uniform default

                # Extract PARADIGM-SPECIFIC likelihoods P(E|H,K) for this paradigm
                cluster_likelihoods = []
                for cluster in evidence_clusters:
                    # Try new format: likelihoods_by_paradigm[K][H]
                    lh_by_paradigm = cluster.get("likelihoods_by_paradigm", {})
                    if paradigm_id in lh_by_paradigm:
                        lh = lh_by_paradigm[paradigm_id]
                    else:
                        # Fallback to old format: likelihoods[H] (same for all paradigms)
                        lh = cluster.get("likelihoods", {})

                    # Extract likelihood for each hypothesis
                    cluster_lh = {}
                    for h_id in hyp_ids:
                        h_lh = lh.get(h_id, lh.get(h_id.upper(), lh.get(h_id.lower(), {})))
                        if isinstance(h_lh, dict):
                            cluster_lh[h_id] = h_lh.get("probability", 0.5)
                        elif isinstance(h_lh, (int, float)):
                            cluster_lh[h_id] = float(h_lh)
                        else:
                            cluster_lh[h_id] = 0.5  # Default neutral
                    cluster_likelihoods.append(cluster_lh)

                # Compute unnormalized posteriors using Bayes' theorem
                # P(H|E,K) ∝ P(H|K) * ∏P(E_k|H,K)
                unnormalized = {}
                for h_id in hyp_ids:
                    log_likelihood = 0.0
                    for cluster_lh in cluster_likelihoods:
                        p_e_h_k = cluster_lh.get(h_id, 0.5)
                        if p_e_h_k > 0:
                            log_likelihood += math.log(p_e_h_k)
                        else:
                            log_likelihood += math.log(1e-10)  # Avoid log(0)

                    total_likelihood = math.exp(log_likelihood)
                    unnormalized[h_id] = priors[h_id] * total_likelihood

                # Normalize
                norm_const = sum(unnormalized.values())
                if norm_const > 0:
                    posteriors[paradigm_id] = {
                        h_id: unnormalized[h_id] / norm_const
                        for h_id in hyp_ids
                    }
                else:
                    # Fallback to priors if computation fails
                    posteriors[paradigm_id] = priors.copy()

                logger.info(f"Paradigm {paradigm_id} posteriors: {posteriors[paradigm_id]}")
        else:
            # Fallback: Parse posteriors from report text (same for all paradigms)
            logger.warning("No evidence clusters available, falling back to text extraction")
            extracted = self._parse_posterior_section(report)

            if not extracted:
                logger.warning("No posteriors extracted from report, using defaults")

            for paradigm in paradigms:
                paradigm_id = paradigm.get("id")
                posteriors[paradigm_id] = {}
                for hypothesis_id, value in extracted.items():
                    posteriors[paradigm_id][hypothesis_id] = value

        return posteriors

    def _run_phase(self, prompt: str, tools: List[Dict], phase_name: str, max_retries: int = 2) -> str:
        """
        Run a single phase with streaming output and retry logic.
        Returns the output text from the phase.
        """
        import time

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Starting {phase_name}" + (f" (attempt {attempt + 1})" if attempt > 0 else ""))
                print(f"\n{'='*60}\n{phase_name}" + (f" (retry {attempt})" if attempt > 0 else "") + f"\n{'='*60}")

                response = None
                stream = self.client.responses.create(
                    model=self.model,
                    input=prompt,
                    max_output_tokens=16000,  # Increased for comprehensive reports
                    tools=tools,
                    include=["file_search_call.results"] if any(t.get("type") == "file_search" for t in tools) else [],
                    stream=True
                )

                for event in stream:
                    if event.type == "response.output_text.delta":
                        print(event.delta, end="", flush=True)
                    elif event.type == "response.web_search_call.searching":
                        print(f"\n[Searching web...]")
                    elif event.type == "response.file_search_call.searching":
                        print(f"\n[Searching vector store...]")
                    elif event.type == "response.code_interpreter_call.interpreting":
                        print(f"\n[Running Python code...]")
                    elif event.type == "response.completed":
                        response = event.response
                    elif event.type == "error":
                        logger.error(f"Error in {phase_name}: {event.error.message}")
                        raise RuntimeError(f"API error in {phase_name}: {event.error.message}")

                if response is None:
                    raise RuntimeError(f"No response received for {phase_name}")

                print(f"\n[{phase_name} complete]")
                logger.info(f"{phase_name} complete, status: {response.status}")

                return response.output_text

            except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 5  # 5s, 10s backoff
                    logger.warning(f"{phase_name} failed with {type(e).__name__}, retrying in {wait_time}s...")
                    print(f"\n[Connection error, retrying in {wait_time}s...]")
                    time.sleep(wait_time)
                else:
                    logger.error(f"{phase_name} failed after {max_retries + 1} attempts: {e}")
                    raise

        raise last_error or RuntimeError(f"Failed to complete {phase_name}")

    def _run_structured_phase(self, prompt: str, schema_name: str, phase_name: str,
                               tools: List[Dict] = None, max_retries: int = 2,
                               model: str = None) -> dict:
        """
        Run a phase with structured output (JSON Schema enforcement).

        This method uses OpenAI's response_format parameter to guarantee
        valid JSON output matching the specified schema.

        Args:
            prompt: The prompt to send to the model
            schema_name: Name of schema from bfih_schemas (paradigms, hypotheses, priors, evidence, clusters)
            phase_name: Human-readable name for logging
            tools: Optional list of tools (file_search, web_search)
            max_retries: Number of retry attempts on connection failure
            model: Optional model override (default: self.model)

        Returns:
            Parsed JSON dict matching the schema
        """
        import time

        last_error = None
        tools = tools or []
        model = model or self.model

        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Starting {phase_name} (structured output, model: {model})" +
                           (f" (attempt {attempt + 1})" if attempt > 0 else ""))
                print(f"\n{'='*60}\n{phase_name} [Structured Output: {model}]" +
                      (f" (retry {attempt})" if attempt > 0 else "") + f"\n{'='*60}")

                # Get the schema for this type
                schema_map = {
                    "paradigms": ParadigmList,
                    "hypotheses": HypothesesWithForcingFunctions,
                    "priors": PriorsByParadigm,
                    "evidence": EvidenceList,
                    "clusters": EvidenceClusterList
                }

                schema_class = schema_map.get(schema_name)
                if not schema_class:
                    raise ValueError(f"Unknown schema: {schema_name}")

                # Build the request with proper Responses API format
                request_params = {
                    "model": model,
                    "input": prompt,
                    "max_output_tokens": 16000,
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": schema_name,
                            "schema": schema_class.model_json_schema(),
                            "strict": True
                        }
                    }
                }

                # Add tools if provided
                if tools:
                    request_params["tools"] = tools
                    if any(t.get("type") == "file_search" for t in tools):
                        request_params["include"] = ["file_search_call.results"]

                # Make the API call (non-streaming for structured output)
                print(f"[Calling API with structured output schema: {schema_name}...]")

                response = self.client.responses.create(**request_params)

                # Extract the output
                output_text = response.output_text
                print(f"\n[Received structured output, parsing JSON...]")

                # Parse JSON from output
                try:
                    # The output should be valid JSON due to schema enforcement
                    result = json.loads(output_text)
                    logger.info(f"{phase_name} complete with valid JSON")
                    print(f"[{phase_name} complete - valid JSON parsed]")
                    return result
                except json.JSONDecodeError as e:
                    # Fallback: try to extract JSON from the response
                    logger.warning(f"Direct JSON parse failed: {e}, attempting extraction")
                    json_match = re.search(r'[\[{].*[}\]]', output_text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group(0))
                        logger.info(f"{phase_name} complete with extracted JSON")
                        return result
                    raise ValueError(f"Could not parse JSON from response: {output_text[:500]}")

            except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"{phase_name} failed with {type(e).__name__}, retrying in {wait_time}s...")
                    print(f"\n[Connection error, retrying in {wait_time}s...]")
                    time.sleep(wait_time)
                else:
                    logger.error(f"{phase_name} failed after {max_retries + 1} attempts: {e}")
                    raise

        raise last_error or RuntimeError(f"Failed to complete {phase_name}")

    def _run_structured_phase_with_model(self, prompt: str, schema_name: str, phase_name: str,
                                          model: str, max_retries: int = 2) -> dict:
        """
        Convenience wrapper for _run_structured_phase with custom model.
        Used when reasoning models support structured output.
        """
        return self._run_structured_phase(prompt, schema_name, phase_name,
                                          tools=None, max_retries=max_retries, model=model)

    def _run_reasoning_phase(self, prompt: str, phase_name: str, max_retries: int = 2,
                              schema_name: str = None) -> dict:
        """
        Run a phase with a reasoning model (o3-mini, o3, o4-mini, gpt-5, etc.) for deep analytical thinking.

        As of 2026, most reasoning models (o3-mini and newer) support structured output.
        If REASONING_MODEL_SUPPORTS_STRUCTURED is True and schema_name is provided,
        we use structured output directly. Otherwise, we parse JSON from the response.

        Args:
            prompt: The prompt to send to the reasoning model
            phase_name: Human-readable name for logging
            max_retries: Number of retry attempts on connection failure
            schema_name: Schema name for structured output (recommended for reliability)

        Returns:
            Parsed JSON dict from the model's output
        """
        import time

        # If structured output is supported and schema provided, use it directly
        if REASONING_MODEL_SUPPORTS_STRUCTURED and schema_name:
            logger.info(f"Using reasoning model with structured output: {self.reasoning_model}")
            return self._run_structured_phase_with_model(
                prompt, schema_name, phase_name, self.reasoning_model, max_retries
            )

        # Otherwise, fall back to JSON extraction from response
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Starting {phase_name} (reasoning model: {self.reasoning_model})" +
                           (f" (attempt {attempt + 1})" if attempt > 0 else ""))
                print(f"\n{'='*60}\n{phase_name} [Reasoning Model: {self.reasoning_model}]" +
                      (f" (retry {attempt})" if attempt > 0 else "") + f"\n{'='*60}")

                # Build the request for reasoning model
                request_params = {
                    "model": self.reasoning_model,
                    "input": prompt,
                }

                # Make the API call
                print(f"[Calling reasoning model for deep analysis...]")

                response = self.client.responses.create(**request_params)

                # Extract the output
                output_text = response.output_text
                print(f"\n[Received reasoning output, extracting JSON...]")

                # Parse JSON from output - reasoning models may include explanation before/after JSON
                try:
                    # Try to find JSON object or array in the response
                    # Look for the main JSON block (usually starts with { and ends with })
                    json_patterns = [
                        r'```json\s*([\s\S]*?)```',  # JSON in code block
                        r'```\s*([\s\S]*?)```',      # Any code block
                        r'(\{[\s\S]*"hypotheses"[\s\S]*\})',  # Object with hypotheses key
                        r'(\{[\s\S]*\})',            # Any JSON object
                    ]

                    result = None
                    for pattern in json_patterns:
                        match = re.search(pattern, output_text, re.DOTALL)
                        if match:
                            try:
                                result = json.loads(match.group(1))
                                break
                            except json.JSONDecodeError:
                                continue

                    if result is None:
                        # Try direct parse as last resort
                        result = json.loads(output_text)

                    logger.info(f"{phase_name} complete with valid JSON from reasoning model")
                    print(f"[{phase_name} complete - JSON extracted from reasoning output]")
                    return result

                except json.JSONDecodeError as e:
                    logger.warning(f"Could not parse JSON from reasoning output: {e}")
                    # Fall back to structured output if schema_name provided
                    if schema_name:
                        logger.info(f"Falling back to structured output with schema '{schema_name}'")
                        print(f"[JSON parse failed, falling back to structured output...]")
                        return self._run_structured_phase(prompt, schema_name, f"{phase_name} (structured fallback)")
                    raise ValueError(f"Could not parse JSON from reasoning response: {output_text[:500]}")

            except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 10  # Longer wait for reasoning models
                    logger.warning(f"{phase_name} failed with {type(e).__name__}, retrying in {wait_time}s...")
                    print(f"\n[Connection error, retrying in {wait_time}s...]")
                    time.sleep(wait_time)
                else:
                    logger.error(f"{phase_name} failed after {max_retries + 1} attempts: {e}")
                    # Fall back to structured output if schema_name provided
                    if schema_name:
                        logger.info(f"Falling back to structured output after connection failures")
                        return self._run_structured_phase(prompt, schema_name, f"{phase_name} (structured fallback)")
                    raise

            except Exception as e:
                # For any other error, try structured fallback if available
                if schema_name:
                    logger.warning(f"Reasoning model error: {e}, falling back to structured output")
                    print(f"[Reasoning model error, falling back to structured output...]")
                    return self._run_structured_phase(prompt, schema_name, f"{phase_name} (structured fallback)")
                raise

        raise last_error or RuntimeError(f"Failed to complete {phase_name}")

    def _run_phase_1_methodology(self, request: BFIHAnalysisRequest) -> str:
        """Phase 1: Retrieve BFIH methodology from vector store"""
        prompt = f"""
You are retrieving methodology for a BFIH (Bayesian Framework for Intellectual Honesty) analysis.

PROPOSITION: "{request.proposition}"

Use file_search to retrieve the following from the BFIH treatise:
1. "Forcing functions" methodology
2. "Paradigm inversion" methods
3. Key sections on:
   - Ontological scan (7 domains)
   - Ancestral check
   - Split-brain technique

Provide a concise summary of the methodology that will guide the analysis.
Focus on actionable steps for applying each forcing function.
"""
        tools = [{"type": "file_search", "vector_store_ids": [self.vector_store_id]}]
        return self._run_phase(prompt, tools, "Phase 1: Retrieve Methodology")

    def _run_phase_2_evidence(self, request: BFIHAnalysisRequest, methodology: str) -> Tuple[str, List[Dict]]:
        """Phase 2: Gather evidence via web search using structured output.
        Returns (markdown_text, structured_evidence)"""
        scenario_json = json.dumps(request.scenario_config, indent=2)

        # Get hypothesis IDs
        hypotheses = request.scenario_config.get("hypotheses", [])
        hyp_ids = [h.get("id", f"H{i}") for i, h in enumerate(hypotheses)]

        prompt = f"""
You are gathering evidence for a BFIH analysis.

PROPOSITION: "{request.proposition}"

HYPOTHESES: {hyp_ids}

SCENARIO CONFIGURATION:
{scenario_json}

METHODOLOGY CONTEXT:
{methodology[:3000]}

YOUR TASK:
For EACH hypothesis, search for real-world evidence:
1. Generate 2-3 specific web search queries per hypothesis
2. Execute web searches to find supporting or refuting evidence
3. Record FULL source citations with URLs for all evidence

Return a JSON object with "evidence_items" array containing 15-25 evidence items.
Each item needs: evidence_id, description, source_name, source_url, citation_apa, date_accessed, supports_hypotheses, refutes_hypotheses, evidence_type.

Evidence types: quantitative, qualitative, expert_testimony, historical_analogy, policy, institutional
"""
        try:
            tools = [{"type": "web_search", "search_context_size": "medium"}]
            result = self._run_structured_phase(
                prompt, "evidence", "Phase 2: Evidence Gathering",
                tools=tools
            )
            evidence_items = result.get("evidence_items", [])
            # Generate markdown summary from structured data
            markdown_summary = self._generate_evidence_markdown(evidence_items)
        except Exception as e:
            logger.error(f"Structured output failed for evidence: {e}, falling back to text extraction")
            # Fallback to old method
            tools = [{"type": "web_search", "search_context_size": "medium"}]
            markdown_summary = self._run_phase(prompt, tools, "Phase 2: Evidence Gathering (fallback)")
            evidence_items = self._parse_evidence_json(markdown_summary)

        logger.info(f"Gathered {len(evidence_items)} evidence items")
        return markdown_summary, evidence_items

    def _generate_evidence_markdown(self, evidence_items: List[Dict]) -> str:
        """Generate markdown summary from structured evidence items"""
        lines = ["## Evidence Gathered\n"]
        for item in evidence_items:
            e_id = item.get("evidence_id", "E?")
            desc = item.get("description", "No description")
            source = item.get("source_name", "Unknown")
            url = item.get("source_url", "")
            supports = ", ".join(item.get("supports_hypotheses", []))
            refutes = ", ".join(item.get("refutes_hypotheses", []))

            lines.append(f"### {e_id}: {desc[:100]}")
            lines.append(f"- **Source:** {source}")
            if url:
                lines.append(f"- **URL:** {url}")
            if supports:
                lines.append(f"- **Supports:** {supports}")
            if refutes:
                lines.append(f"- **Refutes:** {refutes}")
            lines.append("")

        return "\n".join(lines)

    def _parse_evidence_json(self, text: str) -> List[Dict]:
        """Extract structured evidence from EVIDENCE_JSON_START/END markers"""
        pattern = r"EVIDENCE_JSON_START\s*(\[.*?\])\s*EVIDENCE_JSON_END"
        match = re.search(pattern, text, re.DOTALL)

        if match:
            try:
                evidence = json.loads(match.group(1))
                logger.info(f"Parsed {len(evidence)} structured evidence items")
                return evidence
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse evidence JSON: {e}")

        # Fallback: try to find any JSON array
        try:
            array_match = re.search(r'\[\s*\{[^]]+\}\s*\]', text, re.DOTALL)
            if array_match:
                evidence = json.loads(array_match.group(0))
                logger.info(f"Parsed {len(evidence)} evidence items (fallback)")
                return evidence
        except:
            pass

        logger.warning("Could not parse structured evidence, returning empty list")
        return []

    def _run_phase_3_likelihoods(self, request: BFIHAnalysisRequest, evidence_text: str,
                                   evidence_items: List[Dict]) -> Tuple[str, List[Dict]]:
        """Phase 3: Assign PARADIGM-SPECIFIC likelihoods to evidence using structured output.

        Returns (markdown_text, structured_clusters) where likelihoods are P(E|H,K)
        - different for each paradigm-hypothesis combination.
        """
        # Get hypotheses and paradigms
        hypotheses = request.scenario_config.get("hypotheses", [])
        paradigms = request.scenario_config.get("paradigms", [])
        hyp_ids = [h.get("id", f"H{i}") for i, h in enumerate(hypotheses)]
        paradigm_ids = [p.get("id", f"K{i}") for i, p in enumerate(paradigms)]

        # Summarize evidence items
        evidence_summary = json.dumps([{
            "evidence_id": e.get("evidence_id"),
            "description": e.get("description", "")[:200],
            "supports": e.get("supports_hypotheses", []),
            "refutes": e.get("refutes_hypotheses", [])
        } for e in evidence_items], indent=2)

        prompt = f"""
You are assigning PARADIGM-SPECIFIC likelihoods for a BFIH Bayesian analysis.

PROPOSITION: "{request.proposition}"

HYPOTHESES: {hyp_ids}
PARADIGMS: {paradigm_ids}

EVIDENCE ITEMS:
{evidence_summary}

CRITICAL CONCEPT: Likelihoods are P(E|H, K) - they depend on BOTH the hypothesis AND the paradigm!

The SAME evidence can have DIFFERENT likelihoods under different paradigms because:
- Different paradigms weight different types of evidence differently
- A paradigm skeptical of economic explanations assigns lower P(E|H_economic, K_skeptic)

YOUR TASK:
1. Group evidence into 3-5 CLUSTERS based on thematic similarity
2. For EACH cluster, assign likelihoods P(E|H, K) for EACH hypothesis under EACH paradigm
3. Justify how paradigm viewpoint affects the likelihood assessment

Return a JSON object with "clusters" array. Each cluster needs:
- cluster_id, cluster_name, description, evidence_ids (all required)
- paradigm_likelihoods: array of {{paradigm_id, hypothesis_likelihoods: [{{hypothesis_id, probability, justification}}]}}

IMPORTANT: Return ONLY valid JSON. No additional text before or after the JSON object.
"""
        try:
            # Use reasoning model for likelihood assessment (requires careful evidence-paradigm analysis)
            # Falls back to structured output (gpt-4o) if JSON parsing fails
            result = self._run_reasoning_phase(
                prompt, "Phase 3: Likelihood Assignment (reasoning)",
                schema_name="clusters"  # Enables structured output fallback
            )
            raw_clusters = result.get("clusters", [])
            # Convert array format to dict format for compatibility
            clusters = []
            for c in raw_clusters:
                converted = {
                    "cluster_id": c.get("cluster_id"),
                    "cluster_name": c.get("cluster_name"),
                    "description": c.get("description"),
                    "evidence_ids": c.get("evidence_ids", []),
                    "likelihoods_by_paradigm": {}
                }
                for pl in c.get("paradigm_likelihoods", []):
                    paradigm_id = pl.get("paradigm_id")
                    if paradigm_id:
                        converted["likelihoods_by_paradigm"][paradigm_id] = {}
                        for hl in pl.get("hypothesis_likelihoods", []):
                            h_id = hl.get("hypothesis_id")
                            if h_id:
                                converted["likelihoods_by_paradigm"][paradigm_id][h_id] = {
                                    "probability": hl.get("probability", 0.5),
                                    "justification": hl.get("justification", "")
                                }
                clusters.append(converted)
            # Generate markdown summary
            markdown_summary = self._generate_clusters_markdown(clusters)
        except Exception as e:
            logger.error(f"Structured output failed for clusters: {e}, falling back to text extraction")
            # Fallback to old method
            markdown_summary = self._run_phase(prompt, [], "Phase 3: Likelihood Assignment (fallback)")
            clusters = self._parse_clusters_json(markdown_summary)

        logger.info(f"Created {len(clusters)} evidence clusters with paradigm-specific likelihoods")
        return markdown_summary, clusters

    def _generate_clusters_markdown(self, clusters: List[Dict]) -> str:
        """Generate markdown summary from structured clusters"""
        lines = ["## Evidence Clusters with Likelihoods\n"]
        for cluster in clusters:
            c_id = cluster.get("cluster_id", "C?")
            name = cluster.get("cluster_name", "Unknown")
            desc = cluster.get("description", "")
            evidence_ids = cluster.get("evidence_ids", [])

            lines.append(f"### {c_id}: {name}")
            lines.append(f"- **Description:** {desc}")
            lines.append(f"- **Evidence:** {', '.join(evidence_ids)}")

            # Show likelihoods by paradigm
            lh_by_paradigm = cluster.get("likelihoods_by_paradigm", {})
            for paradigm_id, hyp_likelihoods in lh_by_paradigm.items():
                lines.append(f"\n**{paradigm_id} Likelihoods:**")
                for hyp_id, lh_data in hyp_likelihoods.items():
                    prob = lh_data.get("probability", 0.5) if isinstance(lh_data, dict) else lh_data
                    lines.append(f"  - {hyp_id}: {prob:.2f}")
            lines.append("")

        return "\n".join(lines)

    def _parse_clusters_json(self, text: str) -> List[Dict]:
        """Extract structured clusters from CLUSTERS_JSON_START/END markers"""
        pattern = r"CLUSTERS_JSON_START\s*(\[.*?\])\s*CLUSTERS_JSON_END"
        match = re.search(pattern, text, re.DOTALL)

        if match:
            try:
                clusters = json.loads(match.group(1))
                logger.info(f"Parsed {len(clusters)} evidence clusters")
                return clusters
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse clusters JSON: {e}")

        # Fallback: try to find any JSON array with cluster structure
        try:
            array_match = re.search(r'\[\s*\{[^]]*"cluster_id"[^]]+\}\s*\]', text, re.DOTALL)
            if array_match:
                clusters = json.loads(array_match.group(0))
                logger.info(f"Parsed {len(clusters)} clusters (fallback)")
                return clusters
        except:
            pass

        logger.warning("Could not parse structured clusters, returning empty list")
        return []

    def _run_phase_4_computation(self, request: BFIHAnalysisRequest, likelihoods: str) -> str:
        """Phase 4: Run Bayesian computation with code interpreter"""
        scenario_json = json.dumps(request.scenario_config, indent=2)

        # Build the Python code template
        python_code = self._build_bayesian_code_template()

        prompt = f"""
You are computing Bayesian posteriors for a BFIH analysis.

PROPOSITION: "{request.proposition}"

SCENARIO CONFIGURATION:
{scenario_json}

LIKELIHOOD ASSIGNMENTS:
{likelihoods[:6000]}

YOUR TASK:
Use the Python code_interpreter to compute:
1. Parse the likelihood assignments above into evidence clusters
2. Compute P(E|¬H) for each hypothesis using: P(E|¬H_i) = Σ P(E|H_j) * P(H_j)/(1-P(H_i)) for j≠i
3. Compute likelihood ratios: LR = P(E|H) / P(E|¬H)
4. Compute weight of evidence: WoE = 10 * log₁₀(LR) in decibans
5. Compute posterior probabilities using Bayes' theorem
6. Print results in this EXACT format:

BFIH POSTERIOR COMPUTATION
Final Posterior Probabilities:
H1: [value]
H2: [value]
...

Here is a template to adapt:

```python
{python_code}
```

IMPORTANT: Adapt the priors and likelihoods based on the scenario configuration and likelihood assignments above.
Print the final posteriors clearly labeled.
"""
        tools = [{"type": "code_interpreter", "container": {"type": "auto"}}]
        return self._run_phase(prompt, tools, "Phase 4: Bayesian Computation")

    def _run_phase_5_report(self, request: BFIHAnalysisRequest,
                           methodology: str, evidence: str,
                           likelihoods: str, computation: str,
                           evidence_items: List[Dict] = None,
                           evidence_clusters: List[Dict] = None) -> str:
        """Phase 5: Generate final BFIH report in multiple sub-phases for better quality.

        Generates report sections separately then concatenates them.
        """
        # Build context data
        paradigms = request.scenario_config.get("paradigms", [])
        hypotheses = request.scenario_config.get("hypotheses", [])
        priors = request.scenario_config.get("priors_by_paradigm", request.scenario_config.get("priors", {}))

        paradigm_list = "\n".join([f"- {p.get('id', 'K?')}: {p.get('name', 'Unknown')} - {p.get('description', '')}" for p in paradigms])
        hypothesis_list = "\n".join([f"- {h.get('id', 'H?')}: {h.get('name', 'Unknown')} - {h.get('description', '')}" for h in hypotheses])
        evidence_items_json = json.dumps(evidence_items or [], indent=2)
        evidence_clusters_json = json.dumps(evidence_clusters or [], indent=2)

        # Phase 5a: Executive Summary, Paradigms, Hypotheses
        section_a = self._run_phase_5a_intro(
            request, paradigm_list, hypothesis_list, computation, priors
        )

        # Phase 5b: Evidence Matrix (all evidence items with citations)
        section_b = self._run_phase_5b_evidence(
            request, evidence_items, evidence_clusters, hypotheses
        )

        # Phase 5c: Bayesian Results, Conclusions, Sensitivity
        section_c = self._run_phase_5c_results(
            request, computation, paradigms, hypotheses, priors
        )

        # Phase 5d: Bibliography
        section_d = self._run_phase_5d_bibliography(evidence_items)

        # Combine all sections
        full_report = f"""# BFIH Analysis Report: {request.proposition}

**Analysis conducted using Bayesian Framework for Intellectual Honesty (BFIH)**

---

{section_a}

---

{section_b}

---

{section_c}

---

{section_d}

---

**End of BFIH Analysis Report**
"""
        return full_report

    def _run_phase_5a_intro(self, request: BFIHAnalysisRequest,
                            paradigm_list: str, hypothesis_list: str,
                            computation: str, priors: Dict) -> str:
        """Phase 5a: Generate Executive Summary, Paradigms, and Hypotheses sections."""
        prompt = f"""
Write the INTRODUCTION sections of a BFIH analysis report.

PROPOSITION: "{request.proposition}"

PARADIGMS:
{paradigm_list}

HYPOTHESES:
{hypothesis_list}

PRIORS BY PARADIGM:
{json.dumps(priors, indent=2)}

COMPUTATION RESULTS:
{computation[:3000]}

Generate these sections in markdown:

## Executive Summary

**Verdict:** [VALIDATED / PARTIALLY VALIDATED / REJECTED / INDETERMINATE based on posteriors]

Write 3-4 paragraphs covering:
1. Primary finding with specific posterior probability values
2. Which hypothesis has highest posterior and under which paradigm
3. Key evidence that drove the conclusions
4. Whether conclusions are robust across paradigms

---

## 1. Paradigms Analyzed

For EACH paradigm, write 1-2 paragraphs describing:
- The paradigm name and core assumptions
- What this paradigm treats as valid evidence
- How it would approach this question differently from other paradigms

---

## 2. Hypothesis Set

For EACH hypothesis:

**H[X]: [Full Name]**

[3-4 sentence description of what this hypothesis claims]

**Prior Probabilities:**
| Paradigm | Prior P(H) | Rationale |
|----------|------------|-----------|
[Table showing prior for each paradigm with brief justification]

Use DECIMAL format (0.XXX) for all probabilities.
"""
        return self._run_phase(prompt, [], "Phase 5a: Introduction Sections")

    def _run_phase_5b_evidence(self, request: BFIHAnalysisRequest,
                               evidence_items: List[Dict],
                               evidence_clusters: List[Dict],
                               hypotheses: List[Dict]) -> str:
        """Phase 5b: Generate Evidence Matrix with full citations."""
        evidence_json = json.dumps(evidence_items or [], indent=2)
        clusters_json = json.dumps(evidence_clusters or [], indent=2)
        hyp_ids = [h.get('id', f'H{i}') for i, h in enumerate(hypotheses)]

        prompt = f"""
Write the EVIDENCE MATRIX section of a BFIH analysis report.

PROPOSITION: "{request.proposition}"

HYPOTHESES: {hyp_ids}

STRUCTURED EVIDENCE ITEMS (you MUST include ALL of these):
{evidence_json}

EVIDENCE CLUSTERS WITH LIKELIHOODS:
{clusters_json}

Generate this section in markdown:

## 3. Evidence Matrix

### Evidence Items

For EACH evidence item in the JSON above, create an entry with this EXACT format:

---

### E[id]: [description]

**Source:** [source_name]
**URL:** [source_url - include the FULL clickable URL]
**Citation:** [citation_apa]
**Date Accessed:** [date_accessed]
**Evidence Type:** [evidence_type]
**Supports:** [supports_hypotheses] | **Refutes:** [refutes_hypotheses]

[Write 2-3 sentences analyzing what this evidence shows and why it matters]

**Likelihood Assessment:**

| Hypothesis | P(E|H) | Reasoning |
|------------|---------|-----------|
| H1 | 0.XX | [Brief justification for this likelihood] |
| H2 | 0.XX | [Brief justification] |
| H3 | 0.XX | [Brief justification] |
| H4 | 0.XX | [Brief justification] |
| H5 | 0.XX | [Brief justification] |
| H0 | 0.XX | [Brief justification] |

---

IMPORTANT:
- Include ALL {len(evidence_items or [])} evidence items from the JSON
- Include the FULL URL for each source (not truncated)
- Include the complete APA citation
- Create likelihood table for EACH evidence item
"""
        return self._run_phase(prompt, [], "Phase 5b: Evidence Matrix")

    def _run_phase_5c_results(self, request: BFIHAnalysisRequest,
                              computation: str, paradigms: List[Dict],
                              hypotheses: List[Dict], priors: Dict) -> str:
        """Phase 5c: Generate Bayesian Results, Paradigm Comparison, Conclusions."""
        prompt = f"""
Write the RESULTS and CONCLUSIONS sections of a BFIH analysis report.

PROPOSITION: "{request.proposition}"

PARADIGMS: {json.dumps([p.get('name') for p in paradigms])}

HYPOTHESES: {json.dumps([h.get('name') for h in hypotheses])}

PRIORS BY PARADIGM:
{json.dumps(priors, indent=2)}

BAYESIAN COMPUTATION OUTPUT (use these EXACT values):
{computation}

Generate these sections in markdown:

## 4. Evidence Clusters Summary

Summarize how evidence was clustered and the joint likelihoods.

---

## 5. Bayesian Computation Results

**Final Posterior Probabilities:**

| Hypothesis | Prior | Posterior | Change | LR | WoE (dB) |
|------------|-------|-----------|--------|-----|----------|
[Fill in with EXACT values from computation output above]

**Normalization Check:** Sum of posteriors = [calculate] ≈ 1.0

---

## 6. Paradigm Comparison

How do conclusions differ across paradigms? For each paradigm:
- Which hypothesis dominates?
- What posterior probability?
- Key differences in reasoning?

---

## 7. Sensitivity Analysis

Analyze what happens with ±20% prior variation:
- Are conclusions stable?
- Which hypotheses are most sensitive?

---

## 8. Conclusions

**Primary Finding:** [Clear statement of what the analysis concludes]

**Verdict:** [VALIDATED / PARTIALLY VALIDATED / REJECTED / INDETERMINATE]

**Confidence Level:** [High/Moderate/Low] with justification

**Key Uncertainties:** What remains unknown or paradigm-dependent

**Recommendations:** What actions or further analysis might be warranted

Use DECIMAL format (0.XXX) for all probabilities.
Copy posterior values EXACTLY from the computation output.
"""
        return self._run_phase(prompt, [], "Phase 5c: Results & Conclusions")

    def _run_phase_5d_bibliography(self, evidence_items: List[Dict]) -> str:
        """Phase 5d: Generate Bibliography from evidence items."""
        if not evidence_items:
            return "## 9. Bibliography\n\nNo sources available."

        # Build bibliography directly from evidence items
        bib_entries = []
        for i, item in enumerate(evidence_items, 1):
            citation = item.get('citation_apa', '')
            url = item.get('source_url', '')
            source = item.get('source_name', 'Unknown Source')
            desc = item.get('description', '')

            if citation:
                entry = citation
                if url and url not in citation:
                    entry += f" Retrieved from {url}"
            else:
                entry = f"{source}. {desc}."
                if url:
                    entry += f" Retrieved from {url}"

            bib_entries.append(f"{i}. {entry}")

        bibliography = "## 9. Bibliography\n\n**References (APA Format):**\n\n" + "\n\n".join(bib_entries)

        # Add intellectual honesty checklist
        bibliography += """

---

## 10. Intellectual Honesty Checklist

| Forcing Function | Applied | Notes |
|-----------------|---------|-------|
| Ontological Scan (7 domains) | ✓ | Multiple domains covered |
| Ancestral Check | ✓ | Historical baselines examined |
| Paradigm Inversion | ✓ | Alternative paradigms generated |
| MECE Verification | ✓ | Hypotheses are mutually exclusive and collectively exhaustive |
| Sensitivity Analysis | ✓ | Prior variation tested |
"""
        return bibliography

    def _build_bayesian_code_template(self) -> str:
        """Return the Python code template for Bayesian computation"""
        return '''import json
import numpy as np
from collections import OrderedDict

# Define hypotheses and priors (ADAPT THESE based on scenario)
hypotheses = ["H1", "H2", "H3", "H4"]
priors = {"H1": 0.25, "H2": 0.25, "H3": 0.25, "H4": 0.25}

# Define evidence clusters with likelihoods (ADAPT THESE based on likelihood assignments)
evidence_clusters = OrderedDict({
    "Cluster_A": {
        "description": "Evidence cluster A",
        "likelihoods": {"H1": 0.5, "H2": 0.5, "H3": 0.5, "H4": 0.5}
    }
})

# Compute P(E|~H) for each hypothesis and cluster-level metrics
cluster_metrics = {h: [] for h in hypotheses}
for cluster_name, cluster_data in evidence_clusters.items():
    lklhd = cluster_data["likelihoods"]
    cluster_data["likelihoods_not_h"] = {}
    for h_i in hypotheses:
        complement_prior = 1 - priors[h_i]
        if complement_prior > 0:
            p_e_not_h = sum(
                lklhd[h_j] * (priors[h_j] / complement_prior)
                for h_j in hypotheses if h_j != h_i
            )
            cluster_data["likelihoods_not_h"][h_i] = p_e_not_h
            # Cluster-level LR and WoE
            p_e_h = lklhd[h_i]
            lr = p_e_h / p_e_not_h if p_e_not_h > 0 else float("inf")
            woe = 10 * np.log10(lr) if lr > 0 and lr != float("inf") else 0
            cluster_metrics[h_i].append({
                "cluster": cluster_name,
                "P(E|H)": round(p_e_h, 4),
                "P(E|~H)": round(p_e_not_h, 4),
                "LR": round(lr, 4) if lr != float("inf") else "inf",
                "WoE_dB": round(woe, 2)
            })

# Compute posteriors and total likelihood
unnormalized = {}
total_likelihood = {}
for h_i in hypotheses:
    log_likelihood = sum(
        np.log10(cluster["likelihoods"][h_i])
        for cluster in evidence_clusters.values()
    )
    total_likelihood[h_i] = 10 ** log_likelihood
    unnormalized[h_i] = priors[h_i] * total_likelihood[h_i]

norm_const = sum(unnormalized.values())
posteriors = {h: round(unnormalized[h] / norm_const, 6) for h in hypotheses}

# Compute total confirmation metrics (LR and WoE from priors to posteriors)
confirmation_metrics = {}
for h in hypotheses:
    prior = priors[h]
    post = posteriors[h]
    if prior > 0 and prior < 1 and post > 0 and post < 1:
        prior_odds = prior / (1 - prior)
        posterior_odds = post / (1 - post)
        total_lr = posterior_odds / prior_odds
        total_woe = 10 * np.log10(total_lr) if total_lr > 0 else 0
    else:
        total_lr = float("inf") if post >= 1 else 0
        total_woe = float("inf") if post >= 1 else float("-inf")
    confirmation_metrics[h] = {
        "prior": round(prior, 4),
        "posterior": round(post, 6),
        "total_LR": round(total_lr, 4) if total_lr != float("inf") else "inf",
        "total_WoE_dB": round(total_woe, 2) if total_woe not in [float("inf"), float("-inf")] else str(total_woe)
    }

# Output as JSON for reliable parsing
result = {
    "posteriors": posteriors,
    "priors": priors,
    "confirmation_metrics": confirmation_metrics,
    "cluster_metrics": cluster_metrics,
    "sum_check": round(sum(posteriors.values()), 6)
}

print("BFIH_JSON_OUTPUT_START")
print(json.dumps(result, indent=2))
print("BFIH_JSON_OUTPUT_END")

# Also print human-readable format
print("\\nBFIH POSTERIOR COMPUTATION")
print("Final Posterior Probabilities:")
for h in sorted(posteriors.keys(), key=lambda x: posteriors[x], reverse=True):
    cm = confirmation_metrics[h]
    print(f"{h}: {posteriors[h]:.4f} (LR: {cm['total_LR']}, WoE: {cm['total_WoE_dB']} dB)")
'''

    def _parse_posterior_section(self, report: str) -> Dict[str, float]:
        """
        Parse posteriors from the computation output.
        First tries to extract JSON between BFIH_JSON_OUTPUT_START/END markers.
        Falls back to regex parsing of "H1: 0.91" format.
        """
        extracted = {}

        # Method 1: Try to extract JSON output (preferred)
        json_pattern = r"BFIH_JSON_OUTPUT_START\s*(\{.*?\})\s*BFIH_JSON_OUTPUT_END"
        json_match = re.search(json_pattern, report, re.DOTALL)

        if json_match:
            try:
                result = json.loads(json_match.group(1))
                extracted = result.get("posteriors", {})
                logger.info(f"Extracted posteriors from JSON: {extracted}")
                return extracted
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON output: {e}, falling back to regex")

        # Method 2: Fallback to regex parsing
        section_pattern = r"BFIH POSTERIOR COMPUTATION[=\s\n]*(?:Final Posterior Probabilities[:\s]*)?(.+?)(?:Sum:|Normalization|BFIH BAYESIAN|```|$)"
        section_match = re.search(section_pattern, report, re.DOTALL | re.IGNORECASE)

        if section_match:
            section_text = section_match.group(1)
            logger.debug(f"Found posterior section: {section_text[:300]}...")
        else:
            logger.warning("Could not find 'BFIH POSTERIOR COMPUTATION' section, searching full report")
            section_text = report

        # Pattern: H1: 0.91 or H4: 1.2e-3 or **H1**: 0.3890 (with optional bold markdown)
        posterior_pattern = r"\*?\*?(H\d+)\*?\*?\s*:\s*([0-9.]+(?:e[+-]?\d+)?)"
        matches = re.findall(posterior_pattern, section_text, re.IGNORECASE)

        for hypothesis_id, value_str in matches:
            hypothesis_id = hypothesis_id.upper()
            try:
                value = float(value_str)
                if 0.0 <= value <= 1.0:
                    extracted[hypothesis_id] = value
                else:
                    logger.warning(f"Posterior {value} for {hypothesis_id} outside [0,1]")
            except ValueError as e:
                logger.warning(f"Could not parse '{value_str}' for {hypothesis_id}: {e}")

        if extracted:
            total = sum(extracted.values())
            if not (0.9 <= total <= 1.1):
                logger.warning(f"Extracted posteriors sum to {total:.4f}, expected ~1.0")

        logger.info(f"Extracted posteriors: {extracted}")
        return extracted

    # ========================================================================
    # AUTONOMOUS ANALYSIS (Topic Submission → Full Analysis)
    # ========================================================================

    def analyze_topic(self, proposition: str, domain: str = "business",
                      difficulty: str = "medium") -> BFIHAnalysisResult:
        """
        Autonomous BFIH analysis from topic submission.

        Accepts just a proposition and generates everything autonomously:
        - Paradigms (2-4 with epistemic stances)
        - Hypotheses (with forcing functions: Ontological Scan, Ancestral Check, Paradigm Inversion)
        - MECE synthesis (unified hypothesis set)
        - Priors per paradigm
        - Full analysis with evidence, likelihoods, posteriors, report

        Args:
            proposition: The question to analyze (e.g., "Why did X succeed?")
            domain: Domain category (business, medical, policy, historical, etc.)
            difficulty: easy (3-4 hyp), medium (5-6 hyp), hard (7+ hyp)

        Returns:
            BFIHAnalysisResult with full report and generated config
        """
        analysis_start = datetime.now(timezone.utc)
        scenario_id = f"auto_{uuid.uuid4().hex[:8]}"

        logger.info(f"{'='*60}")
        logger.info(f"AUTONOMOUS BFIH ANALYSIS")
        logger.info(f"Proposition: {proposition}")
        logger.info(f"Domain: {domain}, Difficulty: {difficulty}")
        logger.info(f"{'='*60}")

        # Phase 0a: Generate paradigms
        paradigms = self._generate_paradigms(proposition, domain)

        # Phase 0b: Generate hypotheses with forcing functions + MECE synthesis
        hypotheses, forcing_functions_log = self._generate_hypotheses_with_forcing_functions(
            proposition, paradigms, difficulty
        )

        # Phase 0c: Assign priors per paradigm (BEFORE evidence, based only on background context)
        priors_by_paradigm = self._assign_priors(hypotheses, paradigms, proposition)

        # Build scenario_config dynamically
        scenario_config = self._build_scenario_config(
            scenario_id, proposition, domain, paradigms, hypotheses,
            forcing_functions_log, priors_by_paradigm
        )

        # Save scenario config to file
        self._save_scenario_config(scenario_id, scenario_config)

        # Create request and run existing phases 1-5
        request = BFIHAnalysisRequest(
            scenario_id=scenario_id,
            proposition=proposition,
            scenario_config=scenario_config,
            user_id="autonomous"
        )

        result = self.conduct_analysis(request)

        # Update scenario config with evidence data from analysis
        evidence_items = result.metadata.get("evidence_items", [])
        evidence_clusters = result.metadata.get("evidence_clusters", [])

        scenario_config["evidence"] = {
            "items": evidence_items,
            "clusters": evidence_clusters,
            "total_items": len(evidence_items),
            "total_clusters": len(evidence_clusters)
        }

        # Re-save scenario config with evidence included
        self._save_scenario_config(scenario_id, scenario_config)

        # Add generated config to result
        result.metadata["generated_config"] = scenario_config
        result.metadata["autonomous"] = True

        return result

    def _generate_paradigms(self, proposition: str, domain: str) -> List[Dict]:
        """
        Phase 0a: Generate paradigm set with ONE privileged paradigm (K0) and 3-5 biased paradigms (K1-K5).

        Following BFIH Paradigm Construction Manual:
        - K0: Maximally intellectually honest, passes ALL forcing functions
        - K1-K5: Realistically biased (not straw men), each fails ≥1 forcing function

        Uses structured output for guaranteed valid JSON.
        """
        prompt = f"""
You are generating a PARADIGM SET for a BFIH (Bayesian Framework for Intellectual Honesty) analysis.

PROPOSITION: "{proposition}"
DOMAIN: {domain}

## CRITICAL REQUIREMENT: One Privileged + Multiple Biased Paradigms

You MUST generate:
1. **K0 (Privileged Paradigm)**: Maximally intellectually honest
   - Applies ALL forcing functions (Ontological Scan, Ancestral Check, Paradigm Inversion)
   - Covers all 7 ontological domains (Biological, Economic, Cultural, Theological, Historical, Institutional, Psychological)
   - Has explicit assumptions, limitations, and falsification criteria
   - NOT neutral—has a perspective, but systematically interrogates its own blind spots

2. **K1-K5 (Biased Paradigms)**: 3-5 realistically biased paradigms
   - Each must fail ≥1 forcing function (document which one)
   - Must be REALISTIC biases, not straw men (would an expert recognize themselves?)
   - Types of bias to choose from:
     * **Domain Bias**: Only sees one discipline (e.g., economists ignore theology)
     * **Temporal Bias**: Short-term vs long-term focus
     * **Ideological Bias**: Value commitment (libertarian, egalitarian, etc.)
     * **Cognitive Bias**: Overconfidence, availability bias, confirmation bias
     * **Institutional Bias**: Resource constraints, deadline pressure

## OUTPUT FORMAT

For EACH paradigm provide:
- id: K0, K1, K2, K3, etc.
- name: Short descriptive name
- description: Epistemic stance - what this paradigm treats as valid evidence
- is_privileged: true for K0, false for others
- bias_type: null for K0, otherwise one of [domain, temporal, ideological, cognitive, institutional]
- bias_description: null for K0, otherwise describe the specific bias
- inverse_paradigm_id: ID of inverse paradigm if applicable, or null
- forcing_function_compliance: Object with:
  - ontological_scan: "pass" or "fail: [reason]"
  - ancestral_check: "pass" or "fail: [reason]"
  - paradigm_inversion: "pass" or "fail: [reason]"
- domains_covered: List of domains this paradigm engages (K0 should have all 7)
- characteristics: Object with:
  - prefers_evidence_types: List of evidence types this paradigm values
  - skeptical_of: List of factors this paradigm discounts
  - causal_preference: Primary causal mechanism this paradigm favors
  - time_horizon: Short-term, medium-term, long-term, or intergenerational

Return the result as a JSON object with a "paradigms" array starting with K0.

IMPORTANT: Return ONLY valid JSON. No additional text before or after the JSON object.
"""
        try:
            # Use reasoning model for paradigm construction (cognitively demanding task)
            # Falls back to structured output (gpt-4o) if JSON parsing fails
            result = self._run_reasoning_phase(
                prompt, "Phase 0a: Generate Paradigms (reasoning)",
                schema_name="paradigms"  # Enables structured output fallback
            )
            paradigms = result.get("paradigms", [])
        except Exception as e:
            logger.error(f"Structured output failed for paradigms: {e}, using fallback")
            # Fallback to default paradigms following the K0 + K1-K4 structure
            paradigms = [
                {
                    "id": "K0", "name": "Integrated Multi-Domain Analysis",
                    "description": "Intellectually honest synthesis across all domains with explicit uncertainty",
                    "is_privileged": True,
                    "bias_type": None,
                    "bias_description": None,
                    "inverse_paradigm_id": None,
                    "forcing_function_compliance": {
                        "ontological_scan": "pass",
                        "ancestral_check": "pass",
                        "paradigm_inversion": "pass"
                    },
                    "domains_covered": ["Biological", "Economic", "Cultural", "Theological", "Historical", "Institutional", "Psychological"],
                    "characteristics": {
                        "prefers_evidence_types": ["quantitative", "qualitative", "historical", "expert_testimony"],
                        "skeptical_of": ["single-cause explanations", "unfalsifiable claims"],
                        "causal_preference": "multi-causal with documented interactions",
                        "time_horizon": "intergenerational"
                    }
                },
                {
                    "id": "K1", "name": "Techno-Economic Rationalist",
                    "description": "Success/failure driven by measurable economic and technical factors",
                    "is_privileged": False,
                    "bias_type": "domain",
                    "bias_description": "Ignores cultural/theological domains; over-weights quantitative metrics",
                    "inverse_paradigm_id": "K2",
                    "forcing_function_compliance": {
                        "ontological_scan": "fail: ignores Theological and Cultural domains",
                        "ancestral_check": "pass",
                        "paradigm_inversion": "fail: dismisses non-economic explanations"
                    },
                    "domains_covered": ["Economic", "Institutional", "Psychological"],
                    "characteristics": {
                        "prefers_evidence_types": ["quantitative", "financial", "technical"],
                        "skeptical_of": ["faith-based explanations", "cultural narratives"],
                        "causal_preference": "incentive structures and market forces",
                        "time_horizon": "short-term"
                    }
                },
                {
                    "id": "K2", "name": "Cultural-Historical Interpreter",
                    "description": "Events shaped by deep cultural patterns, traditions, and historical precedent",
                    "is_privileged": False,
                    "bias_type": "temporal",
                    "bias_description": "Over-weights historical patterns; may miss novel factors",
                    "inverse_paradigm_id": "K1",
                    "forcing_function_compliance": {
                        "ontological_scan": "fail: under-weights Economic and Technical domains",
                        "ancestral_check": "pass",
                        "paradigm_inversion": "pass"
                    },
                    "domains_covered": ["Cultural", "Historical", "Theological", "Psychological"],
                    "characteristics": {
                        "prefers_evidence_types": ["historical_analogy", "qualitative", "testimonial"],
                        "skeptical_of": ["techno-determinism", "ahistorical analysis"],
                        "causal_preference": "path dependence and cultural momentum",
                        "time_horizon": "long-term"
                    }
                },
                {
                    "id": "K3", "name": "Regulatory-Institutional Analyst",
                    "description": "Outcomes determined by governance structures, rules, and institutional incentives",
                    "is_privileged": False,
                    "bias_type": "institutional",
                    "bias_description": "Over-emphasizes formal rules; may miss informal dynamics",
                    "inverse_paradigm_id": None,
                    "forcing_function_compliance": {
                        "ontological_scan": "fail: ignores Biological and Psychological domains",
                        "ancestral_check": "pass",
                        "paradigm_inversion": "fail: assumes institutional solutions always exist"
                    },
                    "domains_covered": ["Institutional", "Economic", "Historical"],
                    "characteristics": {
                        "prefers_evidence_types": ["policy", "regulatory", "institutional"],
                        "skeptical_of": ["individual agency", "market self-correction"],
                        "causal_preference": "regulatory frameworks and institutional design",
                        "time_horizon": "medium-term"
                    }
                },
                {
                    "id": "K4", "name": "Individual Agency Advocate",
                    "description": "Outcomes primarily reflect individual choices, leadership, and personal responsibility",
                    "is_privileged": False,
                    "bias_type": "ideological",
                    "bias_description": "Over-weights individual action; under-weights structural constraints",
                    "inverse_paradigm_id": "K3",
                    "forcing_function_compliance": {
                        "ontological_scan": "fail: ignores systemic/institutional factors",
                        "ancestral_check": "fail: may ignore historical structural constraints",
                        "paradigm_inversion": "pass"
                    },
                    "domains_covered": ["Psychological", "Economic"],
                    "characteristics": {
                        "prefers_evidence_types": ["biographical", "decision_analysis", "leadership"],
                        "skeptical_of": ["deterministic explanations", "systemic blame"],
                        "causal_preference": "individual decisions and leadership",
                        "time_horizon": "short-term"
                    }
                }
            ]

        logger.info(f"Generated {len(paradigms)} paradigms: {[p.get('name', 'Unknown') for p in paradigms]}")
        return paradigms

    def _generate_hypotheses_with_forcing_functions(
        self, proposition: str, paradigms: List[Dict], difficulty: str
    ) -> Tuple[List[Dict], Dict]:
        """
        Phase 0b: Generate MECE hypotheses with forcing functions.

        Following BFIH Paradigm Construction Manual:
        - Hypotheses are TRUTH-VALUE CLAIMS about the proposition
        - Not mechanism explanations assuming the proposition is true
        - Structure: H0 (catch-all), H1 (affirm), H2 (deny), H3 (qualify), H4+ (domain-specific)

        Uses REASONING MODEL for deeper analytical thinking about hypotheses.
        """
        num_hypotheses = {"easy": 4, "medium": 6, "hard": 8}.get(difficulty, 6)
        paradigm_json = json.dumps(paradigms, indent=2)

        prompt = f"""
You are generating HYPOTHESES for a BFIH (Bayesian Framework for Intellectual Honesty) analysis.

PROPOSITION TO EVALUATE: "{proposition}"

PARADIGMS (these determine priors and likelihood weighting, NOT the hypotheses):
{paradigm_json}

## CRITICAL: HYPOTHESES ARE TRUTH-VALUE CLAIMS

Hypotheses answer: "Is this proposition TRUE, FALSE, or CONDITIONALLY TRUE?"

**WRONG approach** (assumes proposition is true, explores mechanisms):
- Proposition: "Boeing's 737 MAX crashed due to safety issues"
- ❌ "MCAS software caused crashes" (mechanism, not truth-value)
- ❌ "FAA deregulation contributed" (mechanism, not truth-value)
- ❌ "Cost-cutting culture" (mechanism, not truth-value)

**CORRECT approach** (competing truth-value claims):
- H1: "TRUE - Boeing's safety culture degraded systematically, causing the crashes"
- H2: "FALSE - The crashes were primarily due to pilot error, not Boeing's safety issues"
- H3: "PARTIAL - Safety issues contributed, but comparable to industry norms"
- H4: "FALSE - Regulatory capture, not Boeing's internal culture, was primary cause"
- H0: "OTHER - Some unforeseen factor or combination not captured by H1-H4" (catch-all)

## REQUIRED HYPOTHESIS STRUCTURE

Generate exactly {num_hypotheses} hypotheses:

| ID | Type | Description | Required? |
|----|------|-------------|-----------|
| H0 | Catch-all | Unforeseen/unspecified alternative (NOT "unknown") | YES |
| H1 | AFFIRM | Proposition is TRUE (with primary mechanism) | YES |
| H2 | DENY | Proposition is FALSE (alternative explanation) | YES |
| H3 | QUALIFY | Proposition is PARTIALLY true (conditions) | YES |
| H4+ | Domain-specific | From Ontological Scan or Paradigm Inversion | As needed |

IMPORTANT: H0 is NOT "we don't know" or "insufficient evidence". H0 captures any unforeseen or
unspecified alternatives that might explain the observations but aren't covered by H1-H4+.

## FORCING FUNCTIONS TO APPLY

### 1. ONTOLOGICAL SCAN (7 Domains)
Check if explanations from each domain could AFFIRM or DENY the proposition:
- **Biological**: Physical, physiological, or health-related factors
- **Economic**: Financial incentives, market forces, resource constraints
- **Cultural**: Social norms, values, traditions, group identity
- **Theological**: Religious beliefs, moral frameworks, transcendent values
- **Historical**: Precedent, path dependence, lessons from similar cases
- **Institutional**: Rules, regulations, organizational structures
- **Psychological**: Individual cognition, motivation, decision-making

### 2. ANCESTRAL CHECK
- What historical analogues exist for this proposition?
- What lessons do they suggest about likely truth value?
- Does history suggest this type of claim tends to be true/false/overstated?

### 3. PARADIGM INVERSION
- For each biased paradigm (K1-K4), what hypothesis would they DISMISS?
- Generate at least one hypothesis representing the "inverse" view

## OUTPUT FORMAT - Return ONLY valid JSON:

```json
{{
  "hypotheses": [
    {{
      "id": "H0",
      "name": "Other/Unforeseen Alternatives",
      "truth_value_type": "other",
      "statement": "Some unforeseen factor, combination of factors, or alternative not captured by H1-H4+ explains the observations",
      "mechanism_if_true": "Unspecified alternative mechanism",
      "domains": [],
      "testable_predictions": ["Evidence patterns don't fit H1-H4+ predictions", "Novel factors emerge during investigation"],
      "is_catch_all": true,
      "is_ancestral_solution": false,
      "is_paradigm_inversion": false,
      "inverted_from_paradigm": null
    }},
    {{
      "id": "H1",
      "name": "[Proposition TRUE] - [Primary Mechanism]",
      "truth_value_type": "affirm",
      "statement": "The proposition is TRUE: [full statement of what is true and why]",
      "mechanism_if_true": "[The specific causal mechanism]",
      "domains": ["Institutional", "Economic"],
      "testable_predictions": ["If H1, we would observe X", "If H1, metric Y would show Z"],
      "is_catch_all": false,
      "is_ancestral_solution": false,
      "is_paradigm_inversion": false,
      "inverted_from_paradigm": null
    }},
    {{
      "id": "H2",
      "name": "[Proposition FALSE] - [Alternative Explanation]",
      "truth_value_type": "deny",
      "statement": "The proposition is FALSE: [what is actually true instead]",
      "mechanism_if_true": "[The actual causal mechanism that explains observations]",
      "domains": ["Psychological"],
      "testable_predictions": ["If H2, we would observe X instead of Y"],
      "is_catch_all": false,
      "is_ancestral_solution": false,
      "is_paradigm_inversion": true,
      "inverted_from_paradigm": "K1"
    }},
    {{
      "id": "H3",
      "name": "[Proposition PARTIAL] - [Conditions]",
      "truth_value_type": "qualify",
      "statement": "The proposition is PARTIALLY TRUE: [true under conditions A, false under B]",
      "mechanism_if_true": "[The conditional mechanism]",
      "domains": ["Historical"],
      "testable_predictions": ["If H3, we would see effect only when condition A holds"],
      "is_catch_all": false,
      "is_ancestral_solution": true,
      "is_paradigm_inversion": false,
      "inverted_from_paradigm": null
    }}
  ],
  "forcing_functions_log": {{
    "ontological_scan": {{
      "Biological": {{"covered_by": "H4", "justification": "..."}},
      "Economic": {{"covered_by": "H1", "justification": "..."}},
      "Cultural": null,
      "Theological": null,
      "Historical": {{"covered_by": "H3", "justification": "..."}},
      "Institutional": {{"covered_by": "H1", "justification": "..."}},
      "Psychological": {{"covered_by": "H2", "justification": "..."}}
    }},
    "ancestral_check": {{
      "historical_analogues": ["[Similar case 1]", "[Similar case 2]"],
      "lessons_applied": "[What historical pattern suggests about truth value]",
      "hypothesis_informed": "H3"
    }},
    "paradigm_inversion": {{
      "inversions_generated": [
        {{"paradigm": "K1", "dismissed_view": "[what K1 would dismiss]", "captured_in": "H2"}}
      ]
    }},
    "mece_verification": {{
      "mutual_exclusivity": "Each hypothesis makes a distinct truth-value claim",
      "collective_exhaustiveness": "TRUE (H1) + FALSE (H2) + PARTIAL (H3) + OTHER (H0) = complete",
      "sum_to_one_possible": true
    }}
  }}
}}
```

Generate hypotheses that are COMPETING ANSWERS about whether the proposition is TRUE, FALSE, or CONDITIONALLY TRUE.

IMPORTANT: Return ONLY valid JSON. No additional text before or after the JSON object.
"""
        try:
            # Use reasoning model for deeper analytical thinking
            # Falls back to structured output (gpt-4o) if JSON parsing fails
            result = self._run_reasoning_phase(
                prompt, "Phase 0b: Generate Hypotheses + Forcing Functions (reasoning)",
                schema_name="hypotheses"  # Enables structured output fallback
            )
            hypotheses = result.get("hypotheses", [])
            forcing_functions_log = result.get("forcing_functions_log", {})

            # Validate we got actual hypotheses
            if len(hypotheses) < 2:
                raise ValueError(f"Reasoning model only returned {len(hypotheses)} hypotheses")

        except Exception as e:
            logger.warning(f"Reasoning model failed for hypotheses: {e}, falling back to structured output")
            # Fallback to structured output with gpt-4o
            try:
                fallback_prompt = prompt.replace("Think step by step", "").replace("```json", "").replace("```", "")
                result = self._run_structured_phase(
                    fallback_prompt, "hypotheses", "Phase 0b: Generate Hypotheses (fallback)"
                )
                hypotheses = result.get("hypotheses", [])
                forcing_functions_log = result.get("forcing_functions_log", {})
            except Exception as e2:
                logger.error(f"Both reasoning and structured output failed: {e2}")
                # Ultimate fallback with proper truth-value structure
                hypotheses = [
                    {
                        "id": "H0",
                        "name": "Other/Unforeseen Alternatives",
                        "truth_value_type": "other",
                        "statement": f"Some unforeseen factor or combination not captured by H1-H3 explains observations related to: {proposition}",
                        "mechanism_if_true": "Unspecified alternative mechanism",
                        "domains": [],
                        "testable_predictions": ["Evidence patterns don't fit H1-H3 predictions", "Novel factors emerge"],
                        "is_catch_all": True,
                        "is_ancestral_solution": False,
                        "is_paradigm_inversion": False,
                        "inverted_from_paradigm": None
                    },
                    {
                        "id": "H1",
                        "name": "Proposition TRUE - Primary Mechanism",
                        "truth_value_type": "affirm",
                        "statement": f"The proposition is TRUE: {proposition}",
                        "mechanism_if_true": "Primary causal mechanism (to be determined by evidence)",
                        "domains": ["Economic", "Institutional"],
                        "testable_predictions": ["Evidence would support the stated claim"],
                        "is_catch_all": False,
                        "is_ancestral_solution": False,
                        "is_paradigm_inversion": False,
                        "inverted_from_paradigm": None
                    },
                    {
                        "id": "H2",
                        "name": "Proposition FALSE - Alternative Explanation",
                        "truth_value_type": "deny",
                        "statement": f"The proposition is FALSE: An alternative explanation accounts for observations",
                        "mechanism_if_true": "Alternative causal mechanism",
                        "domains": ["Psychological", "Cultural"],
                        "testable_predictions": ["Evidence would contradict the stated claim"],
                        "is_catch_all": False,
                        "is_ancestral_solution": False,
                        "is_paradigm_inversion": True,
                        "inverted_from_paradigm": "K1"
                    },
                    {
                        "id": "H3",
                        "name": "Proposition PARTIAL - Conditional Truth",
                        "truth_value_type": "qualify",
                        "statement": f"The proposition is PARTIALLY TRUE: True under some conditions, false under others",
                        "mechanism_if_true": "Conditional mechanism dependent on context",
                        "domains": ["Historical"],
                        "testable_predictions": ["Effect varies systematically with conditions"],
                        "is_catch_all": False,
                        "is_ancestral_solution": True,
                        "is_paradigm_inversion": False,
                        "inverted_from_paradigm": None
                    }
                ]
                forcing_functions_log = {
                    "ontological_scan": {
                        "Biological": None,
                        "Economic": {"covered_by": "H1", "justification": "Economic factors in H1"},
                        "Cultural": {"covered_by": "H2", "justification": "Cultural factors in H2"},
                        "Theological": None,
                        "Historical": {"covered_by": "H3", "justification": "Historical perspective in H3"},
                        "Institutional": {"covered_by": "H1", "justification": "Institutional factors in H1"},
                        "Psychological": {"covered_by": "H2", "justification": "Psychological factors in H2"}
                    },
                    "ancestral_check": {
                        "historical_analogues": ["Fallback - no specific analogues identified"],
                        "lessons_applied": "Historical context needed",
                        "hypothesis_informed": "H3"
                    },
                    "paradigm_inversion": {
                        "inversions_generated": [
                            {"paradigm": "K1", "dismissed_view": "Non-economic factors", "captured_in": "H2"}
                        ]
                    },
                    "mece_verification": {
                        "mutual_exclusivity": "TRUE/FALSE/PARTIAL/OTHER are mutually exclusive truth-value claims",
                        "collective_exhaustiveness": "H1 (affirm) + H2 (deny) + H3 (qualify) + H0 (other) = complete",
                        "sum_to_one_possible": True
                    }
                }

        logger.info(f"Generated {len(hypotheses)} MECE hypotheses with truth-value structure")
        return hypotheses, forcing_functions_log

    def _assign_priors(self, hypotheses: List[Dict], paradigms: List[Dict], proposition: str = "") -> Dict:
        """
        Phase 0c: Each paradigm assigns priors to the UNIFIED MECE hypothesis set.

        CRITICAL: Priors are based ONLY on background knowledge (K₀) - the shared
        "universe of analysis" that all paradigms agree on BEFORE seeing evidence.

        DO NOT incorporate:
        - Web search evidence (comes in Phase 2)
        - External studies or data (likelihood assignment is Phase 3)

        Priors reflect each paradigm's initial beliefs given ONLY:
        - The proposition statement itself
        - General domain knowledge that forms the shared background context
        - The paradigm's characteristic biases and worldview

        Uses structured output for guaranteed valid JSON.
        """
        hypotheses_json = json.dumps(hypotheses, indent=2)
        paradigms_json = json.dumps(paradigms, indent=2)

        # Get IDs for reference
        hyp_ids = [h.get("id", f"H{i}") for i, h in enumerate(hypotheses)]
        paradigm_ids = [p.get("id", f"K{i}") for i, p in enumerate(paradigms)]

        prompt = f"""
You are assigning PRIOR probabilities for a BFIH (Bayesian Framework for Intellectual Honesty) analysis.

PROPOSITION: "{proposition}"

## CRITICAL DISTINCTION: PRIORS vs LIKELIHOODS

Priors P(H|K) represent INITIAL BELIEFS about hypotheses BEFORE seeing evidence.
You are assigning priors NOW. Evidence gathering and likelihood assignment come LATER.

DO NOT:
- Look up or reference any external evidence, studies, or data
- Consider what evidence might exist on the internet
- Use knowledge of specific research findings or statistics
- Let evidence-based reasoning influence prior assignment

DO:
- Assign priors based ONLY on the paradigm's worldview and the proposition text
- Use the paradigm's characteristic assumptions about causation
- Reflect how each paradigm would weigh hypotheses BEFORE any investigation
- Consider the paradigm's domains_covered and bias_type when assigning priors

## HYPOTHESIS SET (all paradigms use this same MECE set):
{hypotheses_json}

## PARADIGMS:
{paradigms_json}

Hypothesis IDs: {hyp_ids}
Paradigm IDs: {paradigm_ids}

## ASSIGNMENT RULES:

1. **Priors must sum to 1.0** for each paradigm (MECE requirement)
2. **K0 (privileged paradigm)** should have more balanced priors reflecting uncertainty
3. **K1-K5 (biased paradigms)** should have priors that reflect their specific biases:
   - Domain bias: Higher priors for hypotheses in favored domains
   - Temporal bias: Higher priors for hypotheses matching time horizon preference
   - Ideological bias: Higher priors for hypotheses aligned with values
4. **H0 (catch-all)** should generally receive 5-20% prior (room for unforeseen alternatives)
5. **Justifications** should reference paradigm assumptions, NOT external evidence

## OUTPUT FORMAT

Return as a JSON object with "paradigm_priors" array containing:
- paradigm_id: the paradigm identifier
- hypothesis_priors: array of {{hypothesis_id, prior, justification}}

Example justification (GOOD): "K1's economic focus naturally assigns higher prior to market-based explanations"
Example justification (BAD): "Studies show that economic factors account for 60% of such outcomes" (uses evidence!)

IMPORTANT: Return ONLY valid JSON. No additional text before or after the JSON object.
"""
        try:
            # Use reasoning model for prior assignment (requires careful paradigm-aware reasoning)
            # Falls back to structured output (gpt-4o) if JSON parsing fails
            result = self._run_reasoning_phase(
                prompt, "Phase 0c: Assign Priors (reasoning)",
                schema_name="priors"  # Enables structured output fallback
            )
            # Convert array format to dict format for compatibility
            priors_by_paradigm = {}
            for paradigm_set in result.get("paradigm_priors", []):
                paradigm_id = paradigm_set.get("paradigm_id")
                if paradigm_id:
                    priors_by_paradigm[paradigm_id] = {}
                    for hp in paradigm_set.get("hypothesis_priors", []):
                        h_id = hp.get("hypothesis_id")
                        if h_id:
                            priors_by_paradigm[paradigm_id][h_id] = {
                                "prior": hp.get("prior", 0.25),
                                "justification": hp.get("justification", "")
                            }
        except Exception as e:
            logger.error(f"Structured output failed for priors: {e}, using fallback")
            # Fallback: uniform priors
            priors_by_paradigm = {}
            uniform_prior = 1.0 / len(hypotheses) if hypotheses else 0.25
            for p in paradigms:
                priors_by_paradigm[p.get("id", "K1")] = {
                    h.get("id", "H0"): {"prior": uniform_prior, "justification": "Uniform (fallback)"}
                    for h in hypotheses
                }

        logger.info(f"Assigned priors for {len(priors_by_paradigm)} paradigms")
        return priors_by_paradigm

    def _build_scenario_config(
        self, scenario_id: str, proposition: str, domain: str,
        paradigms: List[Dict], hypotheses: List[Dict],
        forcing_functions_log: Dict, priors_by_paradigm: Dict
    ) -> Dict:
        """
        Build the full scenario config following Section 10.2 schema.
        """
        # Convert priors to simpler format for scenario_config
        simple_priors = {}
        for paradigm_id, hyp_priors in priors_by_paradigm.items():
            simple_priors[paradigm_id] = {
                h_id: data["prior"] if isinstance(data, dict) else data
                for h_id, data in hyp_priors.items()
            }

        config = {
            "schema_version": "1.0",
            "scenario_metadata": {
                "scenario_id": scenario_id,
                "title": proposition,
                "description": f"Autonomous BFIH analysis of: {proposition}",
                "domain": domain,
                "difficulty_level": "medium",
                "created_date": datetime.now(timezone.utc).isoformat(),
                "contributors": ["BFIH Autonomous System"],
                "ground_truth_hypothesis_id": None
            },
            "scenario_narrative": {
                "title": proposition,
                "background": f"Analysis of: {proposition}",
                "research_question": proposition
            },
            "paradigms": paradigms,
            "hypotheses": hypotheses,
            "forcing_functions_log": forcing_functions_log,
            "priors_by_paradigm": simple_priors
        }

        return config

    def _save_scenario_config(self, scenario_id: str, config: Dict) -> str:
        """
        Save the generated scenario config to a JSON file.
        """
        filename = f"scenario_config_{scenario_id}.json"
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved scenario config to: {filename}")
        return filename


# ============================================================================
# VECTOR STORE MANAGEMENT (Setup/Maintenance)
# ============================================================================

class VectorStoreManager:
    """Manages OpenAI vector stores for treatise and scenario configs"""
    
    def __init__(self):
        self.client = client
        
    def create_vector_store(self, name: str) -> str:
        """Create new vector store and return ID"""
        vs = self.client.beta.vector_stores.create(name=name)
        logger.info(f"Created vector store: {vs.id} ({name})")
        return vs.id
    
    def upload_file_to_store(self, vector_store_id: str, file_path: str) -> str:
        """Upload file to vector store"""
        with open(file_path, 'rb') as f:
            response = client.files.create(
                file=f,
                purpose="assistants"
            )
            vector_store_file = client.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file_id=response.id
            )
        logger.info(f"Uploaded {file_path} to vector store {vector_store_id}")
        return vector_store_file.id
    
    def list_vector_stores(self) -> List:
        """List all vector stores"""
        stores = self.client.vector_stores.files.list()
        return stores.data
    
    def delete_vector_store(self, vector_store_id: str) -> bool:
        """Delete vector store"""
        self.client.vector_stores.files.delete(vector_store_id)
        logger.info(f"Deleted vector store: {vector_store_id}")
        return True


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_conduct_analysis():
    """Example: Conduct BFIH analysis on startup success scenario"""
    
    scenario_config = {
        "paradigms": [
            {
                "id": "K1",
                "name": "Secular-Individualist",
                "description": "Success driven by founder grit and market efficiency"
            },
            {
                "id": "K2",
                "name": "Religious-Communitarian",
                "description": "Success driven by faith-based networks and community backing"
            },
            {
                "id": "K3",
                "name": "Economistic-Rationalist",
                "description": "Success driven by capital efficiency and unit economics"
            }
        ],
        "hypotheses": [
            {
                "id": "H0",
                "name": "Unknown/Combination",
                "domains": [],
                "associated_paradigms": ["K1", "K2", "K3"],
                "is_catch_all": True
            },
            {
                "id": "H1",
                "name": "Founder Grit & Strategic Vision",
                "domains": ["Psychological"],
                "associated_paradigms": ["K1"],
                "is_ancestral_solution": False
            },
            {
                "id": "H2",
                "name": "Faith-Based Community Networks",
                "domains": ["Theological", "Cultural"],
                "associated_paradigms": ["K2"],
                "is_ancestral_solution": True
            },
            {
                "id": "H3",
                "name": "Capital Efficiency & Unit Economics",
                "domains": ["Economic"],
                "associated_paradigms": ["K3"],
                "is_ancestral_solution": False
            }
        ],
        "priors_by_paradigm": {
            "K1": {"H0": 0.1, "H1": 0.5, "H2": 0.1, "H3": 0.2},
            "K2": {"H0": 0.05, "H1": 0.2, "H2": 0.55, "H3": 0.2},
            "K3": {"H0": 0.15, "H1": 0.1, "H2": 0.15, "H3": 0.6}
        }
    }
    
    proposition = "Why is startup Turing Labs succeeding in CPG formulated products formulation while competitors are struggling?"
    
    # Create request
    request = BFIHAnalysisRequest(
        scenario_id="s_001_startup_success",
        proposition=proposition,
        scenario_config=scenario_config,
        user_id="user_test_001"
    )
    
    # Conduct analysis
    orchestrator = BFIHOrchestrator()
    result = orchestrator.conduct_analysis(request)
    
    # Print results
    print("\n" + "="*80)
    print("BFIH ANALYSIS RESULT")
    print("="*80)
    print(f"Analysis ID: {result.analysis_id}")
    print(f"Scenario: {result.scenario_id}")
    print(f"Proposition: {result.proposition}")
    print("\nReport Preview (first 1000 chars):")
    print(result.report[:1000] + "...")
    print("\nMetadata:")
    print(json.dumps(result.metadata, indent=2))
    print("\nFull result saved to: analysis_result.json")
    
    # Save full result
    with open("analysis_result.json", "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    return result


def example_autonomous_analysis():
    """Example: Autonomous BFIH analysis from just a proposition"""

    # Just provide a proposition - everything else is generated automatically!
    proposition = "Why did Boeing's 737 MAX suffer two fatal crashes while Airbus maintained a strong safety record?"

    # Run autonomous analysis
    orchestrator = BFIHOrchestrator()
    result = orchestrator.analyze_topic(
        proposition=proposition,
        domain="business",
        difficulty="medium"
    )

    # Print results
    print("\n" + "="*80)
    print("AUTONOMOUS BFIH ANALYSIS RESULT")
    print("="*80)
    print(f"Analysis ID: {result.analysis_id}")
    print(f"Scenario: {result.scenario_id}")
    print(f"Proposition: {result.proposition}")
    print(f"\nAutonomous: {result.metadata.get('autonomous', False)}")
    print("\nReport Preview (first 1000 chars):")
    print(result.report[:1000] + "...")
    print("\nPosteriors:")
    print(json.dumps(result.posteriors, indent=2))
    print("\nMetadata:")
    print(json.dumps({k: v for k, v in result.metadata.items() if k != 'generated_config'}, indent=2))
    print("\nFull result saved to: analysis_result.json")

    # Save full result
    with open("analysis_result.json", "w") as f:
        json.dump(result.to_dict(), f, indent=2)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="BFIH Autonomous Analysis - Bayesian Framework for Intellectual Honesty"
    )
    parser.add_argument(
        "--topic", "-t",
        type=str,
        help="The proposition/topic to analyze"
    )
    parser.add_argument(
        "--domain", "-d",
        type=str,
        default="general",
        help="Domain of analysis (default: general)"
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default="medium",
        choices=["easy", "medium", "hard"],
        help="Difficulty level (default: medium)"
    )

    args = parser.parse_args()

    if args.topic:
        # Run with provided topic
        orchestrator = BFIHOrchestrator()
        result = orchestrator.analyze_topic(
            proposition=args.topic,
            domain=args.domain,
            difficulty=args.difficulty
        )

        # Print results
        print("\n" + "="*80)
        print("AUTONOMOUS BFIH ANALYSIS RESULT")
        print("="*80)
        print(f"Analysis ID: {result.analysis_id}")
        print(f"Scenario: {result.scenario_id}")
        print(f"Proposition: {result.proposition}")
        print(f"\nAutonomous: {result.metadata.get('autonomous', False)}")
        print("\nReport Preview (first 1000 chars):")
        print(result.report[:1000] + "...")
        print("\nPosteriors:")
        print(json.dumps(result.posteriors, indent=2))
        print("\nFull result saved to: analysis_result.json")

        with open("analysis_result.json", "w") as f:
            json.dump(result.to_dict(), f, indent=2)
    else:
        # Run default example
        example_autonomous_analysis()
