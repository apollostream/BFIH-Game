"""
BFIH Backend: Main Orchestrator Service
OpenAI Responses API Integration for AI-Assisted Hypothesis Tournament Game

This module coordinates:
1. Web search for evidence via OpenAI Responses API
2. File search for treatise/scenarios via vector stores
3. Python code execution for Bayesian calculations
4. BFIH report generation and storage
"""

import json
import os
import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import uuid
from dataclasses import dataclass, asdict

from openai import OpenAI
from dotenv import load_dotenv


# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TREATISE_VECTOR_STORE_ID = os.getenv("TREATISE_VECTOR_STORE_ID")
MODEL = "gpt-4o"

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = OpenAI(api_key=OPENAI_API_KEY)


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

            # Phase 5: Generate final report
            bfih_report = self._run_phase_5_report(
                request, methodology, evidence_text, likelihoods_text, computation
            )

            # Extract posteriors from computation output (Phase 4)
            posteriors = self._extract_posteriors_from_report(computation, request.scenario_config)

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
                created_at=analysis_end.isoformat()
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
    
    def _extract_posteriors_from_report(self, report: str, scenario_config: Dict) -> Dict:
        """
        Extract posterior probabilities from the generated report.
        Returns dict of {paradigm_id: {hypothesis_id: posterior_value}}

        Uses regex to parse the BFIH POSTERIOR COMPUTATION section.
        Applies same posteriors to all paradigms (flexible extraction).
        """
        # Parse posteriors from the report text
        extracted = self._parse_posterior_section(report)

        if not extracted:
            logger.warning("No posteriors extracted from report, using defaults")

        # Build result structure: same posteriors for all paradigms
        posteriors = {}
        paradigms = scenario_config.get("paradigms", [])

        # If no paradigms defined, create a default one
        if not paradigms:
            paradigms = [{"id": "default"}]

        for paradigm in paradigms:
            paradigm_id = paradigm.get("id")
            posteriors[paradigm_id] = {}

            # Use extracted posteriors directly (flexible extraction)
            for hypothesis_id, value in extracted.items():
                posteriors[paradigm_id][hypothesis_id] = value

        return posteriors

    def _run_phase(self, prompt: str, tools: List[Dict], phase_name: str) -> str:
        """
        Run a single phase with streaming output.
        Returns the output text from the phase.
        """
        logger.info(f"Starting {phase_name}")
        print(f"\n{'='*60}\n{phase_name}\n{'='*60}")

        response = None
        stream = self.client.responses.create(
            model=self.model,
            input=prompt,
            max_output_tokens=8000,
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
        """Phase 2: Gather evidence via web search. Returns (markdown_text, structured_evidence)"""
        scenario_json = json.dumps(request.scenario_config, indent=2)
        prompt = f"""
You are gathering evidence for a BFIH analysis.

PROPOSITION: "{request.proposition}"

SCENARIO CONFIGURATION:
{scenario_json}

METHODOLOGY CONTEXT:
{methodology[:4000]}

YOUR TASK:
For EACH hypothesis in the scenario, search for real-world evidence:
1. Generate 2-3 specific web search queries per hypothesis
2. Execute web searches to find supporting or refuting evidence
3. Organize evidence by hypothesis
4. Record FULL source citations with URLs for all evidence

After your evidence summary, output a structured JSON block with ALL evidence items.
Use this EXACT format with the markers:

EVIDENCE_JSON_START
[
  {{
    "evidence_id": "E1",
    "description": "Brief description of the evidence",
    "source_name": "Publication or website name",
    "source_url": "https://full.url/to/source",
    "citation_apa": "Author/Publication. (Year). Title. URL",
    "date_accessed": "2026-01-06",
    "supports_hypotheses": ["H1"],
    "refutes_hypotheses": [],
    "evidence_type": "quantitative|qualitative|expert_testimony|historical_analogy"
  }},
  {{
    "evidence_id": "E2",
    ...
  }}
]
EVIDENCE_JSON_END

Include 15-25 evidence items total across all hypotheses.
"""
        tools = [{"type": "web_search", "search_context_size": "medium"}]
        result = self._run_phase(prompt, tools, "Phase 2: Evidence Gathering")

        # Parse structured evidence from response
        evidence_items = self._parse_evidence_json(result)

        return result, evidence_items

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
        """Phase 3: Assign likelihoods to evidence. Returns (markdown_text, structured_clusters)"""
        scenario_json = json.dumps(request.scenario_config, indent=2)

        # Get hypothesis IDs for the prompt
        hypotheses = request.scenario_config.get("hypotheses", [])
        hyp_ids = [h.get("id", f"H{i}") for i, h in enumerate(hypotheses)]

        prompt = f"""
You are assigning likelihoods for a BFIH Bayesian analysis.

PROPOSITION: "{request.proposition}"

SCENARIO CONFIGURATION:
{scenario_json}

EVIDENCE GATHERED:
{evidence_text[:6000]}

YOUR TASK:
1. Group evidence items into 3-5 CLUSTERS based on thematic similarity
2. For each cluster, assign likelihoods P(E|H) for EACH hypothesis
3. Justify each likelihood assignment (0.0 to 1.0)
4. Ensure clusters are conditionally independent given any hypothesis

After your analysis, output a structured JSON block with ALL clusters and likelihoods.
Use this EXACT format with markers:

CLUSTERS_JSON_START
[
  {{
    "cluster_id": "C1",
    "cluster_name": "Short descriptive name",
    "description": "What evidence items are in this cluster",
    "evidence_ids": ["E1", "E2", "E3"],
    "conditional_independence_justification": "Why these are conditionally independent",
    "likelihoods": {{
      "H0": {{"probability": 0.3, "justification": "..."}},
      "H1": {{"probability": 0.8, "justification": "..."}},
      "H2": {{"probability": 0.4, "justification": "..."}}
    }}
  }},
  {{
    "cluster_id": "C2",
    ...
  }}
]
CLUSTERS_JSON_END

Hypotheses to include: {hyp_ids}
Create 3-5 clusters covering all evidence.
"""
        tools = []  # No tools needed, pure reasoning
        result = self._run_phase(prompt, tools, "Phase 3: Likelihood Assignment")

        # Parse structured clusters from response
        clusters = self._parse_clusters_json(result)

        return result, clusters

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
                           likelihoods: str, computation: str) -> str:
        """Phase 5: Generate final BFIH report"""
        scenario_json = json.dumps(request.scenario_config, indent=2)
        prompt = f"""
You are generating the final BFIH analysis report.

PROPOSITION: "{request.proposition}"

SCENARIO CONFIGURATION:
{scenario_json}

=== PHASE 1 METHODOLOGY ===
{methodology[:2000]}

=== PHASE 2 EVIDENCE ===
{evidence[:3000]}

=== PHASE 3 LIKELIHOODS ===
{likelihoods[:3000]}

=== PHASE 4 COMPUTATION ===
{computation}

YOUR TASK:
Generate a comprehensive markdown report with these sections:

1. **Executive Summary** (2-3 paragraphs)
   - Primary finding with verdict (VALIDATED/PARTIALLY VALIDATED/REJECTED/INDETERMINATE)
   - Key posterior probabilities from Phase 4
   - Paradigm dependence summary

2. **Scenario & Objectives**

3. **Background Knowledge (K₀) Analysis**
   - Paradigms and their assumptions

4. **Forcing Functions Application**
   - Ontological Scan results
   - Ancestral Check
   - Paradigm Inversion

5. **Hypothesis Set Documentation**
   - Table with all hypotheses

6. **Evidence Matrix & Likelihood Analysis**
   - Evidence clusters from Phase 3
   - Likelihood tables

7. **Bayesian Update Trace**
   - Final posteriors from Phase 4 computation
   - Copy the exact posterior values

8. **Paradigm-Dependence Analysis**

9. **Sensitivity Analysis Results**

10. **Intellectual Honesty Assessment**

Use decimal probabilities (e.g., 0.425). Include all posterior values from Phase 4.
"""
        tools = []  # No tools needed
        return self._run_phase(prompt, tools, "Phase 5: Report Generation")

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

        # Phase 0c: Assign priors per paradigm
        priors_by_paradigm = self._assign_priors(hypotheses, paradigms)

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
        Phase 0a: Generate 2-4 paradigms relevant to the proposition.
        """
        prompt = f"""
You are generating paradigms for a BFIH (Bayesian Framework for Intellectual Honesty) analysis.

PROPOSITION: "{proposition}"
DOMAIN: {domain}

Generate 2-4 paradigms that represent fundamentally different worldviews for analyzing this question.
Include at least one inverse pair (e.g., Secular-Individualist ↔ Religious-Communitarian).

For each paradigm provide:
- id: K1, K2, K3, etc.
- name: Short descriptive name (e.g., "Secular-Individualist")
- description: Epistemic stance - what this paradigm treats as valid evidence and causal mechanisms
- inverse_paradigm_id: ID of the inverse paradigm if applicable, or null
- characteristics: Object with:
  - prefers_evidence_types: List of evidence types this paradigm values
  - skeptical_of: List of factors this paradigm discounts
  - causal_preference: Primary causal mechanism this paradigm favors

Output ONLY valid JSON array, no markdown:
[
  {{
    "id": "K1",
    "name": "...",
    "description": "...",
    "inverse_paradigm_id": "K2",
    "characteristics": {{
      "prefers_evidence_types": ["..."],
      "skeptical_of": ["..."],
      "causal_preference": "..."
    }}
  }}
]
"""
        result = self._run_phase(prompt, [], "Phase 0a: Generate Paradigms")

        # Parse JSON from response
        try:
            # Find JSON array in response
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                paradigms = json.loads(json_match.group(0))
            else:
                raise ValueError("No JSON array found in response")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse paradigms: {e}")
            # Fallback to default paradigms
            paradigms = [
                {"id": "K1", "name": "Secular-Rationalist", "description": "Material and measurable factors",
                 "inverse_paradigm_id": "K2", "characteristics": {}},
                {"id": "K2", "name": "Religious-Communitarian", "description": "Faith, community, transcendent values",
                 "inverse_paradigm_id": "K1", "characteristics": {}},
                {"id": "K3", "name": "Economistic-Rationalist", "description": "Capital efficiency and incentives",
                 "inverse_paradigm_id": None, "characteristics": {}}
            ]

        logger.info(f"Generated {len(paradigms)} paradigms: {[p['name'] for p in paradigms]}")
        return paradigms

    def _generate_hypotheses_with_forcing_functions(
        self, proposition: str, paradigms: List[Dict], difficulty: str
    ) -> Tuple[List[Dict], Dict]:
        """
        Phase 0b: Generate hypotheses with forcing functions and MECE synthesis.

        Executes:
        - Initial hypothesis generation per paradigm
        - Ontological Scan (7 domains)
        - Ancestral Check (historical solutions)
        - Paradigm Inversion (inverse hypotheses)
        - MECE Synthesis (consolidate into unified set)
        """
        num_hypotheses = {"easy": 4, "medium": 6, "hard": 8}.get(difficulty, 6)
        paradigm_json = json.dumps(paradigms, indent=2)

        prompt = f"""
You are generating hypotheses for a BFIH analysis with FORCING FUNCTIONS.

PROPOSITION: "{proposition}"

PARADIGMS:
{paradigm_json}

TARGET: Generate {num_hypotheses} hypotheses (including H0 catch-all)

Execute these FORCING FUNCTIONS in order:

## FORCING FUNCTION 1: ONTOLOGICAL SCAN
Verify coverage of these 7 domains. For each, either include a hypothesis OR justify exclusion:
- Biological (genetic, neurological, health factors)
- Economic (capital, incentives, resources)
- Cultural/Social (norms, networks, community)
- Theological (faith, transcendence, religious institutions)
- Historical (precedent, tradition, time-tested mechanisms)
- Institutional (regulations, organizations, governance)
- Psychological (individual motivation, cognition, personality)

## FORCING FUNCTION 2: ANCESTRAL CHECK
Identify how similar problems were solved historically.
Include at least one hypothesis reflecting a time-tested mechanism.

## FORCING FUNCTION 3: PARADIGM INVERSION
For each paradigm, generate at least one hypothesis from its INVERSE paradigm's perspective.

## FORCING FUNCTION 4: MECE SYNTHESIS
After generating hypotheses from all paradigms:
1. Collect ALL hypotheses
2. Identify overlaps and consolidate
3. Ensure MUTUAL EXCLUSIVITY: no two hypotheses can both be true
4. Ensure COLLECTIVE EXHAUSTIVENESS: hypotheses cover all plausible explanations
5. Include H0 as catch-all for unknown/combination factors
6. Restate each hypothesis with clear, unambiguous boundaries

Output ONLY valid JSON with this structure:
{{
  "hypotheses": [
    {{
      "id": "H0",
      "name": "Unknown/Combination",
      "narrative": "Multiple factors combined in ways not identified",
      "domains": [],
      "associated_paradigms": ["K1", "K2", "K3"],
      "is_ancestral_solution": false,
      "is_catch_all": true
    }},
    {{
      "id": "H1",
      "name": "...",
      "narrative": "...",
      "domains": ["Economic", "Psychological"],
      "associated_paradigms": ["K1"],
      "is_ancestral_solution": false,
      "is_catch_all": false
    }}
  ],
  "forcing_functions_log": {{
    "ontological_scan": {{
      "Biological": {{"hypothesis_id": null, "justification": "..."}},
      "Economic": {{"hypothesis_id": "H1", "justification": "..."}},
      "Cultural": {{"hypothesis_id": "H2", "justification": "..."}},
      "Theological": {{"hypothesis_id": "H3", "justification": "..."}},
      "Historical": {{"hypothesis_id": "H3", "justification": "..."}},
      "Institutional": {{"hypothesis_id": "H4", "justification": "..."}},
      "Psychological": {{"hypothesis_id": "H1", "justification": "..."}}
    }},
    "ancestral_check": {{
      "historical_analogue": "...",
      "primary_mechanism": "...",
      "hypothesis_id": "H3",
      "justification": "..."
    }},
    "paradigm_inversion": [
      {{
        "primary_paradigm": "K1",
        "inverse_paradigm": "K2",
        "generated_hypothesis_id": "H3",
        "quality_assessment": "..."
      }}
    ],
    "mece_synthesis": {{
      "total_candidates": 8,
      "consolidated_to": {num_hypotheses},
      "overlaps_resolved": ["..."],
      "validation": "All hypotheses are mutually exclusive and collectively exhaustive"
    }}
  }}
}}
"""
        # Use file_search to get forcing function methodology from treatise
        tools = [{"type": "file_search", "vector_store_ids": [self.vector_store_id]}]
        result = self._run_phase(prompt, tools, "Phase 0b: Generate Hypotheses + Forcing Functions")

        # Parse JSON from response
        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                hypotheses = data.get("hypotheses", [])
                forcing_functions_log = data.get("forcing_functions_log", {})
            else:
                raise ValueError("No JSON object found in response")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse hypotheses: {e}")
            # Fallback
            hypotheses = [
                {"id": "H0", "name": "Unknown/Combination", "narrative": "Unknown factors",
                 "domains": [], "associated_paradigms": ["K1", "K2", "K3"],
                 "is_ancestral_solution": False, "is_catch_all": True}
            ]
            forcing_functions_log = {}

        logger.info(f"Generated {len(hypotheses)} MECE hypotheses")
        return hypotheses, forcing_functions_log

    def _assign_priors(self, hypotheses: List[Dict], paradigms: List[Dict]) -> Dict:
        """
        Phase 0c: Each paradigm assigns priors to the UNIFIED MECE hypothesis set.
        """
        hypotheses_json = json.dumps(hypotheses, indent=2)
        paradigms_json = json.dumps(paradigms, indent=2)

        prompt = f"""
You are assigning prior probabilities for a BFIH analysis.

UNIFIED MECE HYPOTHESIS SET (all paradigms must use this same set):
{hypotheses_json}

PARADIGMS:
{paradigms_json}

For EACH paradigm, assign prior probabilities P(H|K) to EACH hypothesis.

RULES:
1. Priors must sum to 1.0 for each paradigm
2. Different paradigms should weight the SAME hypotheses differently
3. A secular paradigm should assign LOW prior to theological hypotheses
4. A religious paradigm should assign HIGH prior to faith-based hypotheses
5. Provide brief justification for non-trivial priors

Output ONLY valid JSON with this structure:
{{
  "K1": {{
    "H0": {{"prior": 0.10, "justification": "Catch-all kept low"}},
    "H1": {{"prior": 0.40, "justification": "..."}},
    "H2": {{"prior": 0.30, "justification": "..."}},
    "H3": {{"prior": 0.10, "justification": "..."}},
    "H4": {{"prior": 0.10, "justification": "..."}}
  }},
  "K2": {{
    "H0": {{"prior": 0.05, "justification": "..."}},
    ...
  }}
}}
"""
        result = self._run_phase(prompt, [], "Phase 0c: Assign Priors")

        # Parse JSON from response
        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                priors_by_paradigm = json.loads(json_match.group(0))
            else:
                raise ValueError("No JSON object found in response")
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse priors: {e}")
            # Fallback: uniform priors
            priors_by_paradigm = {}
            uniform_prior = 1.0 / len(hypotheses)
            for p in paradigms:
                priors_by_paradigm[p["id"]] = {
                    h["id"]: {"prior": uniform_prior, "justification": "Uniform (fallback)"}
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
    # Run autonomous analysis (generates everything from just the proposition)
    example_autonomous_analysis()
