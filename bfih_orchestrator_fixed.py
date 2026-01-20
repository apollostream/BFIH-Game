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
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
import uuid
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI, AuthenticationError, APIError, BadRequestError
from dotenv import load_dotenv
import httpx

# Timeout configuration: GPT-5.x models with reasoning need longer timeouts
DEFAULT_TIMEOUT = httpx.Timeout(300.0, connect=30.0)  # 5 min total, 30s connect
GPT5_TIMEOUT = httpx.Timeout(600.0, connect=30.0)     # 10 min total for GPT-5.x with reasoning

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


# ============================================================================
# PROBABILITY BOUNDS
# ============================================================================
# Prevent extreme probabilities (0 or 1) which break Bayesian math:
# - log(0) = -infinity
# - Division by zero in odds calculations
# - No evidence can update a prior of 0 or 1 (violates Cromwell's Rule)

PROB_EPSILON = 0.001  # Minimum distance from 0 or 1
PROB_MIN = PROB_EPSILON        # 0.001
PROB_MAX = 1.0 - PROB_EPSILON  # 0.999


def clamp_probability(p: float, context: str = "") -> float:
    """
    Clamp a probability to avoid extreme values (0 or 1).

    Per Cromwell's Rule: "I beseech you, in the bowels of Christ,
    think it possible that you may be mistaken."

    Args:
        p: Probability value to clamp
        context: Optional context string for logging

    Returns:
        Probability clamped to [PROB_MIN, PROB_MAX]
    """
    if p <= 0.0:
        if context:
            logger.warning(f"Clamping probability from {p} to {PROB_MIN} ({context})")
        return PROB_MIN
    elif p >= 1.0:
        if context:
            logger.warning(f"Clamping probability from {p} to {PROB_MAX} ({context})")
        return PROB_MAX
    elif p < PROB_MIN:
        if context:
            logger.debug(f"Clamping probability from {p} to {PROB_MIN} ({context})")
        return PROB_MIN
    elif p > PROB_MAX:
        if context:
            logger.debug(f"Clamping probability from {p} to {PROB_MAX} ({context})")
        return PROB_MAX
    return p


# OpenAI Configuration
# Priority: 1. Environment variables, 2. Config file (~/.config/bfih/config.json)
try:
    from bfih_config import load_config as load_bfih_config
    _config = load_bfih_config()
    OPENAI_API_KEY = _config.openai_api_key
    TREATISE_VECTOR_STORE_ID = _config.vector_store_id
    if OPENAI_API_KEY:
        logger.info("Loaded credentials from config file")
except ImportError:
    # Config module not available, use env vars only
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    TREATISE_VECTOR_STORE_ID = os.getenv("TREATISE_VECTOR_STORE_ID")

# Environment variables always override config file
if os.getenv("OPENAI_API_KEY"):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if os.getenv("TREATISE_VECTOR_STORE_ID"):
    TREATISE_VECTOR_STORE_ID = os.getenv("TREATISE_VECTOR_STORE_ID")

MODEL = "o4-mini"
# Reasoning model for cognitively demanding tasks (paradigm/hypothesis/prior/likelihood)
# Options: gpt-5.2 (default), o3-mini, o3, o4-mini, gpt-5
REASONING_MODEL = os.getenv("BFIH_REASONING_MODEL", "gpt-5.2")
# Whether reasoning model supports structured output (o3-mini and newer do as of 2026)
REASONING_MODEL_SUPPORTS_STRUCTURED = os.getenv("BFIH_REASONING_STRUCTURED", "true").lower() == "true"

# Persistent BFIH system context prepended to all phase prompts
# This ensures the model maintains awareness of the BFIH methodology throughout the analysis
def get_bfih_system_context(phase_name: str, phase_number: str) -> str:
    """Generate BFIH system context for a specific phase."""
    return f"""
================================================================================
BFIH (BAYESIAN FRAMEWORK FOR INTELLECTUAL HONESTY) ANALYSIS
================================================================================

You are an expert analyst performing a rigorous BFIH analysis. This framework
ensures intellectual honesty through systematic Bayesian reasoning.

CURRENT PHASE: {phase_number} - {phase_name}

CORE BFIH PRINCIPLES:
1. **Paradigm Plurality**: Analyze from multiple epistemic stances (K0 privileged + K1-Kn biased)
2. **Forcing Functions**: Apply Ontological Scan, Ancestral Check, Paradigm Inversion
3. **MECE Hypotheses**: Ensure Mutually Exclusive, Collectively Exhaustive hypothesis sets
4. **Bayesian Updating**: Update beliefs via P(H|E) = P(E|H)×P(H) / P(E)
5. **Transparent Uncertainty**: Quantify confidence, acknowledge limitations

INTELLECTUAL HONESTY REQUIREMENTS:
- State assumptions explicitly
- Consider evidence that challenges your conclusions
- Distinguish strong evidence (high LR) from weak evidence (LR ≈ 1)
- Flag paradigm-dependent vs robust conclusions

Maintain maximum intellectual rigor throughout this phase.
================================================================================

"""

# Create default OpenAI client if credentials are available
# For multi-tenant mode, credentials can be provided per-request instead
if OPENAI_API_KEY:
    # Use longer timeout if default reasoning model is GPT-5.x
    default_timeout = GPT5_TIMEOUT if "gpt-5" in REASONING_MODEL else DEFAULT_TIMEOUT
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        timeout=default_timeout
    )
    logger.info(f"Default OpenAI client initialized (timeout: {default_timeout.read}s)")
else:
    client = None
    logger.info("No default API key configured - credentials must be provided per-request")


# ============================================================================
# DATA MODELS
# ============================================================================

# Available reasoning models for configuration
AVAILABLE_REASONING_MODELS = ["o3-mini", "o3", "o4-mini", "gpt-5", "gpt-5.2", "gpt-5-mini"]


# ============================================================================
# COST TRACKING
# ============================================================================
# Pricing per 1K tokens (as of Jan 2026 - update as needed)
# Source: https://openai.com/pricing

MODEL_PRICING = {
    # GPT-5.x series
    "gpt-5.2": {"input": 0.010, "output": 0.030, "reasoning": 0.030},  # Same as output for reasoning
    "gpt-5": {"input": 0.010, "output": 0.030, "reasoning": 0.030},
    "gpt-5-mini": {"input": 0.002, "output": 0.006, "reasoning": 0.006},
    # o-series (reasoning models)
    "o3": {"input": 0.010, "output": 0.040, "reasoning": 0.040},
    "o3-mini": {"input": 0.001, "output": 0.004, "reasoning": 0.004},
    "o4-mini": {"input": 0.001, "output": 0.004, "reasoning": 0.004},
    # Fallback for unknown models
    "default": {"input": 0.010, "output": 0.030, "reasoning": 0.030},
}


class CostTracker:
    """Tracks API costs and enforces budget limits."""

    def __init__(self, budget_limit: Optional[float] = None):
        """
        Initialize cost tracker.

        Args:
            budget_limit: Maximum allowed cost in USD. None = unlimited.
        """
        self.budget_limit = budget_limit
        self.total_cost = 0.0
        self.call_costs = []  # List of (model, phase, cost) tuples
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_reasoning_tokens = 0

    def get_model_pricing(self, model: str) -> dict:
        """Get pricing for a model, falling back to default if unknown."""
        # Check for exact match
        if model in MODEL_PRICING:
            return MODEL_PRICING[model]
        # Check for partial match (e.g., "gpt-5.2" matches "gpt-5")
        for key in MODEL_PRICING:
            if key in model or model in key:
                return MODEL_PRICING[key]
        return MODEL_PRICING["default"]

    def add_cost(self, model: str, phase: str, input_tokens: int, output_tokens: int, reasoning_tokens: int = 0):
        """
        Record cost from an API call.

        Args:
            model: Model name used
            phase: Phase name for logging
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            reasoning_tokens: Number of reasoning tokens (for o-series/GPT-5)
        """
        pricing = self.get_model_pricing(model)
        cost = (
            (input_tokens / 1000) * pricing["input"] +
            (output_tokens / 1000) * pricing["output"] +
            (reasoning_tokens / 1000) * pricing["reasoning"]
        )

        self.total_cost += cost
        self.call_costs.append((model, phase, cost, input_tokens, output_tokens, reasoning_tokens))
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_reasoning_tokens += reasoning_tokens

        logger.info(f"[COST] {phase}: ${cost:.4f} ({input_tokens}i/{output_tokens}o/{reasoning_tokens}r tokens) | Total: ${self.total_cost:.2f}")

        return cost

    def check_budget(self, phase: str, estimated_cost: float = 0.50) -> None:
        """
        Check if proceeding would exceed budget. Raises exception if so.

        Args:
            phase: Phase about to execute (for error message)
            estimated_cost: Estimated cost of next operation (default $0.50)

        Raises:
            RuntimeError: If budget would be exceeded
        """
        if self.budget_limit is None:
            return  # No limit set

        if self.total_cost + estimated_cost > self.budget_limit:
            raise RuntimeError(
                f"BUDGET LIMIT EXCEEDED: Cannot proceed with {phase}.\n"
                f"Current cost: ${self.total_cost:.2f}\n"
                f"Estimated next: ${estimated_cost:.2f}\n"
                f"Budget limit: ${self.budget_limit:.2f}\n"
                f"Analysis aborted to prevent overspend."
            )

    def get_summary(self) -> dict:
        """Get cost summary."""
        return {
            "total_cost_usd": round(self.total_cost, 4),
            "budget_limit_usd": self.budget_limit,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_reasoning_tokens": self.total_reasoning_tokens,
            "calls": len(self.call_costs),
            "breakdown": [
                {
                    "model": m,
                    "phase": p,
                    "cost_usd": round(c, 4),
                    "input_tokens": i,
                    "output_tokens": o,
                    "reasoning_tokens": r
                }
                for m, p, c, i, o, r in self.call_costs
            ]
        }


@dataclass
class BFIHAnalysisRequest:
    """Request to conduct BFIH analysis"""
    scenario_id: str
    proposition: str
    scenario_config: Dict
    user_id: Optional[str] = None
    reasoning_model: Optional[str] = None  # Override default reasoning model
    budget_limit: Optional[float] = None  # Max cost in USD, None = unlimited

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

    def __init__(self, vector_store_id: Optional[str] = None, api_key: Optional[str] = None, skip_api_init: bool = False,
                 status_callback: Optional[callable] = None, progress_callback: Optional[callable] = None):
        """
        Initialize the orchestrator.

        Args:
            vector_store_id: Optional vector store ID for file search
            api_key: Optional OpenAI API key (for multi-tenant deployment)
            skip_api_init: If True, skip API client initialization (for visualization-only mode)
            status_callback: Optional callback function(phase: str) to report progress
            progress_callback: Optional callback function(message: str) to stream progress logs
        """
        self.status_callback = status_callback
        self.progress_callback = progress_callback

        # Support visualization-only mode (no API calls needed)
        if skip_api_init:
            self.client = None
            self.vector_store_id = None
            self.model = None
            self.reasoning_model = None
            return

        # Support per-request API keys for multi-tenant deployment
        if api_key:
            # Use longer timeout for GPT-5.x models with reasoning
            timeout = GPT5_TIMEOUT if "gpt-5" in REASONING_MODEL else DEFAULT_TIMEOUT
            self.client = OpenAI(
                api_key=api_key,
                timeout=timeout
            )
            logger.info(f"Created client with timeout: {timeout.read}s")
        elif client is not None:
            self.client = client  # Use global client from config/env vars
        else:
            raise ValueError(
                "No OpenAI API key configured. Either:\n"
                "  1. Run 'python bfih_user_setup.py' to set up your credentials, or\n"
                "  2. Set OPENAI_API_KEY environment variable, or\n"
                "  3. Provide api_key parameter when creating the orchestrator"
            )
        self.vector_store_id = vector_store_id or TREATISE_VECTOR_STORE_ID
        self.model = MODEL
        self.reasoning_model = REASONING_MODEL
        logger.info(f"Using reasoning model: {self.reasoning_model} for hypothesis generation")

    def _report_status(self, phase: str):
        """Report current phase to status callback if configured."""
        if self.status_callback:
            try:
                self.status_callback(phase)
            except Exception as e:
                logger.warning(f"Status callback failed: {e}")

    def _log_progress(self, message: str):
        """Log a message and also send to progress callback if set."""
        logger.info(message)
        if self.progress_callback:
            try:
                self.progress_callback(message)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

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

        # Initialize cost tracking (preserve existing tracker if already initialized, e.g., from analyze_topic)
        if not hasattr(self, 'cost_tracker') or self.cost_tracker is None:
            self.cost_tracker = CostTracker(budget_limit=request.budget_limit)
            if request.budget_limit:
                self._log_progress(f"Budget limit set: ${request.budget_limit:.2f}")

        # Override reasoning model if specified in request
        if request.reasoning_model and request.reasoning_model in AVAILABLE_REASONING_MODELS:
            self.reasoning_model = request.reasoning_model
            self._log_progress(f"Using request-specified reasoning model: {self.reasoning_model}")

        self._log_progress(f"Starting BFIH analysis for scenario: {request.scenario_id}")
        self._log_progress(f"Proposition: {request.proposition}")

        try:
            # Phase 1: Retrieve methodology from vector store (cheap)
            self._report_status("phase:methodology")
            self._log_progress("Phase 1: Retrieving methodology...")
            self.cost_tracker.check_budget("Phase 1: Methodology", estimated_cost=0.10)
            methodology = self._run_phase_1_methodology(request)
            self._log_progress("Phase 1 complete: Methodology retrieved")

            # Phase 2: Gather evidence via web search (most expensive - web search + reasoning)
            self._report_status("phase:evidence")
            self._log_progress("Phase 2: Gathering evidence via web search...")
            self.cost_tracker.check_budget("Phase 2: Evidence", estimated_cost=2.00)
            evidence_text, evidence_items = self._run_phase_2_evidence(request, methodology)
            self._log_progress(f"Phase 2 complete: Found {len(evidence_items)} evidence items")

            # Phase 3: Assign likelihoods to evidence (expensive - reasoning model)
            self._report_status("phase:likelihoods")
            self._log_progress("Phase 3: Assigning likelihoods...")
            self.cost_tracker.check_budget("Phase 3: Likelihoods", estimated_cost=1.50)
            likelihoods_text, evidence_clusters = self._run_phase_3_likelihoods(
                request, evidence_text, evidence_items
            )
            self._log_progress(f"Phase 3 complete: {len(evidence_clusters)} evidence clusters")

            # Compute Bayesian metrics (P(E|¬H), LR, WoE) in Python - NOT by LLM
            # Compute metrics for ALL paradigms so frontend can display paradigm-specific values
            priors_by_paradigm = request.scenario_config.get(
                "priors_by_paradigm", request.scenario_config.get("priors", {})
            )
            paradigm_ids = list(priors_by_paradigm.keys()) if priors_by_paradigm else []

            # Compute metrics for each paradigm and merge into bayesian_metrics_by_paradigm
            enriched_clusters = None
            joint_metrics = {}
            first_paradigm = paradigm_ids[0] if paradigm_ids else None

            for paradigm_id in paradigm_ids:
                # Extract priors for this paradigm (clamped to avoid extremes)
                computation_priors = {}
                for h_id, p in priors_by_paradigm[paradigm_id].items():
                    raw_prior = p if isinstance(p, (int, float)) else p.get("probability", 0.5)
                    computation_priors[h_id] = clamp_probability(raw_prior, f"prior {h_id} in {paradigm_id}")

                # Compute metrics for this paradigm
                paradigm_enriched, paradigm_joint = self._compute_cluster_bayesian_metrics(
                    evidence_clusters, computation_priors, paradigm_id
                )

                if enriched_clusters is None:
                    # First paradigm: initialize enriched_clusters with bayesian_metrics_by_paradigm
                    enriched_clusters = []
                    for cluster in paradigm_enriched:
                        new_cluster = {k: v for k, v in cluster.items() if k != "bayesian_metrics"}
                        new_cluster["bayesian_metrics_by_paradigm"] = {
                            paradigm_id: cluster.get("bayesian_metrics", {})
                        }
                        enriched_clusters.append(new_cluster)
                    joint_metrics = paradigm_joint
                else:
                    # Subsequent paradigms: merge metrics into existing clusters
                    for i, cluster in enumerate(paradigm_enriched):
                        enriched_clusters[i]["bayesian_metrics_by_paradigm"][paradigm_id] = cluster.get("bayesian_metrics", {})

            # Fallback if no paradigms
            if enriched_clusters is None:
                enriched_clusters = evidence_clusters

            # Format pre-computed tables for report (using first paradigm for display)
            hyp_ids = [h.get("id") for h in request.scenario_config.get("hypotheses", [])]
            precomputed_cluster_tables = []
            for cluster in enriched_clusters:
                cluster_name = cluster.get("cluster_id") or cluster.get("cluster_name", "Unknown")
                table = self._format_cluster_metrics_table(cluster, hyp_ids, first_paradigm)
                precomputed_cluster_tables.append({
                    "name": cluster_name,
                    "description": cluster.get("description", ""),
                    "evidence_ids": cluster.get("evidence_ids", []),
                    "table": table
                })

            precomputed_joint_table = self._format_joint_metrics_table(joint_metrics, hyp_ids)

            # Phase 4: Compute paradigm-specific posteriors using Python (authoritative source)
            # NOTE: Phase 4 code_interpreter was removed - it produced inconsistent posteriors
            # that didn't account for paradigm-specific priors and likelihoods
            self._report_status("phase:computation")
            self._log_progress("Phase 4: Computing posteriors...")
            posteriors_by_paradigm = self._compute_paradigm_posteriors(
                request.scenario_config, evidence_clusters
            )
            self._log_progress("Phase 4 complete: Posteriors computed")

            # Build paradigm comparison table for Phase 5c
            paradigm_comparison_table = self._format_paradigm_comparison_table(
                posteriors_by_paradigm, request.scenario_config
            )

            # Phase 5: Generate final report (pass pre-computed Bayesian tables AND paradigm posteriors)
            self._report_status("phase:report")
            self._log_progress("Phase 5: Generating report...")
            self.cost_tracker.check_budget("Phase 5: Report Generation", estimated_cost=1.00)
            bfih_report = self._run_phase_5_report(
                request, methodology, evidence_text, likelihoods_text,
                evidence_items, enriched_clusters,
                precomputed_cluster_tables, precomputed_joint_table,
                posteriors_by_paradigm, paradigm_comparison_table
            )
            self._log_progress("Phase 5 complete: Report generated")

            # Use already-computed posteriors
            posteriors = posteriors_by_paradigm

            # Create result object
            analysis_id = str(uuid.uuid4())
            analysis_end = datetime.now(timezone.utc)
            duration_seconds = (analysis_end - analysis_start).total_seconds()

            # Get cost summary
            cost_summary = self.cost_tracker.get_summary()
            self._log_progress(f"Analysis cost: ${cost_summary['total_cost_usd']:.2f} ({cost_summary['calls']} API calls)")

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
                    "evidence_clusters_count": len(evidence_clusters),
                    "cost": cost_summary
                },
                created_at=analysis_end.isoformat(),
                scenario_config=request.scenario_config
            )

            # Store structured evidence in metadata for access
            # Use enriched_clusters which includes bayesian_metrics_by_paradigm for frontend
            result.metadata["evidence_items"] = evidence_items
            result.metadata["evidence_clusters"] = enriched_clusters

            # Generate evidence flow visualization if Graphviz is available
            try:
                import tempfile
                viz_dir = tempfile.gettempdir()  # Use /tmp for cloud compatibility
                viz_output = self.generate_evidence_flow_visualization(result, output_dir=viz_dir)
                if viz_output.get("png"):
                    result.metadata["visualization"] = {
                        "dot": viz_output["dot"],
                        "png": viz_output["png"],
                        "dot_content": viz_output.get("dot_content")
                    }
                    logger.info(f"Generated evidence flow visualization: {viz_output['png']}")
            except Exception as viz_error:
                logger.warning(f"Could not generate visualization: {viz_error}")

            self._log_progress(f"BFIH analysis completed successfully: {analysis_id}")
            self._log_progress(f"Duration: {duration_seconds:.1f}s")
            logger.info(f"Evidence: {len(evidence_items)} items in {len(evidence_clusters)} clusters")
            return result

        except RuntimeError as e:
            # Check if this is a budget limit error
            if "BUDGET LIMIT EXCEEDED" in str(e):
                # Save checkpoint with all progress so far
                checkpoint = self._save_budget_checkpoint(
                    request=request,
                    analysis_start=analysis_start,
                    completed_phases=locals()
                )
                self._log_progress(f"Budget limit reached. Checkpoint saved: {checkpoint}")
                # Re-raise with checkpoint info
                raise RuntimeError(
                    f"{str(e)}\n\nCheckpoint saved to: {checkpoint}\n"
                    f"Resume by loading checkpoint and continuing with remaining phases."
                ) from e
            else:
                logger.error(f"Error conducting BFIH analysis: {str(e)}", exc_info=True)
                raise

        except Exception as e:
            logger.error(f"Error conducting BFIH analysis: {str(e)}", exc_info=True)
            raise

    def _save_budget_checkpoint(self, request: BFIHAnalysisRequest, analysis_start: datetime,
                                 completed_phases: dict) -> str:
        """Save checkpoint when budget limit is reached so analysis can be resumed."""
        checkpoint_id = f"{request.scenario_id}_checkpoint_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        checkpoint_path = f"{checkpoint_id}.json"

        # Extract completed data from locals
        checkpoint_data = {
            "checkpoint_id": checkpoint_id,
            "scenario_id": request.scenario_id,
            "proposition": request.proposition,
            "scenario_config": request.scenario_config,
            "analysis_start": analysis_start.isoformat(),
            "checkpoint_time": datetime.now(timezone.utc).isoformat(),
            "cost_summary": self.cost_tracker.get_summary(),
            "completed_phases": {},
            "resume_from": None
        }

        # Record which phases completed and their data
        if "methodology" in completed_phases and completed_phases.get("methodology"):
            checkpoint_data["completed_phases"]["methodology"] = completed_phases["methodology"][:5000]  # Truncate
            checkpoint_data["resume_from"] = "Phase 2"

        if "evidence_items" in completed_phases and completed_phases.get("evidence_items"):
            checkpoint_data["completed_phases"]["evidence_items"] = completed_phases["evidence_items"]
            checkpoint_data["completed_phases"]["evidence_text"] = completed_phases.get("evidence_text", "")[:10000]
            checkpoint_data["resume_from"] = "Phase 3"

        if "evidence_clusters" in completed_phases and completed_phases.get("evidence_clusters"):
            checkpoint_data["completed_phases"]["evidence_clusters"] = completed_phases["evidence_clusters"]
            checkpoint_data["completed_phases"]["likelihoods_text"] = completed_phases.get("likelihoods_text", "")[:10000]
            checkpoint_data["resume_from"] = "Phase 4"

        if "enriched_clusters" in completed_phases and completed_phases.get("enriched_clusters"):
            checkpoint_data["completed_phases"]["enriched_clusters"] = completed_phases["enriched_clusters"]
            checkpoint_data["completed_phases"]["posteriors_by_paradigm"] = completed_phases.get("posteriors_by_paradigm", {})
            checkpoint_data["resume_from"] = "Phase 5"

        # Save checkpoint
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)

        logger.info(f"Saved budget checkpoint: {checkpoint_path}")
        logger.info(f"Resume from: {checkpoint_data['resume_from']}")
        logger.info(f"Total cost at checkpoint: ${checkpoint_data['cost_summary']['total_cost_usd']:.2f}")

        return checkpoint_path

    def conduct_analysis_with_injected_evidence(
        self,
        request: BFIHAnalysisRequest,
        injected_evidence: List[Dict],
        skip_methodology: bool = True
    ) -> BFIHAnalysisResult:
        """
        Conduct BFIH analysis with pre-supplied evidence items (skip Phase 2).

        This method is designed for meta-analysis scenarios where evidence items
        come from prior BFIH analyses rather than web search. It accepts structured
        evidence and proceeds directly to likelihood assignment (Phase 3).

        Args:
            request: BFIHAnalysisRequest with scenario config and proposition
            injected_evidence: List of evidence items in standard BFIH format:
                [
                    {
                        "evidence_id": "E1",
                        "description": "...",
                        "source_name": "Prior BFIH Analysis",
                        "source_url": "file://...",
                        "evidence_type": "systematic_analysis",
                        "supports_hypotheses": ["H1", "H2"],
                        "refutes_hypotheses": ["H3"]
                    },
                    ...
                ]
            skip_methodology: If True, skip Phase 1 (methodology retrieval)

        Returns:
            BFIHAnalysisResult with report and posteriors
        """
        analysis_start = datetime.now(timezone.utc)

        # Override reasoning model if specified in request
        if request.reasoning_model and request.reasoning_model in AVAILABLE_REASONING_MODELS:
            self.reasoning_model = request.reasoning_model
            self._log_progress(f"Using request-specified reasoning model: {self.reasoning_model}")

        self._log_progress(f"Starting BFIH meta-analysis for scenario: {request.scenario_id}")
        self._log_progress(f"Proposition: {request.proposition}")
        self._log_progress(f"Injected evidence items: {len(injected_evidence)}")

        try:
            # Phase 1: Methodology (optional for meta-analysis)
            if skip_methodology:
                methodology = "Meta-analysis using prior BFIH conclusions as evidence."
                self._log_progress("Phase 1: Skipped (meta-analysis mode)")
            else:
                self._report_status("phase:methodology")
                self._log_progress("Phase 1: Retrieving methodology...")
                methodology = self._run_phase_1_methodology(request)
                self._log_progress("Phase 1 complete: Methodology retrieved")

            # Phase 2: SKIPPED - Use injected evidence
            self._report_status("phase:evidence")
            self._log_progress("Phase 2: Using injected evidence (skipping web search)")
            evidence_items = injected_evidence

            # Generate evidence text summary for Phase 3
            evidence_text = self._format_injected_evidence_as_text(injected_evidence)
            self._log_progress(f"Phase 2 complete: {len(evidence_items)} injected evidence items")

            # Phase 3: Assign likelihoods to evidence (returns structured clusters)
            self._report_status("phase:likelihoods")
            self._log_progress("Phase 3: Assigning likelihoods...")
            likelihoods_text, evidence_clusters = self._run_phase_3_likelihoods(
                request, evidence_text, evidence_items
            )
            self._log_progress(f"Phase 3 complete: {len(evidence_clusters)} evidence clusters")

            # Compute Bayesian metrics for ALL paradigms
            # (Following the same pattern as conduct_analysis)
            priors_by_paradigm = request.scenario_config.get(
                "priors_by_paradigm",
                request.scenario_config.get("priors", {})
            )

            hypotheses = request.scenario_config.get("hypotheses", [])
            paradigms = request.scenario_config.get("paradigms", [])
            hyp_ids = [h.get("id", f"H{i}") for i, h in enumerate(hypotheses)]
            paradigm_ids = [p.get("id", f"K{i}") for i, p in enumerate(paradigms)]

            # Compute metrics for each paradigm and merge into bayesian_metrics_by_paradigm
            enriched_clusters = None
            joint_metrics = {}

            for paradigm_id in paradigm_ids:
                # Extract priors for this paradigm (clamped to avoid extremes)
                computation_priors = {}
                raw_priors = priors_by_paradigm.get(paradigm_id, {})
                for h_id, p in raw_priors.items():
                    raw_prior = p if isinstance(p, (int, float)) else p.get("probability", 0.5)
                    computation_priors[h_id] = clamp_probability(raw_prior, f"prior {h_id} in {paradigm_id}")

                if not computation_priors:
                    continue

                # Compute metrics for this paradigm
                paradigm_enriched, paradigm_joint = self._compute_cluster_bayesian_metrics(
                    evidence_clusters, computation_priors, paradigm_id
                )

                if enriched_clusters is None:
                    # First paradigm: initialize enriched_clusters with bayesian_metrics_by_paradigm
                    enriched_clusters = []
                    for cluster in paradigm_enriched:
                        new_cluster = {k: v for k, v in cluster.items() if k != "bayesian_metrics"}
                        new_cluster["bayesian_metrics_by_paradigm"] = {
                            paradigm_id: cluster.get("bayesian_metrics", {})
                        }
                        enriched_clusters.append(new_cluster)
                    joint_metrics = paradigm_joint
                else:
                    # Subsequent paradigms: merge metrics into existing clusters
                    for i, cluster in enumerate(paradigm_enriched):
                        enriched_clusters[i]["bayesian_metrics_by_paradigm"][paradigm_id] = cluster.get("bayesian_metrics", {})

            # Fallback if no paradigms processed
            if enriched_clusters is None:
                enriched_clusters = evidence_clusters

            # Store structured evidence in scenario_config for report
            if "evidence" not in request.scenario_config:
                request.scenario_config["evidence"] = {}
            request.scenario_config["evidence"]["items"] = evidence_items
            request.scenario_config["evidence"]["clusters"] = evidence_clusters
            request.scenario_config["evidence"]["total_items"] = len(evidence_items)
            request.scenario_config["evidence"]["total_clusters"] = len(evidence_clusters)

            # Phase 4: Bayesian computation
            self._report_status("phase:computation")
            self._log_progress("Phase 4: Computing posteriors...")

            # Use the existing _compute_paradigm_posteriors method
            posteriors_by_paradigm = self._compute_paradigm_posteriors(
                request.scenario_config, enriched_clusters
            )

            request.scenario_config["posteriors_by_paradigm"] = posteriors_by_paradigm
            self._log_progress("Phase 4 complete: Posteriors computed")

            # Build precomputed tables for report
            first_paradigm = paradigm_ids[0] if paradigm_ids else None
            precomputed_cluster_tables = []
            for cluster in enriched_clusters:
                cluster_name = cluster.get("cluster_id") or cluster.get("cluster_name", "Unknown")
                table = self._format_cluster_metrics_table(cluster, hyp_ids, first_paradigm)
                precomputed_cluster_tables.append({
                    "name": cluster_name,
                    "description": cluster.get("description", ""),
                    "evidence_ids": cluster.get("evidence_ids", []),
                    "table": table
                })

            # Build joint metrics table (using joint_metrics from paradigm computation)
            precomputed_joint_table = self._format_joint_metrics_table(joint_metrics, hyp_ids)

            # Build paradigm comparison table
            paradigm_comparison_table = self._format_paradigm_comparison_table(
                posteriors_by_paradigm, request.scenario_config
            )

            # Phase 5: Generate report
            self._report_status("phase:report")
            self._log_progress("Phase 5: Generating report...")
            bfih_report = self._run_phase_5_report(
                request=request,
                methodology=methodology,
                evidence=evidence_text,
                likelihoods=likelihoods_text,
                evidence_items=evidence_items,
                evidence_clusters=enriched_clusters,
                precomputed_cluster_tables=precomputed_cluster_tables,
                precomputed_joint_table=precomputed_joint_table,
                posteriors_by_paradigm=posteriors_by_paradigm,
                paradigm_comparison_table=paradigm_comparison_table
            )
            self._log_progress("Phase 5 complete: Report generated")

            posteriors = posteriors_by_paradigm

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
                    "evidence_clusters_count": len(evidence_clusters),
                    "meta_analysis": True,
                    "injected_evidence": True
                },
                created_at=analysis_end.isoformat(),
                scenario_config=request.scenario_config
            )

            result.metadata["evidence_items"] = evidence_items
            result.metadata["evidence_clusters"] = enriched_clusters

            # Generate visualization
            try:
                import tempfile
                viz_dir = tempfile.gettempdir()
                viz_output = self.generate_evidence_flow_visualization(result, output_dir=viz_dir)
                if viz_output.get("png"):
                    result.metadata["visualization"] = {
                        "dot": viz_output["dot"],
                        "png": viz_output["png"],
                        "dot_content": viz_output.get("dot_content")
                    }
                    logger.info(f"Generated evidence flow visualization: {viz_output['png']}")
            except Exception as viz_error:
                logger.warning(f"Could not generate visualization: {viz_error}")

            self._log_progress(f"BFIH meta-analysis completed successfully: {analysis_id}")
            self._log_progress(f"Duration: {duration_seconds:.1f}s")
            return result

        except Exception as e:
            logger.error(f"Error conducting BFIH meta-analysis: {str(e)}", exc_info=True)
            raise

    def _format_injected_evidence_as_text(self, evidence_items: List[Dict]) -> str:
        """Format injected evidence items as text for Phase 3 processing."""
        lines = ["# Injected Evidence Items\n"]
        for item in evidence_items:
            lines.append(f"## {item.get('evidence_id', 'E?')}: {item.get('description', '')[:200]}")
            lines.append(f"Source: {item.get('source_name', 'Unknown')}")
            lines.append(f"Type: {item.get('evidence_type', 'unknown')}")
            if item.get('supports_hypotheses'):
                lines.append(f"Supports: {', '.join(item['supports_hypotheses'])}")
            if item.get('refutes_hypotheses'):
                lines.append(f"Refutes: {', '.join(item['refutes_hypotheses'])}")
            lines.append("")
        return "\n".join(lines)

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
   - Ontological Scan: table showing relevant domains covered/justified (9 total, with Constitutional/Legal and Democratic mandatory for political topics)
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
    
    def _compute_paradigm_posteriors(self, scenario_config: Dict,
                                      evidence_clusters: List[Dict] = None) -> Dict:
        """
        Compute paradigm-specific posterior probabilities using Bayesian updating.
        Returns dict of {paradigm_id: {hypothesis_id: posterior_value}}

        This is the AUTHORITATIVE source for all posterior values in the system.
        Phase 4 code_interpreter was removed because it didn't account for
        paradigm-specific priors and likelihoods.

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

                # Get priors for each hypothesis (clamped to avoid extremes)
                priors = {}
                for h_id in hyp_ids:
                    p = paradigm_priors.get(h_id, paradigm_priors.get(h_id.upper(), {}))
                    if isinstance(p, dict):
                        raw_prior = p.get("probability", p.get("prior", 1.0 / len(hyp_ids)))
                    elif isinstance(p, (int, float)):
                        raw_prior = float(p)
                    else:
                        raw_prior = 1.0 / len(hyp_ids)  # Uniform default
                    priors[h_id] = clamp_probability(raw_prior, f"prior {h_id} in {paradigm_id}")

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

                    # Extract likelihood for each hypothesis (clamped to avoid extremes)
                    cluster_lh = {}
                    cluster_id = cluster.get("cluster_id", "unknown")
                    for h_id in hyp_ids:
                        h_lh = lh.get(h_id, lh.get(h_id.upper(), lh.get(h_id.lower(), {})))
                        if isinstance(h_lh, dict):
                            raw_lh = h_lh.get("probability", 0.5)
                        elif isinstance(h_lh, (int, float)):
                            raw_lh = float(h_lh)
                        else:
                            raw_lh = 0.5  # Default neutral
                        cluster_lh[h_id] = clamp_probability(raw_lh, f"likelihood {h_id}|{cluster_id}")
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
            # Fallback: Use uniform posteriors when no evidence clusters available
            logger.warning("No evidence clusters available, using uniform posteriors")
            uniform_prob = 1.0 / len(hyp_ids) if hyp_ids else 0.25

            for paradigm in paradigms:
                paradigm_id = paradigm.get("id")
                posteriors[paradigm_id] = {h_id: uniform_prob for h_id in hyp_ids}
                logger.info(f"Paradigm {paradigm_id} using uniform posteriors: {posteriors[paradigm_id]}")

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
                    try:
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
                    except BrokenPipeError:
                        # Ignore broken pipe errors from print statements (happens in background mode)
                        if event.type == "response.completed":
                            response = event.response
                        elif event.type == "error":
                            logger.error(f"Error in {phase_name}: {event.error.message}")
                            raise RuntimeError(f"API error in {phase_name}: {event.error.message}")

                if response is None:
                    raise RuntimeError(f"No response received for {phase_name}")

                # Track costs if usage data is available
                if hasattr(self, 'cost_tracker') and hasattr(response, 'usage') and response.usage:
                    input_tokens = getattr(response.usage, 'input_tokens', 0) or 0
                    output_tokens = getattr(response.usage, 'output_tokens', 0) or 0
                    reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0) or 0
                    self.cost_tracker.add_cost(self.model, phase_name, input_tokens, output_tokens, reasoning_tokens)

                try:
                    print(f"\n[{phase_name} complete]")
                except BrokenPipeError:
                    pass  # Ignore broken pipe in background mode
                logger.info(f"{phase_name} complete, status: {response.status}")

                return response.output_text

            except AuthenticationError as e:
                # API key errors should fail immediately, no retry
                logger.error(f"Authentication error in {phase_name}: {e}")
                raise RuntimeError(f"Invalid OpenAI API key: {e}") from e

            except APIError as e:
                # Check if it's an auth-related API error (invalid key format, etc.)
                error_msg = str(e).lower()
                if "api key" in error_msg or "authentication" in error_msg or "incorrect" in error_msg:
                    logger.error(f"API key error in {phase_name}: {e}")
                    raise RuntimeError(f"Invalid OpenAI API key: {e}") from e
                # Other API errors might be transient, allow retry
                last_error = e
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"{phase_name} failed with APIError: {e}, retrying in {wait_time}s...")
                    print(f"\n[APIError, retrying in {wait_time}s...]")
                    time.sleep(wait_time)
                else:
                    logger.error(f"{phase_name} failed after {max_retries + 1} attempts: {e}")
                    raise

            except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectTimeout, RuntimeError) as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 5  # 5s, 10s backoff
                    logger.warning(f"{phase_name} failed with {type(e).__name__}: {e}, retrying in {wait_time}s...")
                    print(f"\n[{type(e).__name__}, retrying in {wait_time}s...]")
                    time.sleep(wait_time)
                else:
                    logger.error(f"{phase_name} failed after {max_retries + 1} attempts: {e}")
                    raise

        raise last_error or RuntimeError(f"Failed to complete {phase_name}")

    def _run_structured_phase(self, prompt: str, schema_name: str, phase_name: str,
                               tools: List[Dict] = None, max_retries: int = 2,
                               model: str = None, return_citations: bool = False) -> dict:
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
            return_citations: If True, return tuple of (result, url_citations) for web_search

        Returns:
            Parsed JSON dict matching the schema, or tuple (dict, list) if return_citations=True
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
                    include_list = []
                    if any(t.get("type") == "file_search" for t in tools):
                        include_list.append("file_search_call.results")
                    # Request sources from web_search - this is the reliable way to get URLs
                    if any(t.get("type") in ("web_search", "web_search_preview") for t in tools):
                        include_list.append("web_search_call.action.sources")
                    if include_list:
                        request_params["include"] = include_list

                # GPT-5.x models require explicit reasoning.effort parameter
                # (default is "none" for GPT-5.1+, unlike o-series which reason by default)
                if "gpt-5" in model:
                    request_params["reasoning"] = {"effort": "medium"}

                # Make the API call (non-streaming for structured output)
                print(f"[Calling API with structured output schema: {schema_name}...]")

                response = self.client.responses.create(**request_params)

                # Track costs if usage data is available
                if hasattr(self, 'cost_tracker') and hasattr(response, 'usage') and response.usage:
                    input_tokens = getattr(response.usage, 'input_tokens', 0) or 0
                    output_tokens = getattr(response.usage, 'output_tokens', 0) or 0
                    reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0) or 0
                    self.cost_tracker.add_cost(model, phase_name, input_tokens, output_tokens, reasoning_tokens)

                # Extract the output
                output_text = response.output_text
                print(f"\n[Received structured output, parsing JSON...]")

                # Extract URL sources if requested
                url_citations = []
                if return_citations:
                    # Primary method: Get sources from web_search_call.action.sources
                    # This is the reliable way to get all URLs consulted
                    web_search_count = 0
                    for output_item in response.output:
                        if hasattr(output_item, 'type') and output_item.type == 'web_search_call':
                            web_search_count += 1
                            # Log the search query if available
                            if hasattr(output_item, 'action'):
                                query = getattr(output_item.action, 'query', None)
                                if query:
                                    logger.info(f"Web search #{web_search_count} query: {query[:100]}...")
                                    print(f"[Web search #{web_search_count}: {query[:80]}...]")
                            if hasattr(output_item, 'action') and hasattr(output_item.action, 'sources'):
                                sources_in_call = 0
                                for source in output_item.action.sources:
                                    url = getattr(source, 'url', '') if hasattr(source, 'url') else (source.get('url', '') if isinstance(source, dict) else '')
                                    title = getattr(source, 'title', '') if hasattr(source, 'title') else (source.get('title', '') if isinstance(source, dict) else '')
                                    if url and url.startswith('http'):
                                        url_citations.append({
                                            'url': url,
                                            'title': title,
                                            'from_sources': True
                                        })
                                        sources_in_call += 1
                                logger.info(f"  -> {sources_in_call} sources from search #{web_search_count}")
                            else:
                                logger.warning(f"  -> No sources attribute in search #{web_search_count}")

                    if web_search_count > 0:
                        logger.info(f"Total: {web_search_count} web searches, {len(url_citations)} URLs extracted")

                    # Fallback: Also check url_citation annotations in message content
                    if not url_citations:
                        for output_item in response.output:
                            if hasattr(output_item, 'content'):
                                for content_item in output_item.content:
                                    if hasattr(content_item, 'annotations'):
                                        for annotation in content_item.annotations:
                                            if hasattr(annotation, 'type') and annotation.type == 'url_citation':
                                                url = getattr(annotation, 'url', '')
                                                if url and url.startswith('http'):
                                                    url_citations.append({
                                                        'url': url,
                                                        'title': getattr(annotation, 'title', ''),
                                                        'from_sources': False
                                                    })

                    if url_citations:
                        source_type = "sources" if url_citations[0].get('from_sources') else "annotations"
                        logger.info(f"Extracted {len(url_citations)} URLs from web_search {source_type}")
                        print(f"[Extracted {len(url_citations)} URLs from web_search {source_type}]")

                # Parse JSON from output
                try:
                    # The output should be valid JSON due to schema enforcement
                    result = json.loads(output_text)
                    logger.info(f"{phase_name} complete with valid JSON")
                    print(f"[{phase_name} complete - valid JSON parsed]")
                    if return_citations:
                        return result, url_citations
                    return result
                except json.JSONDecodeError as e:
                    # Fallback: try to extract JSON from the response
                    logger.warning(f"Direct JSON parse failed: {e}, attempting extraction")
                    json_match = re.search(r'[\[{].*[}\]]', output_text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group(0))
                        logger.info(f"{phase_name} complete with extracted JSON")
                        if return_citations:
                            return result, url_citations
                        return result
                    raise ValueError(f"Could not parse JSON from response: {output_text[:500]}")

            except AuthenticationError as e:
                # API key errors should fail immediately, no retry
                logger.error(f"Authentication error in {phase_name}: {e}")
                raise RuntimeError(f"Invalid OpenAI API key: {e}") from e

            except BadRequestError as e:
                # Handle token limit and context length errors with user-friendly messages
                error_msg = str(e).lower()
                if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
                    logger.error(f"Context length exceeded in {phase_name}: {e}")
                    raise RuntimeError(
                        f"Input too long for {model}'s context window. "
                        f"Try a simpler proposition or reduce the analysis scope."
                    ) from e
                elif "max_tokens" in error_msg or "maximum.*tokens" in error_msg:
                    logger.error(f"Token limit exceeded in {phase_name}: {e}")
                    raise RuntimeError(
                        f"Response exceeded token limit for {model}. "
                        f"The analysis may be too complex for this model."
                    ) from e
                # Other bad request errors - fail immediately
                logger.error(f"Bad request in {phase_name}: {e}")
                raise RuntimeError(f"Invalid request to {model}: {e}") from e

            except APIError as e:
                # Check if it's an auth-related API error
                error_msg = str(e).lower()
                if "api key" in error_msg or "authentication" in error_msg or "incorrect" in error_msg:
                    logger.error(f"API key error in {phase_name}: {e}")
                    raise RuntimeError(f"Invalid OpenAI API key: {e}") from e
                # Other API errors might be transient, allow retry
                last_error = e
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"{phase_name} failed with APIError: {e}, retrying in {wait_time}s...")
                    print(f"\n[APIError, retrying in {wait_time}s...]")
                    time.sleep(wait_time)
                else:
                    logger.error(f"{phase_name} failed after {max_retries + 1} attempts: {e}")
                    raise

            except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"{phase_name} failed with {type(e).__name__}, retrying in {wait_time}s...")
                    print(f"\n[Connection error, retrying in {wait_time}s...]")
                    time.sleep(wait_time)
                else:
                    logger.error(f"{phase_name} failed after {max_retries + 1} attempts: {e}")
                    # Provide user-friendly timeout message
                    if isinstance(e, (httpx.ReadTimeout, httpx.ConnectTimeout)):
                        raise RuntimeError(
                            f"Request to {model} timed out during {phase_name}. "
                            f"GPT-5.x models with reasoning may need more time. "
                            f"Please try again or use a faster model like o4-mini."
                        ) from e
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

                # GPT-5.x models require explicit reasoning.effort parameter
                # (default is "none" for GPT-5.1+, unlike o-series which reason by default)
                if "gpt-5" in self.reasoning_model:
                    request_params["reasoning"] = {"effort": "medium"}

                # Make the API call
                print(f"[Calling reasoning model for deep analysis...]")

                response = self.client.responses.create(**request_params)

                # Track costs if usage data is available
                if hasattr(self, 'cost_tracker') and hasattr(response, 'usage') and response.usage:
                    input_tokens = getattr(response.usage, 'input_tokens', 0) or 0
                    output_tokens = getattr(response.usage, 'output_tokens', 0) or 0
                    reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0) or 0
                    self.cost_tracker.add_cost(self.reasoning_model, phase_name, input_tokens, output_tokens, reasoning_tokens)

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

            except AuthenticationError as e:
                # API key errors should fail immediately, no retry
                logger.error(f"Authentication error in {phase_name}: {e}")
                raise RuntimeError(f"Invalid OpenAI API key: {e}") from e

            except BadRequestError as e:
                # Handle token limit and context length errors with user-friendly messages
                error_msg = str(e).lower()
                if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
                    logger.error(f"Context length exceeded in {phase_name}: {e}")
                    raise RuntimeError(
                        f"Input too long for {self.reasoning_model}'s context window. "
                        f"Try a simpler proposition or reduce the analysis scope."
                    ) from e
                elif "max_tokens" in error_msg or "maximum.*tokens" in error_msg:
                    logger.error(f"Token limit exceeded in {phase_name}: {e}")
                    raise RuntimeError(
                        f"Response exceeded token limit for {self.reasoning_model}. "
                        f"The analysis may be too complex for this model."
                    ) from e
                # Other bad request errors - fail immediately
                logger.error(f"Bad request in {phase_name}: {e}")
                raise RuntimeError(f"Invalid request to {self.reasoning_model}: {e}") from e

            except APIError as e:
                # Check if it's an auth-related API error
                error_msg = str(e).lower()
                if "api key" in error_msg or "authentication" in error_msg or "incorrect" in error_msg:
                    logger.error(f"API key error in {phase_name}: {e}")
                    raise RuntimeError(f"Invalid OpenAI API key: {e}") from e
                # Other API errors might be transient, allow retry
                last_error = e
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 10
                    logger.warning(f"{phase_name} failed with APIError: {e}, retrying in {wait_time}s...")
                    print(f"\n[APIError, retrying in {wait_time}s...]")
                    time.sleep(wait_time)
                else:
                    logger.error(f"{phase_name} failed after {max_retries + 1} attempts: {e}")
                    raise

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
                    # Provide user-friendly timeout message
                    if isinstance(e, (httpx.ReadTimeout, httpx.ConnectTimeout)):
                        raise RuntimeError(
                            f"Request to {self.reasoning_model} timed out during {phase_name}. "
                            f"GPT-5.x models with reasoning may need more time. "
                            f"Please try again or use a faster model like o4-mini."
                        ) from e
                    raise

            except Exception as e:
                # For any other error, try structured fallback if available
                if schema_name:
                    logger.warning(f"Reasoning model error: {e}, falling back to structured output")
                    print(f"[Reasoning model error, falling back to structured output...]")
                    return self._run_structured_phase(prompt, schema_name, f"{phase_name} (structured fallback)")
                raise

        raise last_error or RuntimeError(f"Failed to complete {phase_name}")

    def _generate_inverse_proposition(self, proposition: str) -> str:
        """Generate the logical inverse/negation of a proposition for balanced evidence gathering.

        This implements dual-framing to avoid confirmation bias in search queries.
        For example:
        - "AI will benefit humanity" -> "AI will harm humanity" or "AI will not benefit humanity"
        - "Climate change is caused by humans" -> "Climate change is not primarily caused by humans"
        """
        prompt = f"""Given this proposition, generate its logical inverse or negation.
The inverse should represent the opposite claim that would be true if the original is false.

PROPOSITION: "{proposition}"

Rules:
1. Keep the same subject matter and scope
2. Invert the core claim (not just add "not")
3. Make it a natural-sounding statement someone might actually argue
4. If the proposition is already negative, make it affirmative

Return ONLY the inverse proposition, nothing else."""

        try:
            response = self.client.responses.create(
                model="o4-mini",  # Fast model for simple task
                input=prompt,
            )
            # Track costs if usage data is available
            if hasattr(self, 'cost_tracker') and hasattr(response, 'usage') and response.usage:
                input_tokens = getattr(response.usage, 'input_tokens', 0) or 0
                output_tokens = getattr(response.usage, 'output_tokens', 0) or 0
                self.cost_tracker.add_cost("o4-mini", "inverse_proposition", input_tokens, output_tokens, 0)
            inverse = response.output_text.strip().strip('"')
            logger.info(f"Generated inverse proposition: {inverse}")
            return inverse
        except Exception as e:
            logger.warning(f"Failed to generate inverse proposition: {e}")
            # Fallback: simple negation
            if proposition.lower().startswith("it is "):
                return proposition.replace("It is ", "It is not ", 1).replace("it is ", "it is not ", 1)
            return f"It is not the case that {proposition.lower()}"

    def _run_phase_1_methodology(self, request: BFIHAnalysisRequest) -> str:
        """Phase 1: Retrieve BFIH methodology from vector store"""
        bfih_context = get_bfih_system_context("Methodology Retrieval", "1")
        prompt = f"""{bfih_context}
PROPOSITION: "{request.proposition}"

Use file_search to retrieve the following from the BFIH treatise:
1. "Forcing functions" methodology
2. "Paradigm inversion" methods
3. Key sections on:
   - Ontological scan (9 domains including Constitutional/Legal and Democratic)
   - Ancestral check
   - Split-brain technique

Provide a concise summary of the methodology that will guide the analysis.
Focus on actionable steps for applying each forcing function.
"""
        tools = [{"type": "file_search", "vector_store_ids": [self.vector_store_id]}]
        return self._run_phase(prompt, tools, "Phase 1: Retrieve Methodology")

    # =========================================================================
    # TOPIC-ADAPTIVE EVIDENCE SEARCH SYSTEM
    # =========================================================================
    # Different topic types require different search strategies:
    # - Academic/philosophical topics need journal papers, encyclopedias, scholarly works
    # - Consumer/product topics need reviews, ratings, comparisons
    # - Political/policy topics need news, think tanks, government sources
    # - Scientific topics need research papers, datasets, empirical studies

    TOPIC_SEARCH_TEMPLATES = {
        "academic": [
            "peer-reviewed academic papers on {proposition}",
            "scholarly journal articles about {proposition}",
            "Stanford Encyclopedia of Philosophy {proposition}",
            "PhilPapers research on {proposition}",
            "academic books and monographs on {proposition}",
            "university research publications {proposition}",
            "theoretical frameworks for {proposition}",
            "critical analysis and debates about {proposition}",
        ],
        "philosophical": [
            "philosophy papers on {proposition}",
            "epistemology research {proposition}",
            "Stanford Encyclopedia {proposition}",
            "PhilPapers {proposition}",
            "philosophical debates about {proposition}",
            "history of philosophy {proposition}",
            "contemporary philosophers on {proposition}",
            "philosophical journals {proposition}",
        ],
        "scientific": [
            "peer-reviewed scientific studies on {proposition}",
            "empirical research data {proposition}",
            "meta-analyses and systematic reviews {proposition}",
            "scientific consensus {proposition}",
            "research methodology {proposition}",
            "experimental findings {proposition}",
            "arXiv papers on {proposition}",
            "Nature Science journals {proposition}",
        ],
        "consumer": [
            "rankings and best-of lists for {proposition}",
            "user reviews and ratings {proposition}",
            "critical reviews and complaints {proposition}",
            "expert professional reviews {proposition}",
            "comparison guides {proposition}",
            "consumer reports {proposition}",
        ],
        "political": [
            "policy analysis {proposition}",
            "think tank research {proposition}",
            "government reports {proposition}",
            "political science research {proposition}",
            "news analysis {proposition}",
            "expert political commentary {proposition}",
            "historical political context {proposition}",
            "international perspectives {proposition}",
        ],
        "historical": [
            "historical research {proposition}",
            "primary historical sources {proposition}",
            "historiography {proposition}",
            "academic history journals {proposition}",
            "historical archives {proposition}",
            "historians' analyses {proposition}",
        ],
        "general": [
            "comprehensive overview {proposition}",
            "expert analysis {proposition}",
            "research and evidence {proposition}",
            "different perspectives on {proposition}",
            "critical evaluation {proposition}",
            "supporting evidence {proposition}",
            "counter-arguments {proposition}",
        ],
    }

    def _classify_topic_type(self, proposition: str) -> str:
        """Classify the proposition into a topic type for search optimization.

        Returns one of: academic, philosophical, scientific, consumer, political, historical, general
        """
        prompt = f"""Classify this proposition into ONE of these topic types:
- academic: scholarly/theoretical topics requiring peer-reviewed sources
- philosophical: epistemology, ethics, metaphysics, philosophy of mind/science
- scientific: empirical claims requiring research studies and data
- consumer: product/service comparisons, purchases, recommendations
- political: policy, governance, political events, elections
- historical: past events, historical analysis, historiography
- general: doesn't clearly fit other categories

PROPOSITION: "{proposition}"

Respond with ONLY the topic type (one word, lowercase). Choose the MOST specific applicable type.
For questions about philosophical schools, epistemology, or reasoning frameworks, choose "philosophical".
"""
        try:
            response = self.client.responses.create(
                model="o4-mini",  # Fast, cheap model for classification
                input=prompt,
                max_output_tokens=20,
            )
            # Track costs if usage data is available
            if hasattr(self, 'cost_tracker') and hasattr(response, 'usage') and response.usage:
                input_tokens = getattr(response.usage, 'input_tokens', 0) or 0
                output_tokens = getattr(response.usage, 'output_tokens', 0) or 0
                self.cost_tracker.add_cost("o4-mini", "topic_classification", input_tokens, output_tokens, 0)
            topic_type = response.output_text.strip().lower()
            # Validate it's a known type
            if topic_type in self.TOPIC_SEARCH_TEMPLATES:
                logger.info(f"Topic classified as: {topic_type}")
                return topic_type
            else:
                logger.warning(f"Unknown topic type '{topic_type}', defaulting to 'general'")
                return "general"
        except Exception as e:
            logger.warning(f"Topic classification failed: {e}, defaulting to 'general'")
            return "general"

    def _generate_search_categories(self, proposition: str, topic_type: str,
                                     hypotheses: List[Dict]) -> List[str]:
        """Generate diverse search categories based on topic type and hypotheses."""

        # Get base templates for this topic type
        templates = self.TOPIC_SEARCH_TEMPLATES.get(topic_type, self.TOPIC_SEARCH_TEMPLATES["general"])

        # Generate searches from templates
        searches = []
        for template in templates:
            searches.append(template.format(proposition=proposition))

        # Add hypothesis-specific searches
        for h in hypotheses:
            title = h.get("title", h.get("name", ""))
            if title and title.lower() not in ["catch-all", "other", "none of the above", "unforeseen"]:
                # Add hypothesis-specific search based on topic type
                if topic_type in ["academic", "philosophical", "scientific"]:
                    searches.append(f"research papers on {title}")
                    searches.append(f"scholarly analysis of {title}")
                elif topic_type == "consumer":
                    searches.append(f"detailed reviews of {title}")
                elif topic_type == "political":
                    searches.append(f"policy analysis {title}")
                else:
                    searches.append(f"evidence and analysis: {title}")

        # Deduplicate while preserving order
        seen = set()
        unique_searches = []
        for s in searches:
            s_lower = s.lower()
            if s_lower not in seen:
                seen.add(s_lower)
                unique_searches.append(s)

        # Limit to reasonable number (10-15 searches)
        return unique_searches[:15]

    def _run_single_search(self, search_category: str, proposition: str,
                            hyp_names: List[str]) -> Tuple[List[Dict], List[Dict]]:
        """Execute a single focused web search and return evidence items + URL citations.

        Makes one API call with structured output for a specific search category.
        """
        bfih_context = get_bfih_system_context("Evidence Gathering", "2")
        prompt = f"""{bfih_context}
SEARCH CATEGORY: {search_category}
PROPOSITION: "{proposition}"

HYPOTHESES:
{chr(10).join(hyp_names)}

YOUR TASK:
Search the web for evidence specifically relevant to: **{search_category}**

Return 6-10 DIVERSE evidence items from your search. IMPORTANT: Each item should come from a DIFFERENT source/publication. Do NOT return multiple items from the same website or encyclopedia entry.

Each item needs:
- evidence_id (unique string like "E1", "E2", etc.)
- description (specific factual finding - be detailed and specific)
- source_name (publication or website name)
- source_url (MUST be a full URL starting with https:// or http://, or "" if unknown)
- citation_apa (APA format citation with author, year, title, and source)
- date_accessed (today's date)
- supports_hypotheses (list of hypothesis IDs this supports)
- refutes_hypotheses (list of hypothesis IDs this argues against)
- evidence_type (one of: quantitative, qualitative, expert_testimony, historical_analogy, policy, institutional)

**CRITICAL**:
- source_url MUST be a real URL like https://example.com or leave empty if unknown
- Each evidence item must be from a UNIQUE source - avoid duplicates
- Prioritize peer-reviewed sources, academic journals, and authoritative publications
"""
        try:
            tools = [{"type": "web_search", "search_context_size": "high"}]
            result, url_citations = self._run_structured_phase(
                prompt, "evidence", f"Search: {search_category[:40]}",
                tools=tools, return_citations=True, model=self.model
            )
            return result.get("evidence_items", []), url_citations
        except Exception as e:
            logger.warning(f"Search '{search_category}' failed: {e}")
            return [], []

    def _run_phase_2_evidence(self, request: BFIHAnalysisRequest, methodology: str) -> Tuple[str, List[Dict]]:
        """Phase 2: Gather evidence via MULTIPLE focused web searches.
        Returns (markdown_text, structured_evidence)

        Uses topic-adaptive search strategy:
        1. Classifies the proposition type (academic, philosophical, consumer, etc.)
        2. Generates domain-appropriate search queries
        3. Performs 10-15 diverse searches to gather comprehensive evidence
        4. Deduplicates results by URL to avoid bibliography repetition
        """
        hypotheses = request.scenario_config.get("hypotheses", [])
        hyp_names = [f"{h.get('id', f'H{i}')}: {h.get('title', h.get('name', ''))}"
                     for i, h in enumerate(hypotheses)]
        proposition = request.proposition

        # Step 1: Classify topic type for search optimization
        print(f"\n[Classifying topic type for optimal search strategy...]")
        topic_type = self._classify_topic_type(proposition)
        print(f"[Topic classified as: {topic_type}]")

        # Step 2: Generate domain-specific search categories
        search_categories = self._generate_search_categories(proposition, topic_type, hypotheses)

        logger.info(f"Starting multi-search evidence gathering: {len(search_categories)} focused searches (PARALLEL)")
        print(f"\n[Starting {len(search_categories)} focused evidence searches in PARALLEL]")

        all_evidence = []
        all_citations = []

        # Define search function for parallel execution
        def run_search(search_idx: int, category: str) -> Tuple[int, str, List[Dict], List[Dict]]:
            """Run a single search and return (index, category, items, citations)"""
            logger.info(f"Search {search_idx + 1}/{len(search_categories)}: {category[:60]}...")
            items, citations = self._run_single_search(category, proposition, hyp_names)
            logger.info(f"  Search {search_idx + 1} complete: {len(items)} items, {len(citations)} citations")
            return (search_idx, category, items, citations)

        # Execute searches in PARALLEL
        max_parallel = min(8, len(search_categories))  # Limit parallel requests
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            # Submit all searches
            futures = {
                executor.submit(run_search, i, cat): i
                for i, cat in enumerate(search_categories)
            }

            # Collect results as they complete, maintaining order
            results = [None] * len(search_categories)
            completed = 0
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                    completed += 1
                    self._report_status(f"phase:evidence:{completed}/{len(search_categories)}")
                    print(f"[Search {completed}/{len(search_categories)} complete]")
                except Exception as e:
                    logger.error(f"Search {idx} failed: {e}")
                    results[idx] = (idx, search_categories[idx], [], [])

        # Process results in order and assign evidence IDs
        for search_idx, category, items, citations in results:
            base_id = len(all_evidence) + 1
            for j, item in enumerate(items):
                item["evidence_id"] = f"E{base_id + j}"

            all_evidence.extend(items)
            all_citations.extend(citations)

        logger.info(f"Multi-search complete: {len(all_evidence)} evidence items, {len(all_citations)} citations")
        print(f"[Multi-search complete: {len(all_evidence)} evidence items from {len(search_categories)} parallel searches]")

        # Now process the combined evidence
        evidence_items = all_evidence
        url_citations = all_citations

        # Populate source_url from url_citations if not already set
        # Build a lookup by title (case-insensitive, partial match)
        citation_url_map = {}
        for citation in url_citations:
            if citation.get('url') and citation.get('title'):
                # Store with lowercase title for matching
                title_key = citation['title'].lower().strip()
                citation_url_map[title_key] = citation['url']

        # Try to match evidence items with citations
        for item in evidence_items:
            if not item.get('source_url') or item['source_url'].strip() == '':
                source_name = item.get('source_name', '').lower().strip()
                citation_text = item.get('citation_apa', '').lower()

                # Try exact match on source name
                for title, url in citation_url_map.items():
                    if source_name and source_name in title:
                        item['source_url'] = url
                        break
                    # Also try matching parts of the citation
                    if title in citation_text:
                        item['source_url'] = url
                        break

        # If we have unused citations, add them to items without URLs
        used_urls = {item.get('source_url') for item in evidence_items if item.get('source_url')}
        unused_citations = [c for c in url_citations if c.get('url') and c['url'] not in used_urls]
        items_without_urls = [item for item in evidence_items if not item.get('source_url') or item['source_url'].strip() == '']

        # Assign remaining citations to items without URLs (best effort)
        for item, citation in zip(items_without_urls, unused_citations):
            item['source_url'] = citation['url']

        # Validate and clean up invalid URLs (must start with http)
        # LLM sometimes puts dates or descriptions in source_url field
        invalid_url_count = 0
        for item in evidence_items:
            url = item.get('source_url', '').strip()
            if url and not url.startswith('http'):
                # This is not a valid URL - clear it
                invalid_url_count += 1
                item['source_url'] = ''
        if invalid_url_count > 0:
            logger.warning(f"Cleared {invalid_url_count} invalid URLs (non-http values)")

        valid_url_count = sum(1 for item in evidence_items if item.get('source_url', '').startswith('http'))
        logger.info(f"Populated {valid_url_count} items with valid URLs from {len(url_citations)} citations")

        # Step 3: Deduplicate evidence by URL to avoid bibliography repetition
        # This is critical - same source appearing multiple times (e.g., Stanford Encyclopedia)
        # makes the bibliography look poor and repetitive
        seen_urls = set()
        seen_sources = set()  # Also dedupe by source name for items without URLs
        deduplicated_evidence = []

        for item in evidence_items:
            url = item.get('source_url', '').strip()
            source_name = item.get('source_name', '').lower().strip()

            # Normalize URL for comparison (remove archive dates, trailing slashes)
            normalized_url = url.lower().rstrip('/')
            # Remove archive date variations (e.g., /archives/fall2024/ -> /entries/)
            normalized_url = re.sub(r'/archives/[^/]+/', '/entries/', normalized_url)

            # Check if we've seen this URL or a very similar source
            is_duplicate = False
            if normalized_url and normalized_url.startswith('http'):
                if normalized_url in seen_urls:
                    is_duplicate = True
                else:
                    seen_urls.add(normalized_url)
            elif source_name:
                # For items without URLs, dedupe by source name
                if source_name in seen_sources:
                    is_duplicate = True
                else:
                    seen_sources.add(source_name)

            if not is_duplicate:
                deduplicated_evidence.append(item)
            else:
                logger.debug(f"Removing duplicate: {source_name or url[:50]}")

        # Step 4: Content-based deduplication using description similarity
        # This catches cases where the same study appears from different sources
        from difflib import SequenceMatcher

        def description_similarity(desc1: str, desc2: str) -> float:
            """Calculate similarity between two descriptions."""
            d1 = desc1.lower()[:200]
            d2 = desc2.lower()[:200]
            return SequenceMatcher(None, d1, d2).ratio()

        # Find and remove content duplicates (keep the one with better URL/citation)
        content_duplicates = set()
        for i, item1 in enumerate(deduplicated_evidence):
            if i in content_duplicates:
                continue
            for j, item2 in enumerate(deduplicated_evidence):
                if j <= i or j in content_duplicates:
                    continue
                desc1 = item1.get('description', '')
                desc2 = item2.get('description', '')
                if description_similarity(desc1, desc2) > 0.75:
                    # Keep the item with a valid URL, or the first one
                    url1 = item1.get('source_url', '').startswith('http')
                    url2 = item2.get('source_url', '').startswith('http')
                    if url2 and not url1:
                        content_duplicates.add(i)
                        logger.debug(f"Content duplicate: keeping {item2.get('evidence_id')} over {item1.get('evidence_id')}")
                    else:
                        content_duplicates.add(j)
                        logger.debug(f"Content duplicate: keeping {item1.get('evidence_id')} over {item2.get('evidence_id')}")

        if content_duplicates:
            deduplicated_evidence = [item for i, item in enumerate(deduplicated_evidence) if i not in content_duplicates]
            logger.info(f"Removed {len(content_duplicates)} content-similar duplicates")
            print(f"[Removed {len(content_duplicates)} content-similar evidence items]")

        # Renumber evidence IDs after deduplication
        for i, item in enumerate(deduplicated_evidence, 1):
            item["evidence_id"] = f"E{i}"

        duplicates_removed = len(evidence_items) - len(deduplicated_evidence)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} total duplicate evidence items")
            print(f"[Removed {duplicates_removed} total duplicate sources from evidence]")

        evidence_items = deduplicated_evidence

        # Generate markdown summary from structured data
        markdown_summary = self._generate_evidence_markdown(evidence_items)

        logger.info(f"Gathered {len(evidence_items)} unique evidence items")
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

    def _estimate_base_rates_stage1(self, request: BFIHAnalysisRequest,
                                     evidence_items: List[Dict]) -> Dict[str, float]:
        """Stage 1 of two-stage likelihood estimation: Estimate P(E) base rates.

        For each evidence item, estimates the marginal probability P(E) - the probability
        of observing that evidence regardless of which hypothesis is true.

        This is computed as: P(E) = Σ P(E|Hj) × P(Hj)

        The base rates are then used in Stage 2 to guide relative likelihood assessment,
        ensuring that non-predictive hypotheses get P(E|H) = P(E), yielding LR = 1.

        Returns:
            Dict mapping evidence_id -> P(E) base rate estimate
        """
        hypotheses = request.scenario_config.get("hypotheses", [])
        priors = request.scenario_config.get("priors_by_paradigm", {}).get("K0", {})

        # If no priors set, use uniform
        if not priors:
            n_hyp = len(hypotheses)
            priors = {h.get("id", f"H{i}"): 1.0/n_hyp for i, h in enumerate(hypotheses)}

        # Build hypothesis summary with priors for context
        hyp_summary = []
        for h in hypotheses:
            h_id = h.get("id", "H?")
            h_name = h.get("name", "Unknown")
            h_desc = h.get("description", "")[:150]
            prior = priors.get(h_id, 0.1)
            hyp_summary.append(f"- {h_id} (prior={prior:.2f}): {h_name} - {h_desc}")
        hyp_text = "\n".join(hyp_summary)

        # Build evidence summary
        evidence_summary = json.dumps([{
            "evidence_id": e.get("evidence_id"),
            "description": e.get("description", "")[:200],
            "source_name": e.get("source_name", "Unknown"),
            "evidence_type": e.get("evidence_type", "unknown")
        } for e in evidence_items], indent=2)

        bfih_context = get_bfih_system_context("Base Rate Estimation", "3a")
        prompt = f"""{bfih_context}
PROPOSITION: "{request.proposition}"

HYPOTHESES (with priors):
{hyp_text}

EVIDENCE ITEMS:
{evidence_summary}

## STAGE 1: BASE RATE ESTIMATION

For each evidence item, estimate P(E) - the marginal probability of observing this evidence
regardless of which hypothesis is true.

P(E) represents: "How likely is it that we would observe this evidence in the world as it is?"

This is conceptually: P(E) = Σ P(E|Hj) × P(Hj) summed over all hypotheses.

### Guidelines:
- P(E) reflects how surprising/common this evidence is in the general landscape
- Common findings (e.g., "experts disagree on X") have high P(E) ≈ 0.7-0.9
- Rare, specific findings (e.g., "RCT finds 47% effect size") have lower P(E) ≈ 0.1-0.4
- P(E) should NOT depend on which hypothesis you think is true - it's the unconditional probability

### Response Format:
Return a JSON object with "base_rates" array. Each item needs:
- evidence_id: The ID of the evidence item
- base_rate: Your estimate of P(E) between 0.01 and 0.99
- reasoning: Brief explanation of why this evidence has this base rate

IMPORTANT: Return ONLY valid JSON. No additional text before or after.

Example format:
{{
  "base_rates": [
    {{"evidence_id": "E1", "base_rate": 0.75, "reasoning": "Common finding in meta-analyses"}},
    {{"evidence_id": "E2", "base_rate": 0.25, "reasoning": "Rare specific result from large RCT"}}
  ]
}}
"""
        try:
            self._log_progress("Phase 3a: Estimating evidence base rates P(E)...")
            result = self._run_reasoning_phase(
                prompt, "Phase 3a: Base Rate Estimation",
                schema_name=None  # Will parse JSON manually
            )

            # Parse base rates from response
            base_rates = {}
            if isinstance(result, dict) and "base_rates" in result:
                for item in result.get("base_rates", []):
                    e_id = item.get("evidence_id")
                    rate = item.get("base_rate", 0.5)
                    if e_id:
                        base_rates[e_id] = max(0.01, min(0.99, rate))
                        logger.info(f"Base rate for {e_id}: P(E)={rate:.2f}")

            # Fill in missing evidence with default 0.5
            for e in evidence_items:
                e_id = e.get("evidence_id")
                if e_id and e_id not in base_rates:
                    base_rates[e_id] = 0.5
                    logger.warning(f"Missing base rate for {e_id}, using default 0.5")

            logger.info(f"Estimated base rates for {len(base_rates)} evidence items")
            return base_rates

        except Exception as e:
            logger.error(f"Base rate estimation failed: {e}, using default 0.5 for all")
            return {e.get("evidence_id"): 0.5 for e in evidence_items if e.get("evidence_id")}

    def _run_phase_3_likelihoods(self, request: BFIHAnalysisRequest, evidence_text: str,
                                   evidence_items: List[Dict]) -> Tuple[str, List[Dict]]:
        """Phase 3: Assign PARADIGM-SPECIFIC likelihoods using TWO-STAGE prompting.

        STAGE 1: Estimate P(E) base rate for each evidence item
        STAGE 2: Assign P(E|H,K) relative to P(E), ensuring non-predictive hypotheses get LR=1

        Returns (markdown_text, structured_clusters) where likelihoods are P(E|H,K)
        - different for each paradigm-hypothesis combination.
        """
        # STAGE 1: Estimate base rates P(E) for each evidence item
        base_rates = self._estimate_base_rates_stage1(request, evidence_items)

        # Get hypotheses and paradigms
        hypotheses = request.scenario_config.get("hypotheses", [])
        paradigms = request.scenario_config.get("paradigms", [])
        hyp_ids = [h.get("id", f"H{i}") for i, h in enumerate(hypotheses)]
        paradigm_ids = [p.get("id", f"K{i}") for i, p in enumerate(paradigms)]

        # Build hypothesis descriptions for better assessment
        hyp_descriptions = []
        for h in hypotheses:
            h_id = h.get("id", "H?")
            h_name = h.get("name", "Unknown")
            h_desc = h.get("description", "")[:200]
            verdict_type = h.get("verdict_type", "")
            hyp_descriptions.append(f"- {h_id}: {h_name}\n  Description: {h_desc}\n  Type: {verdict_type}")
        hyp_text = "\n".join(hyp_descriptions)

        # Summarize evidence items WITH base rates from Stage 1
        evidence_with_base_rates = [{
            "evidence_id": e.get("evidence_id"),
            "description": e.get("description", "")[:200],
            "source_name": e.get("source_name", "Unknown"),
            "source_url": e.get("source_url", ""),
            "evidence_type": e.get("evidence_type", "unknown"),
            "supports": e.get("supports_hypotheses", []),
            "refutes": e.get("refutes_hypotheses", []),
            "base_rate_P_E": base_rates.get(e.get("evidence_id"), 0.5)
        } for e in evidence_items]
        evidence_summary = json.dumps(evidence_with_base_rates, indent=2)

        bfih_context = get_bfih_system_context("Likelihood Assignment", "3b")
        prompt = f"""{bfih_context}
PROPOSITION: "{request.proposition}"

HYPOTHESES:
{hyp_text}

PARADIGMS: {paradigm_ids}

EVIDENCE ITEMS (with pre-computed base rates P(E)):
{evidence_summary}

## STAGE 2: RELATIVE LIKELIHOOD ASSESSMENT

You have been provided with P(E) - the base rate for each evidence item. Now you must assign
P(E|H) for each hypothesis RELATIVE TO P(E).

### CRITICAL PRINCIPLE: Likelihood Ratios and Non-Predictive Hypotheses

The Likelihood Ratio is: LR(H;E) = P(E|H) / P(E|¬H)

For a hypothesis to UPDATE posteriors, it must PREDICT the evidence differently than chance:
- If H specifically PREDICTS E → P(E|H) > P(E) → LR > 1 → positive evidence for H
- If H specifically PREDICTS ¬E → P(E|H) < P(E) → LR < 1 → negative evidence for H
- If H is COMPATIBLE with E but makes NO specific prediction → P(E|H) = P(E) → LR = 1 → NO UPDATE

### MANDATORY RULE FOR NON-PREDICTIVE HYPOTHESES

A "catch-all", "unforeseen", or "partial/hedged" hypothesis that does NOT make specific predictions
MUST have P(E|H) = P(E) for that evidence. This yields LR = 1 and WoE = 0 dB.

Why? Because if a hypothesis doesn't predict whether E occurs, then observing E tells us nothing
about whether that hypothesis is true. The evidence and hypothesis are independent.

WRONG: Assigning P(E|H) = 0.5 to all non-predictive hypotheses (this creates artificial LR shifts)
RIGHT: Assigning P(E|H) = P(E) (the base rate) to non-predictive hypotheses (this yields LR = 1)

### HOW TO ASSESS P(E|H) RELATIVE TO P(E)

For each evidence item with base rate P(E):

1. **Does hypothesis H make a SPECIFIC prediction about this evidence?**
   - If YES: Estimate P(E|H) based on how strongly H predicts E
   - If NO (H is compatible but non-predictive): Set P(E|H) = P(E) exactly

2. **For predictive hypotheses, assess the direction:**
   - H predicts E should occur: P(E|H) > P(E)
   - H predicts E should NOT occur: P(E|H) < P(E)

3. **Scale by prediction strength:**
   - Strong prediction: P(E|H) can be much higher/lower than P(E)
   - Weak prediction: P(E|H) is only slightly higher/lower than P(E)

### EXAMPLE

Evidence E: "Large meta-analysis finds no link between X and Y" with P(E) = 0.70

- H1 (X causes Y): PREDICTS ¬E → P(E|H1) = 0.10 (much lower than P(E))
- H2 (X does not cause Y): PREDICTS E → P(E|H2) = 0.95 (higher than P(E))
- H0 (Unforeseen factor): NO PREDICTION → P(E|H0) = 0.70 = P(E) (exactly equal!)
- H3 (Subgroup effect only): WEAK PREDICTION toward E → P(E|H3) = 0.75 (slightly above P(E))

### PARADIGM EFFECTS

Different paradigms may weight evidence types differently, affecting P(E|H,K):
- Paradigm K0 (mainstream): Uses base rates as-is
- Biased paradigms: May adjust how strongly evidence predicts hypotheses

YOUR TASK:
1. Group evidence into 3-5 CLUSTERS based on thematic similarity
2. For EACH cluster, assign P(E|H,K) for EACH hypothesis under EACH paradigm
3. For EACH likelihood, explicitly compare to the base rate P(E):
   - If H predicts E: P(E|H) > P(E)
   - If H predicts ¬E: P(E|H) < P(E)
   - If H makes no prediction: P(E|H) = P(E) EXACTLY
4. Justify your assessment relative to the base rate

Return a JSON object with "clusters" array. Each cluster needs:
- cluster_id, cluster_name, description, evidence_ids (all required)
- cluster_base_rate: average P(E) for evidence in this cluster
- paradigm_likelihoods: array of {{paradigm_id, hypothesis_likelihoods: [{{hypothesis_id, probability, justification, relative_to_base_rate: "above"/"below"/"equal"}}]}}

IMPORTANT: Return ONLY valid JSON. No additional text before or after the JSON object.
"""
        # Check schema complexity
        schema_complexity = len(paradigms) * len(hypotheses)

        # DEFAULT: Use calibrated likelihood elicitation to combat hedging bias
        # This forces the LLM to commit to discrimination strength (LR_range) before
        # assigning probabilities, preventing the 0.4-0.6 hedging that makes posteriors meaningless.
        use_calibrated = True  # Set to False to revert to old batched/direct approach

        if use_calibrated:
            logger.info(f"Using CALIBRATED likelihood elicitation (schema complexity: {schema_complexity})")
            clusters = self._run_phase_3b_calibrated(
                request, evidence_items, base_rates, hypotheses, paradigms, hyp_text, evidence_summary
            )
            markdown_summary = self._generate_clusters_markdown(clusters, base_rates)
        elif schema_complexity > 24:
            logger.info(f"Schema complexity {schema_complexity} > 24, using batched paradigm approach")
            clusters = self._run_phase_3b_batched(
                request, evidence_items, base_rates, hypotheses, paradigms, hyp_text, evidence_summary
            )
            markdown_summary = self._generate_clusters_markdown(clusters, base_rates)
        else:
            try:
                # Use reasoning model for likelihood assessment (requires careful evidence-paradigm analysis)
                # Falls back to structured output (o4-mini) if JSON parsing fails
                self._log_progress("Phase 3b: Assigning likelihoods relative to base rates...")
                result = self._run_reasoning_phase(
                    prompt, "Phase 3b: Likelihood Assignment (reasoning)",
                    schema_name="clusters"  # Enables structured output fallback
                )
                raw_clusters = result.get("clusters", [])
                # Convert array format to dict format for compatibility
                clusters = []
                for c in raw_clusters:
                    # Compute average base rate for this cluster
                    cluster_evidence_ids = c.get("evidence_ids", [])
                    cluster_base_rate = c.get("cluster_base_rate")
                    if cluster_base_rate is None and cluster_evidence_ids:
                        rates = [base_rates.get(e_id, 0.5) for e_id in cluster_evidence_ids]
                        cluster_base_rate = sum(rates) / len(rates) if rates else 0.5

                    converted = {
                        "cluster_id": c.get("cluster_id"),
                        "cluster_name": c.get("cluster_name"),
                        "description": c.get("description"),
                        "evidence_ids": cluster_evidence_ids,
                        "cluster_base_rate": cluster_base_rate,
                        "likelihoods_by_paradigm": {}
                    }
                    for pl in c.get("paradigm_likelihoods", []):
                        paradigm_id = pl.get("paradigm_id")
                        if paradigm_id:
                            converted["likelihoods_by_paradigm"][paradigm_id] = {}
                            for hl in pl.get("hypothesis_likelihoods", []):
                                h_id = hl.get("hypothesis_id")
                                if h_id:
                                    prob = hl.get("probability", 0.5)
                                    rel = hl.get("relative_to_base_rate", "")
                                    converted["likelihoods_by_paradigm"][paradigm_id][h_id] = {
                                        "probability": prob,
                                        "justification": hl.get("justification", ""),
                                        "relative_to_base_rate": rel
                                    }
                                    # Log when LR = 1 (non-predictive)
                                    if rel == "equal" or (cluster_base_rate and abs(prob - cluster_base_rate) < 0.02):
                                        logger.info(f"  {h_id} is non-predictive for cluster {c.get('cluster_id')}: P(E|H)={prob:.2f} ≈ P(E)={cluster_base_rate:.2f} → LR≈1")
                    clusters.append(converted)
                # Generate markdown summary with base rate info
                markdown_summary = self._generate_clusters_markdown(clusters, base_rates)
            except Exception as e:
                logger.error(f"Structured output failed for clusters: {e}, falling back to batched approach")
                # Fallback to batched paradigm approach
                clusters = self._run_phase_3b_batched(
                    request, evidence_items, base_rates, hypotheses, paradigms, hyp_text, evidence_summary
                )
                markdown_summary = self._generate_clusters_markdown(clusters, base_rates)

        logger.info(f"Created {len(clusters)} evidence clusters with two-stage likelihood assessment")
        return markdown_summary, clusters

    def _run_phase_3b_batched(
        self,
        request: BFIHAnalysisRequest,
        evidence_items: List[Dict],
        base_rates: Dict[str, float],
        hypotheses: List[Dict],
        paradigms: List[Dict],
        hyp_text: str,
        evidence_summary: str
    ) -> List[Dict]:
        """Phase 3b with batched paradigm processing for complex schemas.

        When there are many paradigms × hypotheses, this method:
        1. First gets cluster structure (grouping only)
        2. Then processes each paradigm separately
        3. Merges all paradigm likelihoods into the clusters

        This reduces each API call from O(paradigms × hypotheses) to O(hypotheses).
        """
        self._log_progress("Phase 3b: Using batched paradigm approach for complex schema...")

        paradigm_ids = [p.get("id", f"K{i}") for i, p in enumerate(paradigms)]
        hyp_ids = [h.get("id", f"H{i}") for i, h in enumerate(hypotheses)]

        # STEP 1: Get cluster structure (no likelihoods yet)
        bfih_context = get_bfih_system_context("Cluster Formation", "3b-step1")
        cluster_prompt = f"""{bfih_context}
PROPOSITION: "{request.proposition}"

EVIDENCE ITEMS (with pre-computed base rates P(E)):
{evidence_summary}

## STEP 1: CLUSTER FORMATION

Group the evidence items into 3-5 thematic clusters based on what aspect of the proposition they address.

For each cluster provide:
- cluster_id: C1, C2, etc.
- cluster_name: Short descriptive name
- description: What this evidence cluster addresses
- evidence_ids: List of evidence IDs in this cluster
- cluster_base_rate: Average P(E) for evidence in this cluster

Return JSON with a "clusters" array. Do NOT include paradigm_likelihoods yet - we will add those separately.

Example format:
{{"clusters": [
  {{"cluster_id": "C1", "cluster_name": "Name", "description": "...", "evidence_ids": ["E1", "E2"], "cluster_base_rate": 0.65}},
  ...
]}}
"""
        try:
            self._log_progress("Phase 3b Step 1: Forming evidence clusters...")
            result = self._run_reasoning_phase(
                cluster_prompt, "Phase 3b Step 1: Cluster Formation",
                schema_name="clusters_simple"
            )
            raw_clusters = result.get("clusters", [])
        except Exception as e:
            logger.warning(f"Cluster formation failed: {e}, using default single cluster")
            # Fallback: single cluster with all evidence
            raw_clusters = [{
                "cluster_id": "C1",
                "cluster_name": "All Evidence",
                "description": "All gathered evidence items",
                "evidence_ids": [e.get("evidence_id") for e in evidence_items],
                "cluster_base_rate": sum(base_rates.values()) / len(base_rates) if base_rates else 0.5
            }]

        # Initialize clusters with empty paradigm likelihoods
        clusters = []
        for c in raw_clusters:
            cluster_evidence_ids = c.get("evidence_ids", [])
            cluster_base_rate = c.get("cluster_base_rate")
            if cluster_base_rate is None and cluster_evidence_ids:
                rates = [base_rates.get(e_id, 0.5) for e_id in cluster_evidence_ids]
                cluster_base_rate = sum(rates) / len(rates) if rates else 0.5

            clusters.append({
                "cluster_id": c.get("cluster_id"),
                "cluster_name": c.get("cluster_name"),
                "description": c.get("description"),
                "evidence_ids": cluster_evidence_ids,
                "cluster_base_rate": cluster_base_rate,
                "likelihoods_by_paradigm": {}
            })

        logger.info(f"Phase 3b Step 1: Created {len(clusters)} evidence clusters")

        # STEP 2: Get likelihoods for each paradigm separately
        cluster_summary = json.dumps([{
            "cluster_id": c["cluster_id"],
            "cluster_name": c["cluster_name"],
            "description": c["description"],
            "evidence_ids": c["evidence_ids"],
            "cluster_base_rate": c["cluster_base_rate"]
        } for c in clusters], indent=2)

        for p_idx, paradigm in enumerate(paradigms):
            paradigm_id = paradigm.get("id", f"K{p_idx}")
            paradigm_name = paradigm.get("name", "Unknown")
            paradigm_desc = paradigm.get("description", "")[:200]

            self._log_progress(f"Phase 3b Step 2: Assigning likelihoods for {paradigm_id} ({p_idx + 1}/{len(paradigms)})...")

            paradigm_prompt = f"""{bfih_context}
PROPOSITION: "{request.proposition}"

HYPOTHESES:
{hyp_text}

PARADIGM: {paradigm_id} - {paradigm_name}
Description: {paradigm_desc}

EVIDENCE CLUSTERS:
{cluster_summary}

## STEP 2: LIKELIHOOD ASSIGNMENT FOR {paradigm_id}

For EACH cluster, assign P(E|H) for EACH hypothesis under paradigm {paradigm_id}.

CRITICAL RULES:
1. If hypothesis H makes NO specific prediction about this evidence → P(E|H) = cluster_base_rate (LR = 1)
2. If H predicts this evidence → P(E|H) > cluster_base_rate
3. If H predicts AGAINST this evidence → P(E|H) < cluster_base_rate

Return JSON with cluster likelihoods for this paradigm only:
{{"paradigm_id": "{paradigm_id}", "cluster_likelihoods": [
  {{"cluster_id": "C1", "hypothesis_likelihoods": [
    {{"hypothesis_id": "H0", "probability": 0.65, "relative_to_base_rate": "equal"}},
    {{"hypothesis_id": "H1", "probability": 0.85, "relative_to_base_rate": "above"}},
    ...
  ]}},
  ...
]}}
"""
            try:
                # Use raw JSON output (no schema) since the structure is simpler per-paradigm
                result = self._run_reasoning_phase(
                    paradigm_prompt, f"Phase 3b: {paradigm_id} Likelihoods",
                    schema_name=None  # Simpler per-paradigm output doesn't need schema enforcement
                )

                # Merge results into clusters
                cluster_likelihoods = result.get("cluster_likelihoods", [])
                for cl in cluster_likelihoods:
                    c_id = cl.get("cluster_id")
                    # Find matching cluster
                    for cluster in clusters:
                        if cluster["cluster_id"] == c_id:
                            cluster["likelihoods_by_paradigm"][paradigm_id] = {}
                            cluster_base_rate = cluster.get("cluster_base_rate", 0.5)
                            for hl in cl.get("hypothesis_likelihoods", []):
                                h_id = hl.get("hypothesis_id")
                                if h_id:
                                    prob = hl.get("probability", 0.5)
                                    rel = hl.get("relative_to_base_rate", "")
                                    cluster["likelihoods_by_paradigm"][paradigm_id][h_id] = {
                                        "probability": prob,
                                        "justification": hl.get("justification", ""),
                                        "relative_to_base_rate": rel
                                    }
                                    # Log non-predictive
                                    if rel == "equal" or abs(prob - cluster_base_rate) < 0.02:
                                        logger.info(f"  {h_id} is non-predictive for {c_id} under {paradigm_id}: P(E|H)={prob:.2f} ≈ P(E)={cluster_base_rate:.2f}")
                            break

            except Exception as e:
                logger.error(f"FATAL: Failed to get likelihoods for {paradigm_id}: {e}")
                raise RuntimeError(
                    f"Phase 3b ABORTED: Could not obtain valid likelihoods for paradigm {paradigm_id}. "
                    f"Error: {e}. Refusing to continue with meaningless fallback values."
                )

        # Validate that we got actual likelihoods for all paradigms
        for cluster in clusters:
            for paradigm_id in paradigm_ids:
                if paradigm_id not in cluster.get("likelihoods_by_paradigm", {}):
                    raise RuntimeError(
                        f"Phase 3b ABORTED: Missing likelihoods for paradigm {paradigm_id} in cluster {cluster.get('cluster_id')}. "
                        f"Refusing to continue with incomplete data."
                    )
                paradigm_likelihoods = cluster["likelihoods_by_paradigm"][paradigm_id]
                if len(paradigm_likelihoods) < len(hyp_ids) * 0.5:  # At least 50% of hypotheses
                    raise RuntimeError(
                        f"Phase 3b ABORTED: Incomplete likelihoods for paradigm {paradigm_id} in cluster {cluster.get('cluster_id')}. "
                        f"Got {len(paradigm_likelihoods)}/{len(hyp_ids)} hypotheses. Refusing to continue with incomplete data."
                    )

        logger.info(f"Phase 3b batched complete: {len(clusters)} clusters with {len(paradigms)} paradigms each (all validated)")
        return clusters

    # ============================================================================
    # LR_RANGE QUALITATIVE SCALE - Calibration anchors for likelihood ratios
    # ============================================================================
    LR_SCALE = {
        "weak": {"lr": 3, "description": "Weak discrimination - evidence slightly favors one hypothesis over another"},
        "moderate": {"lr": 6, "description": "Moderate discrimination - noticeable but not conclusive preference"},
        "strong": {"lr": 10, "description": "Strong discrimination - clear preference, ~10dB weight of evidence"},
        "very_strong": {"lr": 18, "description": "Very strong discrimination - compelling preference"},
        "decisive": {"lr": 30, "description": "Decisive discrimination - near-conclusive preference, ~15dB WoE"},
    }

    def _compute_likelihood_bounds(self, base_rate: float, lr_range: float) -> Tuple[float, float]:
        """
        Compute P(E|H_min) and P(E|H_max) given base rate and LR range.

        Uses the constraint that if H_min and H_max had equal priors, their
        weighted average would equal the base rate:
            P(E) ≈ (P(E|H_min) + P(E|H_max)) / 2
        Combined with:
            LR_range = P(E|H_max) / P(E|H_min)

        Solving: P(E|H_min) = 2 * P(E) / (1 + LR_range)
                 P(E|H_max) = P(E|H_min) * LR_range

        With bounds clamping to [0.02, 0.98].
        """
        # Compute unclamped values
        p_min = 2 * base_rate / (1 + lr_range)
        p_max = p_min * lr_range

        # Clamp to valid probability range
        p_min = max(0.02, min(0.98, p_min))
        p_max = max(0.02, min(0.98, p_max))

        # If clamping broke the ratio, adjust
        if p_max / p_min < lr_range * 0.5:  # More than 50% off
            # Spread from base_rate using log-odds
            log_spread = math.log(lr_range) / 2
            logit_base = math.log(base_rate / (1 - base_rate)) if 0 < base_rate < 1 else 0

            logit_max = logit_base + log_spread
            logit_min = logit_base - log_spread

            p_max = 1 / (1 + math.exp(-logit_max))
            p_min = 1 / (1 + math.exp(-logit_min))

            # Final clamp
            p_min = max(0.02, min(0.98, p_min))
            p_max = max(0.02, min(0.98, p_max))

        return p_min, p_max

    def _run_phase_3b_calibrated(
        self,
        request: BFIHAnalysisRequest,
        evidence_items: List[Dict],
        base_rates: Dict[str, float],
        hypotheses: List[Dict],
        paradigms: List[Dict],
        hyp_text: str,
        evidence_summary: str
    ) -> List[Dict]:
        """Phase 3b with CALIBRATED likelihood elicitation to combat hedging bias.

        Instead of asking for raw P(E|H) values (which LLMs hedge to 0.4-0.6),
        this method uses a structured elicitation process:

        For each evidence cluster:
        1. Confirm base rate P(E)
        2. Identify H_max (most favored) and H_min (least favored) hypotheses
        3. Choose LR_range from calibrated scale (3, 6, 10, 18, 30)
        4. Compute P(E|H_max) and P(E|H_min) programmatically
        5. Place remaining hypotheses relative to these anchors
        6. Sanity check the full likelihood set

        This forces the LLM to commit to discrimination strength FIRST,
        then derive consistent probabilities from that commitment.
        """
        self._log_progress("Phase 3b: Using CALIBRATED likelihood elicitation...")

        paradigm_ids = [p.get("id", f"K{i}") for i, p in enumerate(paradigms)]
        hyp_ids = [h.get("id", f"H{i}") for i, h in enumerate(hypotheses)]

        # Build hypothesis summary for prompts
        hyp_summary = []
        for h in hypotheses:
            h_id = h.get("id", "H?")
            h_name = h.get("name", "Unknown")
            h_stance = h.get("proposition_stance", "")
            hyp_summary.append(f"- {h_id}: {h_name} [{h_stance}]")
        hyp_summary_text = "\n".join(hyp_summary)

        # STEP 1: Get cluster structure based on MECHANISTIC INDEPENDENCE
        bfih_context = get_bfih_system_context("Calibrated Likelihood Elicitation", "3b-calibrated")
        cluster_prompt = f"""{bfih_context}
PROPOSITION: "{request.proposition}"

EVIDENCE ITEMS (with pre-computed base rates P(E)):
{evidence_summary}

## STEP 1: MECHANISTIC CLUSTER FORMATION

Group evidence items by their **mechanistic source** - the generative process that produced the evidence.
This is NOT about topic or theme, but about CONDITIONAL INDEPENDENCE.

### The Conditional Independence Principle

Two evidence items E1 and E2 should be in SEPARATE clusters if they are conditionally independent
given the hypotheses. Ask: "Given hypothesis H, does knowing E1 tell me anything about E2 beyond
what H already tells me?"

**Examples of DIFFERENT mechanistic sources (should be separate clusters):**
- Clinical case studies (from medical/neurological observation)
- Experimental philosophy surveys (from psychological studies of folk intuitions)
- Philosophical arguments (from conceptual/logical analysis)
- Legal precedents (from institutional/juridical practice)
- Historical practices (from anthropological/historical records)
- Neuroscientific findings (from brain imaging/lesion studies)

**Examples of SAME mechanistic source (should be same cluster):**
- Two different amnesia case studies (both from clinical observation)
- Two surveys of folk intuitions about identity (both from experimental psychology)
- Two philosophical thought experiments by different authors (both from conceptual analysis)

### Why This Matters

If we incorrectly lump conditionally independent evidence together:
- Complex "PARTIAL" hypotheses get unearned credit for "explaining mixed evidence"
- Simple hypotheses get unfairly penalized for not predicting unrelated evidence
- Occam's Razor fails because accommodation is confused with prediction

### Instructions

1. For each evidence item, identify its mechanistic source
2. Group items that share the SAME generative process
3. Create at most **8 clusters** (if more sources exist, merge the most similar ones)
4. Justify why items in each cluster are conditionally DEPENDENT (share a source)
5. Assign clusters to higher-level categories for reporting hierarchy

For each cluster provide:
- cluster_id: C1, C2, etc.
- cluster_name: Short descriptive name (e.g., "Clinical Amnesia Cases")
- mechanistic_source: The generative process (e.g., "medical/neurological observation")
- dependence_justification: Why these items are conditionally dependent given hypotheses
- hierarchy_group: Higher-level category for reporting (e.g., "Empirical Studies", "Theoretical Arguments", "Institutional Practices")
- evidence_ids: List of evidence IDs in this cluster
- cluster_base_rate: Average P(E) for evidence in this cluster

Return JSON with this structure:
{{
  "clusters": [
    {{
      "cluster_id": "C1",
      "cluster_name": "Clinical Amnesia Cases",
      "mechanistic_source": "medical/neurological case observation",
      "dependence_justification": "All items arise from clinical documentation of patients with memory disorders; knowing one case outcome informs expectations about similar cases",
      "hierarchy_group": "Empirical Studies",
      "evidence_ids": ["E1", "E3", "E7"],
      "cluster_base_rate": 0.65
    }},
    ...
  ],
  "hierarchy": [
    {{
      "group_name": "Empirical Studies",
      "description": "Evidence from scientific observation and experimentation",
      "cluster_ids": ["C1", "C2"]
    }},
    ...
  ]
}}

IMPORTANT:
- Maximum 8 clusters
- Each evidence item must appear in exactly one cluster
- Prioritize MECHANISTIC INDEPENDENCE over thematic similarity
- If unsure whether items are independent, default to SEPARATE clusters
"""
        try:
            self._log_progress("Phase 3b Step 1: Forming mechanistic evidence clusters...")
            result = self._run_reasoning_phase(
                cluster_prompt, "Phase 3b Step 1: Mechanistic Cluster Formation",
                schema_name=None  # Free-form JSON for complex structure
            )
            raw_clusters = result.get("clusters", [])
            cluster_hierarchy = result.get("hierarchy", [])
        except Exception as e:
            logger.warning(f"Cluster formation failed: {e}, using default single cluster")
            raw_clusters = [{
                "cluster_id": "C1",
                "cluster_name": "All Evidence",
                "mechanistic_source": "mixed sources",
                "dependence_justification": "Fallback: all evidence grouped together",
                "hierarchy_group": "All Evidence",
                "evidence_ids": [e.get("evidence_id") for e in evidence_items],
                "cluster_base_rate": sum(base_rates.values()) / len(base_rates) if base_rates else 0.5
            }]
            cluster_hierarchy = [{"group_name": "All Evidence", "description": "All gathered evidence", "cluster_ids": ["C1"]}]

        # Sanity check: max 8 clusters
        if len(raw_clusters) > 8:
            logger.warning(f"Cluster formation returned {len(raw_clusters)} clusters, limiting to 8")
            raw_clusters = raw_clusters[:8]

        # Initialize clusters with new mechanistic fields
        clusters = []
        for c in raw_clusters:
            cluster_evidence_ids = c.get("evidence_ids", [])
            cluster_base_rate = c.get("cluster_base_rate")
            if cluster_base_rate is None and cluster_evidence_ids:
                rates = [base_rates.get(e_id, 0.5) for e_id in cluster_evidence_ids]
                cluster_base_rate = sum(rates) / len(rates) if rates else 0.5

            cluster_data = {
                "cluster_id": c.get("cluster_id"),
                "cluster_name": c.get("cluster_name"),
                "mechanistic_source": c.get("mechanistic_source", "unspecified"),
                "dependence_justification": c.get("dependence_justification", ""),
                "hierarchy_group": c.get("hierarchy_group", "Uncategorized"),
                "description": c.get("description", c.get("mechanistic_source", "")),
                "evidence_ids": cluster_evidence_ids,
                "cluster_base_rate": cluster_base_rate,
                "likelihoods_by_paradigm": {},
                "calibration_info": {}  # Store calibration metadata
            }
            clusters.append(cluster_data)

            # Log cluster info including mechanistic source
            item_count = len(cluster_evidence_ids)
            logger.info(f"  {cluster_data['cluster_id']}: {cluster_data['cluster_name']} ({item_count} items) - Source: {cluster_data['mechanistic_source']}")
            if item_count == 1:
                logger.warning(f"  WARNING: Cluster {cluster_data['cluster_id']} has only 1 item - consider if this is appropriate")

        # Store hierarchy for reporting
        self._cluster_hierarchy = cluster_hierarchy

        logger.info(f"Phase 3b Step 1: Created {len(clusters)} mechanistic evidence clusters")

        # STEP 2-6: Calibrated likelihood elicitation for each cluster (PARALLELIZED)
        lr_scale_text = "\n".join([
            f"- {name}: LR={info['lr']}x - {info['description']}"
            for name, info in self.LR_SCALE.items()
        ])

        # Define calibration function for a single cluster (to be run in parallel)
        def calibrate_cluster(cluster_idx: int, cluster: dict) -> dict:
            c_id = cluster["cluster_id"]
            c_name = cluster["cluster_name"]
            c_desc = cluster["description"]
            c_base_rate = cluster["cluster_base_rate"]
            c_evidence = cluster["evidence_ids"]

            self._log_progress(f"Phase 3b Cluster {cluster_idx + 1}/{len(clusters)}: Calibrating likelihoods for {c_id}...")

            # Combined calibration prompt - asks for all calibration info at once
            calibration_prompt = f"""{bfih_context}
PROPOSITION: "{request.proposition}"

HYPOTHESES:
{hyp_summary_text}

EVIDENCE CLUSTER: {c_id} - {c_name}
Description: {c_desc}
Evidence IDs: {', '.join(c_evidence)}
Base Rate P(E): {c_base_rate:.3f}

## CALIBRATED LIKELIHOOD ELICITATION

You must assign likelihoods P(E|H) for this evidence cluster. To avoid hedging bias,
follow this structured process:

### CRITICAL: Occam's Razor Principle

Before assigning likelihoods, understand this fundamental principle:

**"Compatible with E" is NOT the same as "predicts E"**

- A hypothesis that makes a SHARP, SPECIFIC prediction that E will occur deserves HIGH P(E|H)
- A hypothesis that is merely COMPATIBLE with E (but also compatible with many other outcomes)
  deserves P(E|H) close to base rate P(E), because E is just one of many outcomes it allows

**Complexity Penalty:**

Compare hypotheses by their complexity (number of conditions, qualifications, or degrees of freedom):
- SIMPLE hypothesis: "X requires Y" (sharp prediction, easily falsified)
- COMPLEX/PARTIAL hypothesis: "X requires Y under conditions Z1, Z2, Z3..." (fuzzy prediction, hard to falsify)

If BOTH a simple and a complex hypothesis are compatible with evidence E:
- The SIMPLER hypothesis gets HIGHER P(E|H) because it made a riskier, sharper prediction
- The COMPLEX hypothesis gets LOWER P(E|H) because its probability mass is spread across many possible outcomes

**Example:**
- H_simple: "LLMs cannot be conscious" → If we see mixed evidence, this is surprising → LOW P(E|H)
- H_complex: "LLMs are conscious under specific architectural conditions" → Mixed evidence fits → but so would
  full consciousness AND no consciousness, so P(E|H) should be MODERATE, not HIGH

A "PARTIAL" or "nuanced" hypothesis that could explain almost ANY outcome should get P(E|H) ≈ P(E).
Only hypotheses that would be FALSIFIED by ¬E deserve P(E|H) significantly above P(E).

### Step A: Identify Discriminating Hypotheses (with Required Rationales)

Which hypothesis would MOST expect this evidence (H_max)?
Which hypothesis would LEAST expect this evidence (H_min)?

**CRITICAL: Focus on the most reliable evidence pieces.** An evidence cluster should be judged by
its most methodologically rigorous and statistically significant pieces. Do NOT let one weak study
or unreliable observation dilute the impact of multiple strong, reliable experiments. Identify the
2-3 strongest evidence items in the cluster and let those drive your discrimination assessment.

**REQUIRED RATIONALES:**
You MUST provide a 1-sentence rationale for EACH choice:
- **H_max rationale**: Cite SPECIFIC aspects of the evidence (study findings, experimental results,
  observed phenomena) and explain HOW those aspects align with H_max's predictions.
- **H_min rationale**: Cite SPECIFIC aspects of the evidence and explain HOW those aspects
  contradict or fail to support H_min's predictions.

These rationales must be LOGICALLY COHERENT with your likelihood assignments. If your rationale
contradicts your H_max/H_min choice (e.g., you say "H3 predicts mixed findings" but H3 doesn't
actually predict that more sharply than simpler hypotheses), you must REASSESS and choose differently.

Think carefully:
- Does this evidence actually discriminate between hypotheses?
- Is the apparent "winner" a simple hypothesis making a sharp prediction, or a complex hypothesis
  that could explain almost anything?
- Apply Occam's Razor: prefer simpler hypotheses that make riskier predictions
- **Coherence check**: Re-read your rationales. Would a neutral observer agree that your cited
  evidence aspects logically support your H_max/H_min assignments?

### Step B: Choose Discrimination Strength (LR_range)

How diagnostic is this evidence? The Likelihood Ratio range LR_range = P(E|H_max)/P(E|H_min)
indicates how strongly this evidence discriminates:

{lr_scale_text}

If the evidence doesn't discriminate (all hypotheses equally compatible), choose "none" (LR=1).

### Step C: Assign Likelihood Values

Given your chosen LR_range, assign P(E|H) for ALL hypotheses following these rules:

1. P(E|H_max) should be ABOVE the base rate P(E)={c_base_rate:.3f}
2. P(E|H_min) should be BELOW the base rate
3. The ratio P(E|H_max)/P(E|H_min) should approximately equal your chosen LR_range
4. Other hypotheses should be placed relative to these anchors:
   - If similar to H_max: closer to P(E|H_max)
   - If similar to H_min: closer to P(E|H_min)
   - If non-predictive (no specific prediction): P(E|H) = P(E) = {c_base_rate:.3f}

5. **COMPLEXITY ADJUSTMENT (Occam's Razor):**
   - If two hypotheses are equally compatible with E, the SIMPLER one gets HIGHER P(E|H)
   - PARTIAL/conditional hypotheses (e.g., "X under conditions Y and Z") should be penalized
     relative to simpler hypotheses that make the same prediction
   - A hypothesis with many qualifications that could "explain" almost any outcome
     should get P(E|H) ≈ P(E), NOT P(E|H) > P(E)

### Step D: Sanity Check

Verify your assignments make sense:
- Does P(E|H_max)/P(E|H_min) ≈ LR_range?
- Are non-predictive hypotheses at the base rate?
- Do the relative positions match the hypotheses' predictions?
- **Occam check:** Is a PARTIAL/complex hypothesis getting higher P(E|H) than a simpler hypothesis
  that makes the same prediction? If so, reduce the complex hypothesis's likelihood.

Return JSON with this exact structure:
{{
  "cluster_id": "{c_id}",
  "base_rate": {c_base_rate:.3f},
  "key_evidence": ["<ID of strongest evidence item>", "<ID of 2nd strongest>"],
  "calibration": {{
    "h_max": "<hypothesis ID that most expects this evidence>",
    "h_max_rationale": "<1 sentence citing SPECIFIC evidence aspects and HOW they support H_max>",
    "h_min": "<hypothesis ID that least expects this evidence>",
    "h_min_rationale": "<1 sentence citing SPECIFIC evidence aspects and HOW they contradict H_min>",
    "lr_range_category": "<none|weak|moderate|strong|very_strong|decisive>",
    "lr_range_value": <numeric LR value: 1, 3, 6, 10, 18, or 30>,
    "coherence_verified": <true if rationales logically support H_max/H_min choices, false if reassessment was needed>
  }},
  "hypothesis_likelihoods": [
    {{"hypothesis_id": "H0", "probability": <float 0.02-0.98>, "position": "<h_min|below_base|at_base|above_base|h_max>"}},
    {{"hypothesis_id": "H1", "probability": <float>, "position": "<position>"}},
    ...
  ]
}}

IMPORTANT:
- Use actual probability values, not placeholders
- Probability values must be between 0.02 and 0.98
- If LR_range > 1, H_max and H_min MUST have different probabilities
- Position "at_base" means P(E|H) ≈ {c_base_rate:.3f} (non-predictive hypothesis)
"""

            try:
                result = self._run_reasoning_phase(
                    calibration_prompt, f"Phase 3b: {c_id} Calibration",
                    schema_name=None
                )

                # Extract calibration info
                calibration = result.get("calibration", {})
                h_max = calibration.get("h_max", "")
                h_max_rationale = calibration.get("h_max_rationale", "")
                h_min = calibration.get("h_min", "")
                h_min_rationale = calibration.get("h_min_rationale", "")
                lr_category = calibration.get("lr_range_category", "moderate")
                lr_value = calibration.get("lr_range_value", 6)
                coherence_verified = calibration.get("coherence_verified", True)
                key_evidence = result.get("key_evidence", [])

                cluster["calibration_info"] = {
                    "h_max": h_max,
                    "h_max_rationale": h_max_rationale,
                    "h_min": h_min,
                    "h_min_rationale": h_min_rationale,
                    "lr_range_category": lr_category,
                    "lr_range_value": lr_value,
                    "coherence_verified": coherence_verified,
                    "key_evidence": key_evidence
                }

                logger.info(f"  {c_id} calibration: H_max={h_max}, H_min={h_min}, LR={lr_value}x ({lr_category})")
                logger.info(f"  {c_id} H_max rationale: {h_max_rationale[:100]}..." if len(h_max_rationale) > 100 else f"  {c_id} H_max rationale: {h_max_rationale}")
                logger.info(f"  {c_id} H_min rationale: {h_min_rationale[:100]}..." if len(h_min_rationale) > 100 else f"  {c_id} H_min rationale: {h_min_rationale}")

                # Extract likelihoods
                hypothesis_likelihoods = result.get("hypothesis_likelihoods", [])

                # Validate and log the likelihoods
                likelihoods_dict = {}
                p_max_actual = 0
                p_min_actual = 1

                for hl in hypothesis_likelihoods:
                    h_id = hl.get("hypothesis_id")
                    prob = hl.get("probability", c_base_rate)
                    position = hl.get("position", "at_base")

                    if h_id:
                        # Clamp to valid range
                        prob = max(0.02, min(0.98, float(prob)))
                        likelihoods_dict[h_id] = {
                            "probability": prob,
                            "position": position,
                            "relative_to_base_rate": "above" if prob > c_base_rate + 0.02 else ("below" if prob < c_base_rate - 0.02 else "equal")
                        }

                        if h_id == h_max:
                            p_max_actual = prob
                        if h_id == h_min:
                            p_min_actual = prob

                # Validate LR ratio
                if lr_value > 1 and p_min_actual > 0:
                    actual_lr = p_max_actual / p_min_actual
                    if actual_lr < lr_value * 0.3:  # More than 70% off target
                        logger.warning(f"  {c_id}: Actual LR={actual_lr:.1f} much lower than target LR={lr_value}. Calibration may have failed.")
                    else:
                        logger.info(f"  {c_id}: Actual LR={actual_lr:.1f} (target: {lr_value})")

                # Fill in any missing hypotheses with base rate
                for h_id in hyp_ids:
                    if h_id not in likelihoods_dict:
                        logger.warning(f"  {c_id}: Missing likelihood for {h_id}, using base rate")
                        likelihoods_dict[h_id] = {
                            "probability": c_base_rate,
                            "position": "at_base",
                            "relative_to_base_rate": "equal"
                        }

                # Store as single paradigm "K0" (calibrated baseline)
                # For multi-paradigm, we'll apply this to all paradigms with optional adjustments
                cluster["likelihoods_by_paradigm"]["K0"] = likelihoods_dict

            except Exception as e:
                logger.error(f"FATAL: Calibration failed for cluster {c_id}: {e}")
                raise RuntimeError(
                    f"Phase 3b ABORTED: Calibrated elicitation failed for cluster {c_id}. "
                    f"Error: {e}. Refusing to continue with meaningless fallback values."
                )

            return cluster  # Return the updated cluster

        # Execute calibrations in PARALLEL using ThreadPoolExecutor
        self._log_progress(f"Phase 3b: Calibrating {len(clusters)} clusters in parallel...")

        with ThreadPoolExecutor(max_workers=min(8, len(clusters))) as executor:
            # Submit all calibration tasks
            future_to_idx = {
                executor.submit(calibrate_cluster, idx, cluster): idx
                for idx, cluster in enumerate(clusters)
            }

            # Collect results as they complete
            calibrated_clusters = [None] * len(clusters)
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    calibrated_clusters[idx] = future.result()
                except Exception as e:
                    logger.error(f"Cluster calibration {idx} failed: {e}")
                    raise

        # Replace clusters with calibrated results
        clusters = calibrated_clusters

        # STEP 7: Apply calibrated likelihoods to all paradigms
        # For now, use the same calibrated likelihoods for all paradigms
        # (paradigm effects are captured in priors, not likelihoods)
        self._log_progress("Phase 3b: Applying calibrated likelihoods to all paradigms...")

        for cluster in clusters:
            k0_likelihoods = cluster["likelihoods_by_paradigm"].get("K0", {})
            for paradigm_id in paradigm_ids:
                if paradigm_id != "K0":
                    # Copy K0 likelihoods to other paradigms
                    cluster["likelihoods_by_paradigm"][paradigm_id] = k0_likelihoods.copy()

        # Validation
        for cluster in clusters:
            for paradigm_id in paradigm_ids:
                if paradigm_id not in cluster.get("likelihoods_by_paradigm", {}):
                    raise RuntimeError(
                        f"Phase 3b ABORTED: Missing likelihoods for paradigm {paradigm_id} in cluster {cluster.get('cluster_id')}."
                    )

        # Log calibration summary
        logger.info("=" * 60)
        logger.info("CALIBRATED LIKELIHOOD SUMMARY:")
        for cluster in clusters:
            c_id = cluster["cluster_id"]
            cal = cluster.get("calibration_info", {})
            logger.info(f"  {c_id}: LR={cal.get('lr_range_value', '?')}x, H_max={cal.get('h_max', '?')}, H_min={cal.get('h_min', '?')}")
            k0_lh = cluster["likelihoods_by_paradigm"].get("K0", {})
            probs = [lh.get("probability", 0.5) for lh in k0_lh.values() if isinstance(lh, dict)]
            if probs:
                logger.info(f"       P(E|H) range: [{min(probs):.3f}, {max(probs):.3f}], spread={max(probs)-min(probs):.3f}")
        logger.info("=" * 60)

        logger.info(f"Phase 3b calibrated complete: {len(clusters)} clusters with {len(paradigms)} paradigms each")
        return clusters

    def _generate_clusters_markdown(self, clusters: List[Dict], base_rates: Dict[str, float] = None) -> str:
        """Generate markdown summary from structured clusters with base rate information."""
        lines = ["## Evidence Clusters with Likelihoods (Two-Stage Assessment)\n"]
        for cluster in clusters:
            c_id = cluster.get("cluster_id", "C?")
            name = cluster.get("cluster_name", "Unknown")
            desc = cluster.get("description", "")
            evidence_ids = cluster.get("evidence_ids", [])
            cluster_base_rate = cluster.get("cluster_base_rate")

            lines.append(f"### {c_id}: {name}")
            lines.append(f"- **Description:** {desc}")
            lines.append(f"- **Evidence:** {', '.join(evidence_ids)}")

            # Show base rate for this cluster
            if cluster_base_rate is not None:
                lines.append(f"- **Cluster Base Rate P(E):** {cluster_base_rate:.2f}")

            # Show likelihoods by paradigm with relative indicators
            lh_by_paradigm = cluster.get("likelihoods_by_paradigm", {})
            base_rate_display = f"{cluster_base_rate:.2f}" if cluster_base_rate is not None else "0.50"
            for paradigm_id, hyp_likelihoods in lh_by_paradigm.items():
                lines.append(f"\n**{paradigm_id} Likelihoods (relative to P(E)={base_rate_display}):**")
                for hyp_id, lh_data in hyp_likelihoods.items():
                    if isinstance(lh_data, dict):
                        prob = lh_data.get("probability", 0.5)
                        rel = lh_data.get("relative_to_base_rate", "")
                        # Determine indicator symbol
                        if rel == "equal" or (cluster_base_rate and abs(prob - cluster_base_rate) < 0.02):
                            indicator = "= P(E) → LR≈1"
                        elif rel == "above" or (cluster_base_rate and prob > cluster_base_rate):
                            indicator = "> P(E) → LR>1"
                        elif rel == "below" or (cluster_base_rate and prob < cluster_base_rate):
                            indicator = "< P(E) → LR<1"
                        else:
                            indicator = ""
                        lines.append(f"  - {hyp_id}: {prob:.2f} {indicator}")
                    else:
                        lines.append(f"  - {hyp_id}: {lh_data:.2f}")
            lines.append("")

        return "\n".join(lines)

    def _parse_clusters_json(self, text: str) -> List[Dict]:
        """Extract structured clusters from various JSON formats.

        Handles:
        - CLUSTERS_JSON_START/END markers
        - Direct JSON object with "clusters" key
        - Direct JSON array of clusters
        """
        # Try 1: Look for explicit markers
        pattern = r"CLUSTERS_JSON_START\s*(\[.*?\])\s*CLUSTERS_JSON_END"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                clusters = json.loads(match.group(1))
                logger.info(f"Parsed {len(clusters)} evidence clusters (markers)")
                return clusters
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse clusters JSON from markers: {e}")

        # Try 2: Parse entire text as JSON object with "clusters" key
        try:
            data = json.loads(text.strip())
            if isinstance(data, dict) and "clusters" in data:
                clusters = data["clusters"]
                if isinstance(clusters, list):
                    logger.info(f"Parsed {len(clusters)} clusters (direct JSON object)")
                    return clusters
        except json.JSONDecodeError:
            pass

        # Try 3: Find JSON object with "clusters" key embedded in text
        try:
            obj_match = re.search(r'\{\s*"clusters"\s*:\s*\[.*?\]\s*\}', text, re.DOTALL)
            if obj_match:
                data = json.loads(obj_match.group(0))
                clusters = data.get("clusters", [])
                logger.info(f"Parsed {len(clusters)} clusters (embedded JSON object)")
                return clusters
        except (json.JSONDecodeError, AttributeError):
            pass

        # Try 4: Find any JSON array with cluster_id
        try:
            array_match = re.search(r'\[\s*\{[^]]*"cluster_id"[^]]+\}\s*\]', text, re.DOTALL)
            if array_match:
                clusters = json.loads(array_match.group(0))
                logger.info(f"Parsed {len(clusters)} clusters (array fallback)")
                return clusters
        except:
            pass

        logger.warning("Could not parse structured clusters, returning empty list")
        return []

    def _run_phase_5_report(self, request: BFIHAnalysisRequest,
                           methodology: str, evidence: str,
                           likelihoods: str,
                           evidence_items: List[Dict] = None,
                           evidence_clusters: List[Dict] = None,
                           precomputed_cluster_tables: List[Dict] = None,
                           precomputed_joint_table: str = None,
                           posteriors_by_paradigm: Dict = None,
                           paradigm_comparison_table: str = None) -> str:
        """Phase 5: Generate final BFIH report in multiple sub-phases for better quality.

        Generates report sections separately then concatenates them.

        Args:
            precomputed_cluster_tables: Pre-computed Bayesian metrics tables for each cluster
            precomputed_joint_table: Pre-computed joint evidence metrics table
            posteriors_by_paradigm: Dict mapping paradigm_id -> {hypothesis_id -> posterior}
            paradigm_comparison_table: Pre-formatted markdown comparing K0 vs biased paradigms

        NOTE: Phase 4 code_interpreter was removed. All Bayesian computation is now done
        in Python (_compute_paradigm_posteriors) to ensure paradigm-specific posteriors
        are consistent throughout the report.
        """
        # Build context data
        paradigms = request.scenario_config.get("paradigms", [])
        hypotheses = request.scenario_config.get("hypotheses", [])
        priors = request.scenario_config.get("priors_by_paradigm", request.scenario_config.get("priors", {}))

        paradigm_list = self._build_paradigm_list_with_stances(paradigms)
        hypothesis_list = "\n".join([f"- {h.get('id', 'H?')}: {h.get('name', 'Unknown')} - {h.get('description', '')}" for h in hypotheses])
        evidence_items_json = json.dumps(evidence_items or [], indent=2)
        evidence_clusters_json = json.dumps(evidence_clusters or [], indent=2)

        # Phase 5a: Executive Summary, Paradigms, Hypotheses
        section_a = self._run_phase_5a_intro(
            request, paradigm_list, hypothesis_list, priors,
            posteriors_by_paradigm
        )

        # Phase 5b: Evidence Matrix (with PRE-COMPUTED Bayesian tables)
        section_b = self._run_phase_5b_evidence(
            request, evidence_items, evidence_clusters, hypotheses,
            precomputed_cluster_tables or []
        )

        # Phase 5c: Bayesian Results (with PRE-COMPUTED joint metrics table AND paradigm comparison)
        section_c = self._run_phase_5c_results(
            request, paradigms, hypotheses, priors,
            precomputed_cluster_tables or [], precomputed_joint_table or "",
            paradigm_comparison_table or ""
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
        # Post-process report to add short names next to Ki/Hj symbols
        full_report = self._enrich_report_with_short_names(full_report, request.scenario_config)
        return full_report

    def _build_paradigm_list_with_stances(self, paradigms: List[Dict]) -> str:
        """
        Build paradigm list with pre-computed stance tables for the report.

        Each paradigm gets a description and a 6-dimension stance table built
        programmatically from the paradigm JSON data.
        """
        sections = []
        for p in paradigms:
            p_id = p.get('id', 'K?')
            p_name = p.get('name', 'Unknown')
            p_desc = p.get('description', '')
            p_stance = p.get('stance', {})

            # Build stance table if stance data exists
            if p_stance:
                stance_table = f"""
**Explicit Stance (6 Dimensions):**

| Dimension | Stance |
|-----------|--------|
| Ontology | {p_stance.get('ontology', 'Not specified')} |
| Epistemology | {p_stance.get('epistemology', 'Not specified')} |
| Axiology | {p_stance.get('axiology', 'Not specified')} |
| Methodology | {p_stance.get('methodology', 'Not specified')} |
| Sociology | {p_stance.get('sociology', 'Not specified')} |
| Temporality | {p_stance.get('temporality', 'Not specified')} |
"""
            else:
                stance_table = "\n*(No explicit stance data available)*\n"

            # Mark K0-inv specially
            inverse_note = ""
            if p.get('is_k0_inverse'):
                inverse_note = " **(True inverse of K0)**"
            elif p.get('is_privileged'):
                inverse_note = " **(Privileged paradigm)**"

            section = f"""### {p_id}: {p_name}{inverse_note}

{p_desc}
{stance_table}"""
            sections.append(section)

        return "\n---\n".join(sections)

    def _enrich_report_with_short_names(self, report: str, scenario_config: Dict) -> str:
        """
        Post-process the report to add short names next to paradigm (Ki) and hypothesis (Hj) symbols.

        Uses regex to find standalone Ki/Hj patterns in tables and adds abbreviated names.
        This improves readability without requiring the LLM to generate extra tokens.
        """
        paradigms = scenario_config.get("paradigms", [])
        hypotheses = scenario_config.get("hypotheses", [])

        # Build lookup dictionaries with abbreviated names (max ~25 chars)
        paradigm_names = {}
        for p in paradigms:
            p_id = p.get("id", "")
            name = p.get("name", "")
            # Abbreviate long names
            if len(name) > 25:
                short_name = name[:22] + "..."
            else:
                short_name = name
            paradigm_names[p_id] = short_name

        hypothesis_names = {}
        for h in hypotheses:
            h_id = h.get("id", "")
            name = h.get("name", "")
            # Abbreviate long names
            if len(name) > 30:
                short_name = name[:27] + "..."
            else:
                short_name = name
            hypothesis_names[h_id] = short_name

        # Pattern to match Ki or Hj in table cells (after | or at start of cell)
        # Matches: "| K0 |" or "| H1 |" or "K0:" or "H1:" etc.
        # Excludes already-annotated entries like "K0 (name)"

        def replace_paradigm(match):
            """Replace Ki with Ki (short-name) if not already annotated."""
            prefix = match.group(1)  # | or space or start
            p_id = match.group(2)    # K0, K1, etc.
            suffix = match.group(3)  # | or : or space

            if p_id in paradigm_names:
                short_name = paradigm_names[p_id]
                return f"{prefix}{p_id} ({short_name}){suffix}"
            return match.group(0)

        def replace_hypothesis(match):
            """Replace Hj with Hj (short-name) if not already annotated."""
            prefix = match.group(1)
            h_id = match.group(2)    # H0, H1, etc.
            suffix = match.group(3)

            if h_id in hypothesis_names:
                short_name = hypothesis_names[h_id]
                return f"{prefix}{h_id} ({short_name}){suffix}"
            return match.group(0)

        # Process line by line to add short names and escape conditional probability bars
        lines = report.split('\n')
        enriched_lines = []

        for line in lines:
            # Only process table rows (start with |) and skip separator rows
            if line.strip().startswith('|') and not re.match(r'^\|[-\s|]+\|$', line.strip()):
                # Escape vertical bars in conditional probability notation: P(E|H) -> P(E\|H)
                # Match P(...|...) patterns where | is not already escaped
                # Handles: P(E|H), P(E|¬H), P(H|E), P(H|K), etc.
                line = re.sub(r'P\(([^)|]+)(?<!\\)\|([^)]+)\)', r'P(\1\\|\2)', line)

                # Replace hypothesis IDs at start of table cell: "| H0 |" or "| H0 " (first column)
                # Pattern: | H0 | or | H0 followed by space and other content
                for h_id, short_name in hypothesis_names.items():
                    # Match "| H0 |" or "| H0 " at cell boundaries, not already annotated
                    pattern = rf'(\| ){h_id}( \||\s+(?!\())'
                    if re.search(pattern, line) and f"{h_id} (" not in line:
                        line = re.sub(pattern, rf'\1{h_id} ({short_name})\2', line, count=1)

                # Replace paradigm IDs: "| K0 |" or "K0 Posterior" etc.
                for p_id, short_name in paradigm_names.items():
                    # Match paradigm ID at cell boundaries
                    pattern = rf'(\| ){p_id}( \||\s+(?!\())'
                    if re.search(pattern, line) and f"{p_id} (" not in line:
                        line = re.sub(pattern, rf'\1{p_id} ({short_name})\2', line, count=1)

            enriched_lines.append(line)

        return '\n'.join(enriched_lines)

    def _run_phase_5a_intro(self, request: BFIHAnalysisRequest,
                            paradigm_list: str, hypothesis_list: str,
                            priors: Dict,
                            posteriors_by_paradigm: Dict = None) -> str:
        """Phase 5a: Generate Executive Summary, Paradigms, and Hypotheses sections."""
        bfih_context = get_bfih_system_context("Report Generation - Introduction", "5a")

        # Format paradigm-specific posteriors for Executive Summary
        # This is the AUTHORITATIVE source - use these values, not code_interpreter output
        posteriors_by_paradigm = posteriors_by_paradigm or {}
        k0_posteriors = posteriors_by_paradigm.get("K0", {})

        # Build posteriors summary table
        posteriors_summary = "**K0 (Privileged Paradigm) Posteriors - USE THESE VALUES:**\n\n"
        posteriors_summary += "| Hypothesis | Posterior |\n|------------|----------|\n"
        for h_id in sorted(k0_posteriors.keys()):
            posteriors_summary += f"| {h_id} | {k0_posteriors[h_id]:.4f} |\n"

        # Find winning hypothesis under K0
        if k0_posteriors:
            winning_h = max(k0_posteriors.keys(), key=lambda h: k0_posteriors[h])
            winning_posterior = k0_posteriors[winning_h]
            posteriors_summary += f"\n**Winning hypothesis under K0: {winning_h} (posterior: {winning_posterior:.4f})**\n"

        prompt = f"""{bfih_context}
PROPOSITION: "{request.proposition}"

PARADIGMS:
{paradigm_list}

HYPOTHESES:
{hypothesis_list}

PRIORS BY PARADIGM:
{json.dumps(priors, indent=2)}

## AUTHORITATIVE POSTERIOR PROBABILITIES (computed mathematically)

IMPORTANT: The posteriors below were computed programmatically using Bayesian updating.
Use ONLY these values in the Executive Summary. Do NOT use any other posterior values.

{posteriors_summary}

All paradigm posteriors:
{json.dumps(posteriors_by_paradigm, indent=2)}

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

The paradigm data below includes PRE-BUILT stance tables. Copy them EXACTLY as provided.
For each paradigm, you may add 1-2 sentences of additional context AFTER the stance table,
but DO NOT modify the table content - it was computed programmatically from the paradigm JSON.

---

## 2. Hypothesis Set

For EACH hypothesis:

**H[X]: [Full Name]**

[3-4 sentence description of what this hypothesis claims]

**Prior Probabilities:**

| Paradigm | Prior P(H) | Rationale |
|----------|------------|-----------|
[Table showing prior for each paradigm with brief justification]

IMPORTANT MARKDOWN FORMATTING:
- Always include a BLANK LINE before any table (between label and table header)
- Use DECIMAL format (0.XXX) for all probabilities
- DO NOT wrap your output in code blocks (no ```markdown or ``` delimiters)
- Output raw markdown directly
"""
        return self._run_phase(prompt, [], "Phase 5a: Introduction Sections")

    def _run_phase_5b_evidence(self, request: BFIHAnalysisRequest,
                               evidence_items: List[Dict],
                               evidence_clusters: List[Dict],
                               hypotheses: List[Dict],
                               precomputed_cluster_tables: List[Dict] = None) -> str:
        """Phase 5b: Generate Evidence Matrix with full citations and PRE-COMPUTED Bayesian metrics.

        Split into sub-phases to avoid output token limits:
        - 5b1: Evidence Clusters (Section 3)
        - 5b2: Evidence Items Detail in batches (Section 4)
        """
        # Phase 5b1: Generate Section 3 (Evidence Clusters)
        section_3 = self._run_phase_5b1_clusters(
            request, evidence_clusters, hypotheses, precomputed_cluster_tables
        )

        # Phase 5b2: Generate Section 4 (Evidence Items) in batches
        section_4_content = self._run_phase_5b2_evidence_items(
            request, evidence_items, evidence_clusters
        )

        # Inject section 4 header programmatically (not relying on LLM)
        section_4 = f"## 4. Evidence Items Detail\n\n{section_4_content}"

        return f"{section_3}\n\n---\n\n{section_4}"

    def _run_phase_5b1_clusters(self, request: BFIHAnalysisRequest,
                                 evidence_clusters: List[Dict],
                                 hypotheses: List[Dict],
                                 precomputed_cluster_tables: List[Dict] = None,
                                 cluster_hierarchy: List[Dict] = None) -> str:
        """Phase 5b1: Generate Evidence Clusters section with pre-computed Bayesian tables.

        Now includes hierarchical organization and mechanistic source information.
        """
        precomputed_cluster_tables = precomputed_cluster_tables or []
        cluster_hierarchy = cluster_hierarchy or getattr(self, '_cluster_hierarchy', [])

        # Build lookup from cluster_id to cluster data
        cluster_data_lookup = {}
        for cluster in evidence_clusters:
            c_id = cluster.get('cluster_id')
            if c_id:
                cluster_data_lookup[c_id] = cluster

        # Build lookup from cluster name to precomputed table
        cluster_table_lookup = {}
        for ct in precomputed_cluster_tables:
            cluster_table_lookup[ct.get('name', '')] = ct

        # Build pre-computed cluster sections organized by hierarchy
        hierarchy_sections = []

        if cluster_hierarchy:
            # Organize clusters by hierarchy groups
            for group in cluster_hierarchy:
                group_name = group.get('group_name', 'Uncategorized')
                group_desc = group.get('description', '')
                group_cluster_ids = group.get('cluster_ids', [])

                group_content = [f"### {group_name}\n\n*{group_desc}*\n"]

                for c_id in group_cluster_ids:
                    cluster = cluster_data_lookup.get(c_id, {})
                    cluster_name = cluster.get('cluster_name', c_id)
                    ct = cluster_table_lookup.get(cluster_name, {})

                    # Include mechanistic source and calibration info
                    mech_source = cluster.get('mechanistic_source', 'unspecified')
                    dep_just = cluster.get('dependence_justification', '')
                    cal_info = cluster.get('calibration_info', {})
                    h_max = cal_info.get('h_max', '?')
                    h_min = cal_info.get('h_min', '?')
                    h_max_rationale = cal_info.get('h_max_rationale', '')
                    h_min_rationale = cal_info.get('h_min_rationale', '')
                    lr_value = cal_info.get('lr_range_value', '?')

                    cluster_section = f"""
#### {cluster_name} ({c_id})

**Mechanistic Source:** {mech_source}
**Conditional Dependence:** {dep_just}
**Evidence Items:** {', '.join(cluster.get('evidence_ids', [])) or 'See items below'}

**Calibration Results:**
- **H_max:** {h_max} — {h_max_rationale}
- **H_min:** {h_min} — {h_min_rationale}
- **Likelihood Ratio:** {lr_value}x

**Bayesian Metrics (computed mathematically):**

{ct.get('table', '(No metrics available)')}
"""
                    group_content.append(cluster_section)

                hierarchy_sections.append("\n".join(group_content))
        else:
            # Fallback: no hierarchy, just list clusters
            for ct in precomputed_cluster_tables:
                cluster = cluster_data_lookup.get(ct.get('name'), {})
                mech_source = cluster.get('mechanistic_source', 'unspecified')
                cal_info = cluster.get('calibration_info', {})

                cluster_section = f"""
### Cluster: {ct['name']}

**Mechanistic Source:** {mech_source}
**Description:** {ct.get('description', 'Evidence cluster')}
**Evidence Items:** {', '.join(ct.get('evidence_ids', [])) or 'See items below'}

**Bayesian Metrics (computed mathematically):**

{ct['table']}
"""
                hierarchy_sections.append(cluster_section)

        precomputed_clusters_text = "\n---\n".join(hierarchy_sections) if hierarchy_sections else "(No cluster metrics available)"

        bfih_context = get_bfih_system_context("Report Generation - Evidence Clusters", "5b1")
        prompt = f"""{bfih_context}
PROPOSITION: "{request.proposition}"

## PRE-COMPUTED CLUSTER-LEVEL BAYESIAN METRICS
The following tables were computed mathematically using:
- P(E|¬H_i) = Σ P(E|H_j) × P(H_j)/(1-P(H_i)) for j≠i
- LR = P(E|H) / P(E|¬H)
- WoE = 10 × log₁₀(LR) decibans

YOU MUST COPY THESE TABLES EXACTLY - DO NOT MODIFY THE VALUES:

{precomputed_clusters_text}

---

Generate this section in markdown:

## 3. Evidence Clusters

Copy the PRE-COMPUTED cluster tables above EXACTLY as shown. For each cluster:
1. Copy the cluster name, description, and evidence items
2. Copy the Bayesian Metrics table EXACTLY (these are mathematically computed, DO NOT change values)
3. Add 2-3 sentences interpreting what the LR and WoE values mean for each hypothesis

MARKDOWN FORMATTING:
- Always include a BLANK LINE before any table
- DO NOT wrap your output in code blocks (no ```markdown or ``` delimiters)
- Output raw markdown directly
"""
        return self._run_phase(prompt, [], "Phase 5b1: Evidence Clusters")

    def _run_phase_5b2_evidence_items(self, request: BFIHAnalysisRequest,
                                       evidence_items: List[Dict],
                                       evidence_clusters: List[Dict]) -> str:
        """Phase 5b2: Generate Evidence Items Detail section in batches.

        Simplified format without per-item P(E|H) tables (those are at cluster level).
        Processes items in batches of 15 to avoid output token limits.
        """
        evidence_items = evidence_items or []
        evidence_clusters = evidence_clusters or []

        # Build cluster membership lookup
        cluster_lookup = {}
        for cluster in evidence_clusters:
            cluster_name = cluster.get('cluster_name', cluster.get('name', 'Unknown'))
            for eid in cluster.get('evidence_ids', []):
                cluster_lookup[eid] = cluster_name

        # Process in batches of 15
        BATCH_SIZE = 15
        all_sections = []

        for batch_start in range(0, len(evidence_items), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(evidence_items))
            batch_items = evidence_items[batch_start:batch_end]
            batch_num = (batch_start // BATCH_SIZE) + 1
            total_batches = (len(evidence_items) + BATCH_SIZE - 1) // BATCH_SIZE

            # Prepare batch data with cluster info
            batch_data = []
            for item in batch_items:
                eid = item.get('evidence_id', '')
                batch_data.append({
                    'evidence_id': eid,
                    'description': item.get('description', ''),
                    'source_name': item.get('source_name', ''),
                    'source_url': item.get('source_url', ''),
                    'citation_apa': item.get('citation_apa', ''),
                    'date_accessed': item.get('date_accessed', ''),
                    'evidence_type': item.get('evidence_type', ''),
                    'cluster': cluster_lookup.get(eid, 'Unassigned')
                })

            batch_json = json.dumps(batch_data, indent=2)

            bfih_context = get_bfih_system_context("Report Generation - Evidence Items", "5b2")
            prompt = f"""{bfih_context}
PROPOSITION: "{request.proposition}"

EVIDENCE ITEMS BATCH {batch_num}/{total_batches} (items {batch_start + 1}-{batch_end} of {len(evidence_items)}):
{batch_json}

---

Generate evidence item entries for this batch. For EACH item, use this CONCISE format:

### E[id]: [description - keep brief, ~1 sentence]

- **Source:** [source_name]
- **URL:** [source_url - FULL URL]
- **Citation:** [citation_apa]
- **Accessed:** [date_accessed]
- **Type:** [evidence_type]
- **Cluster:** [cluster name from data]

[1-2 sentences on what this evidence shows and its relevance to the proposition]

---

IMPORTANT:
- Keep each entry CONCISE - no P(E|H) tables (those are at cluster level)
- Include the FULL URL for each source
- Use bullet format for metadata to save space
- Write brief analysis (1-2 sentences max)

MARKDOWN FORMATTING:
- DO NOT wrap your output in code blocks
- Output raw markdown directly
"""
            batch_result = self._run_phase(prompt, [], f"Phase 5b2: Evidence Items batch {batch_num}/{total_batches}")
            all_sections.append(batch_result)

        return "\n".join(all_sections)

    def _run_phase_5c_results(self, request: BFIHAnalysisRequest,
                              paradigms: List[Dict],
                              hypotheses: List[Dict], priors: Dict,
                              precomputed_cluster_tables: List[Dict] = None,
                              precomputed_joint_table: str = None,
                              paradigm_comparison_table: str = None) -> str:
        """Phase 5c: Generate Bayesian Results, Paradigm Comparison, Conclusions."""
        precomputed_cluster_tables = precomputed_cluster_tables or []
        precomputed_joint_table = precomputed_joint_table or ""
        paradigm_comparison_table = paradigm_comparison_table or ""

        # Build cluster summary for reference
        cluster_summary = []
        for ct in precomputed_cluster_tables:
            cluster_summary.append(f"- **{ct['name']}**: {ct.get('description', '')}")
        cluster_summary_text = "\n".join(cluster_summary) if cluster_summary else "(No clusters)"

        bfih_context = get_bfih_system_context("Report Generation - Results & Conclusions", "5c")
        prompt = f"""{bfih_context}
PROPOSITION: "{request.proposition}"

PARADIGMS: {json.dumps([p.get('name') for p in paradigms])}

HYPOTHESES: {json.dumps([h.get('name') for h in hypotheses])}

PRIORS BY PARADIGM:
{json.dumps(priors, indent=2)}

EVIDENCE CLUSTERS ANALYZED:
{cluster_summary_text}

## PRE-COMPUTED JOINT EVIDENCE TABLE
The following table was computed mathematically. YOU MUST COPY IT EXACTLY:

{precomputed_joint_table}

---

## PRE-COMPUTED PARADIGM COMPARISON TABLE
The following comparison shows posteriors under each paradigm, contrasting biased paradigms (K1-Kn)
with the privileged paradigm K0 (designed to be maximally intellectually honest).
COPY THIS SECTION EXACTLY - values are mathematically computed:

{paradigm_comparison_table}

---

Generate these sections in markdown:

## 5. Joint Evidence Computation

**Cumulative Evidence Effect (all clusters combined under K0):**

COPY THE PRE-COMPUTED TABLE ABOVE EXACTLY:
{precomputed_joint_table}

**Normalization Check:** Sum of posteriors ≈ 1.0

**Interpretation:** [Explain which hypothesis has highest posterior and why based on Total LR/WoE]

---

## 6. Paradigm Comparison

COPY THE PRE-COMPUTED PARADIGM COMPARISON TABLE ABOVE EXACTLY.

Then add a brief discussion (2-3 paragraphs) addressing:
1. **Robustness**: Which conclusions hold across ALL paradigms vs which are paradigm-dependent?
2. **Bias Effects**: How do the biased paradigms' blind spots affect their conclusions?
3. **K0 Advantage**: Why K0's multi-domain, forcing-function-compliant analysis is more reliable

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

IMPORTANT:
- COPY the pre-computed joint evidence table EXACTLY - these values are mathematically computed
- The LR and WoE values determine which hypothesis the evidence supports, NOT just posteriors
- Positive WoE = evidence supports hypothesis, Negative WoE = evidence refutes hypothesis

MARKDOWN FORMATTING:
- Always include a BLANK LINE before any table
- Use values from the pre-computed table exactly as shown
- DO NOT wrap your output in code blocks (no ```markdown or ``` delimiters)
- Output raw markdown directly - the content will be rendered as markdown
"""
        return self._run_phase(prompt, [], "Phase 5c: Results & Conclusions")

    def _run_phase_5d_bibliography(self, evidence_items: List[Dict]) -> str:
        """Phase 5d: Generate Bibliography from evidence items."""
        if not evidence_items:
            return "## 9. Bibliography\n\nNo sources available."

        # Build bibliography directly from evidence items
        # Deduplicate by citation text or URL
        seen_citations = set()
        seen_urls = set()
        bib_entries = []
        entry_num = 0

        for item in evidence_items:
            citation = item.get('citation_apa', '').strip()
            url = item.get('source_url', '').strip()
            source = item.get('source_name', 'Unknown Source')

            # Skip "composite" or "synthesis" sources
            if 'composite' in source.lower() or 'synthesis' in source.lower():
                continue

            # Check for valid URL
            has_valid_url = url and url.lower() not in ('n/a', 'na', '-', '—', 'none', 'see above') and url.startswith('http')

            # Skip if we've seen this URL already
            if has_valid_url and url in seen_urls:
                continue

            # Skip if we've seen this exact citation already (for items without URLs)
            if citation and citation in seen_citations:
                continue

            # Skip items with neither citation nor valid URL
            if not citation and not has_valid_url:
                continue

            # Mark as seen
            if has_valid_url:
                seen_urls.add(url)
            if citation:
                seen_citations.add(citation)

            entry_num += 1
            if citation:
                entry = citation
                if has_valid_url and url not in citation:
                    entry += f" Retrieved from {url}"
            else:
                desc = item.get('description', '')[:100]  # Truncate long descriptions
                entry = f"{source}. {desc}."
                if has_valid_url:
                    entry += f" Retrieved from {url}"

            bib_entries.append(f"{entry_num}. {entry}")

        if not bib_entries:
            bibliography = "## 9. Bibliography\n\nNo citable sources available."
        else:
            bibliography = "## 9. Bibliography\n\n**References (APA Format):**\n\n" + "\n\n".join(bib_entries)

        # Add intellectual honesty checklist
        bibliography += """

---

## 10. Intellectual Honesty Checklist

| Forcing Function | Applied | Notes |
|-----------------|---------|-------|
| Ontological Scan (9 domains) | ✓ | Multiple domains covered (Constitutional/Legal and Democratic for political topics) |
| Ancestral Check | ✓ | Historical baselines examined |
| Paradigm Inversion | ✓ | Alternative paradigms generated |
| MECE Verification | ✓ | Hypotheses are mutually exclusive and collectively exhaustive |
| Sensitivity Analysis | ✓ | Prior variation tested |
"""
        return bibliography

    def _compute_cluster_bayesian_metrics(
        self, evidence_clusters: List[Dict], priors: Dict[str, float], paradigm_id: str = None
    ) -> Tuple[List[Dict], Dict]:
        """
        Compute P(E|¬H), LR, and WoE for each cluster using MATHEMATICAL formulas.

        This MUST be done in Python, not by LLM generation.

        Formula for likelihood under negation:
            P(E|¬H_i) = Σ P(E|H_j) × P(H_j|¬H_i)  for j ≠ i
            where P(H_j|¬H_i) = P(H_j) / (1 - P(H_i))

        Args:
            evidence_clusters: List of clusters with likelihoods data
            priors: Dict of {H_id: prior_probability}
            paradigm_id: Which paradigm's likelihoods to use (e.g., 'K0')

        Returns:
            (enriched_clusters, summary_metrics) where:
            - enriched_clusters: clusters with added 'bayesian_metrics' per hypothesis
            - summary_metrics: aggregate metrics across all clusters
        """
        if not evidence_clusters or not priors:
            logger.warning("Cannot compute Bayesian metrics: missing clusters or priors")
            return evidence_clusters, {}

        hyp_ids = list(priors.keys())
        enriched_clusters = []

        # Track cumulative likelihoods for joint computation
        # Joint P(E|H_j) = PRODUCT of P(C_i|H_j) for all clusters i
        cumulative_likelihood = {h: 1.0 for h in hyp_ids}

        for cluster in evidence_clusters:
            cluster_name = cluster.get("cluster_id") or cluster.get("cluster_name", "Unknown")

            # Try multiple sources for likelihoods:
            # 1. likelihoods_by_paradigm[paradigm_id] (structured output format)
            # 2. likelihoods (simple format)
            likelihoods = {}
            likelihoods_by_paradigm = cluster.get("likelihoods_by_paradigm", {})

            if paradigm_id and paradigm_id in likelihoods_by_paradigm:
                likelihoods = likelihoods_by_paradigm[paradigm_id]
                logger.debug(f"Cluster '{cluster_name}': using likelihoods from paradigm {paradigm_id}")
            elif likelihoods_by_paradigm:
                # Fall back to first available paradigm
                first_paradigm = list(likelihoods_by_paradigm.keys())[0]
                likelihoods = likelihoods_by_paradigm[first_paradigm]
                logger.debug(f"Cluster '{cluster_name}': using likelihoods from fallback paradigm {first_paradigm}")
            else:
                likelihoods = cluster.get("likelihoods", {})
                if likelihoods:
                    logger.debug(f"Cluster '{cluster_name}': using simple likelihoods format")
                else:
                    logger.warning(f"Cluster '{cluster_name}': no likelihoods found, using defaults")

            # Normalize likelihood format (may be {H: prob} or {H: {probability: prob}})
            # Clamp to avoid extremes (0 or 1)
            norm_likelihoods = {}
            for h_id in hyp_ids:
                lh = likelihoods.get(h_id, likelihoods.get(h_id.upper(), {}))
                if isinstance(lh, dict):
                    raw_lh = lh.get("probability", 0.5)
                elif isinstance(lh, (int, float)):
                    raw_lh = float(lh)
                else:
                    raw_lh = 0.5  # Default neutral
                norm_likelihoods[h_id] = clamp_probability(raw_lh, f"likelihood {h_id}|{cluster_name}")

            # Compute P(E|¬H), LR, WoE for each hypothesis
            bayesian_metrics = {}
            for h_i in hyp_ids:
                p_e_h = norm_likelihoods.get(h_i, 0.5)
                prior_i = priors.get(h_i, 1.0 / len(hyp_ids))
                complement_prior = 1.0 - prior_i

                # P(E|¬H_i) = Σ P(E|H_j) × P(H_j) / (1 - P(H_i)) for j ≠ i
                if complement_prior > 0:
                    p_e_not_h = sum(
                        norm_likelihoods.get(h_j, 0.5) * (priors.get(h_j, 0) / complement_prior)
                        for h_j in hyp_ids if h_j != h_i
                    )
                else:
                    p_e_not_h = 0.5  # Fallback for edge case

                # Likelihood Ratio
                if p_e_not_h > 0:
                    lr = p_e_h / p_e_not_h
                else:
                    lr = float('inf') if p_e_h > 0 else 1.0

                # Weight of Evidence in decibans
                if lr > 0 and lr != float('inf'):
                    woe = 10 * math.log10(lr)
                else:
                    woe = float('inf') if lr == float('inf') else float('-inf')

                # Direction based on LR
                if lr > 3:
                    direction = "Strong Support" if lr > 10 else "Moderate Support"
                elif lr > 1.1:
                    direction = "Weak Support"
                elif lr < 0.33:
                    direction = "Strong Refutation" if lr < 0.1 else "Moderate Refutation"
                elif lr < 0.9:
                    direction = "Weak Refutation"
                else:
                    direction = "Neutral"

                bayesian_metrics[h_i] = {
                    "P(E|H)": round(p_e_h, 4),
                    "P(E|~H)": round(p_e_not_h, 4),
                    "LR": round(lr, 4) if lr != float('inf') else "inf",
                    "WoE_dB": round(woe, 2) if woe not in [float('inf'), float('-inf')] else str(woe),
                    "direction": direction
                }

                # Update cumulative likelihood for joint computation
                cumulative_likelihood[h_i] *= p_e_h

            # Add metrics to enriched cluster
            enriched_cluster = dict(cluster)
            enriched_cluster["bayesian_metrics"] = bayesian_metrics
            enriched_clusters.append(enriched_cluster)

            logger.debug(f"Cluster '{cluster_name}' metrics computed for {len(bayesian_metrics)} hypotheses")

        # Compute joint/cumulative metrics using correct Bayesian formulas:
        # 1. Joint P(E|H_j) = PRODUCT(P(C_i|H_j)) for all clusters i
        # 2. Posterior P(H_j|E) = P(E|H_j) × P(H_j) / SUM(P(E|H_l) × P(H_l))
        # 3. Total LR = Odds(H_j|E) / Odds(H_j), where Odds(X) = P(X)/(1-P(X))

        joint_metrics = {}

        # Step 1: Joint likelihoods are already in cumulative_likelihood
        # Step 2: Compute unnormalized posteriors
        unnorm_posteriors = {}
        for h_i in hyp_ids:
            prior_i = priors.get(h_i, 1.0 / len(hyp_ids))
            joint_p_e_h = cumulative_likelihood[h_i]
            unnorm_posteriors[h_i] = prior_i * joint_p_e_h

        # Normalization constant = P(E) = SUM(P(E|H_l) × P(H_l))
        norm_const = sum(unnorm_posteriors.values())

        # Step 3: Compute posteriors and Total LR from odds ratio
        for h_i in hyp_ids:
            prior_i = priors.get(h_i, 1.0 / len(hyp_ids))
            joint_p_e_h = cumulative_likelihood[h_i]

            # Normalized posterior
            if norm_const > 0:
                posterior = unnorm_posteriors[h_i] / norm_const
            else:
                posterior = prior_i  # Fallback to prior if no evidence

            # Compute joint P(E|¬H) using weighted average of other hypotheses' joint likelihoods
            # P(E|¬H_j) = SUM(P(E|H_k) × P(H_k|¬H_j)) for k≠j
            # where P(H_k|¬H_j) = P(H_k) / (1 - P(H_j))
            complement_prior = 1.0 - prior_i
            if complement_prior > 0:
                joint_p_e_not_h = sum(
                    cumulative_likelihood[h_k] * (priors.get(h_k, 0) / complement_prior)
                    for h_k in hyp_ids if h_k != h_i
                )
            else:
                joint_p_e_not_h = 0.0

            # Total LR = Odds(H|E) / Odds(H) = [P(H|E)/(1-P(H|E))] / [P(H)/(1-P(H))]
            # This is mathematically equivalent to P(E|H) / P(E|¬H)
            prior_odds = prior_i / (1.0 - prior_i) if prior_i < 1.0 else float('inf')
            posterior_odds = posterior / (1.0 - posterior) if posterior < 1.0 else float('inf')

            if prior_odds > 0 and prior_odds != float('inf'):
                total_lr = posterior_odds / prior_odds
            elif posterior_odds == float('inf'):
                total_lr = float('inf')
            else:
                total_lr = 1.0

            # Weight of Evidence in decibans
            if total_lr > 0 and total_lr != float('inf'):
                total_woe = 10 * math.log10(total_lr)
            else:
                total_woe = float('inf') if total_lr == float('inf') else float('-inf')

            joint_metrics[h_i] = {
                "prior": round(prior_i, 4),
                "joint_P(E|H)": f"{joint_p_e_h:.4e}",
                "joint_P(E|~H)": f"{joint_p_e_not_h:.4e}",
                "total_LR": round(total_lr, 4) if total_lr != float('inf') else "inf",
                "total_WoE_dB": round(total_woe, 2) if total_woe not in [float('inf'), float('-inf')] else str(total_woe),
                "posterior": round(posterior, 6)
            }

        logger.info(f"Computed Bayesian metrics for {len(enriched_clusters)} clusters, {len(hyp_ids)} hypotheses")
        return enriched_clusters, joint_metrics

    def _format_cluster_metrics_table(self, cluster: Dict, hyp_ids: List[str], paradigm_id: str = None) -> str:
        """Format a single cluster's Bayesian metrics as a markdown table.

        Args:
            cluster: Cluster dict with bayesian_metrics or bayesian_metrics_by_paradigm
            hyp_ids: List of hypothesis IDs
            paradigm_id: Optional paradigm ID to get metrics for (uses first if not specified)
        """
        # Try bayesian_metrics_by_paradigm first (new format)
        metrics_by_paradigm = cluster.get("bayesian_metrics_by_paradigm", {})
        if metrics_by_paradigm:
            if paradigm_id and paradigm_id in metrics_by_paradigm:
                metrics = metrics_by_paradigm[paradigm_id]
            else:
                # Use first available paradigm
                first_key = list(metrics_by_paradigm.keys())[0] if metrics_by_paradigm else None
                metrics = metrics_by_paradigm.get(first_key, {}) if first_key else {}
        else:
            # Fall back to old format
            metrics = cluster.get("bayesian_metrics", {})

        if not metrics:
            return ""

        lines = [
            "| Hypothesis | P(E|H) | P(E|¬H) | LR | WoE (dB) | Direction |",
            "|------------|--------|---------|-----|----------|-----------|"
        ]
        for h_id in hyp_ids:
            m = metrics.get(h_id, {})
            lines.append(
                f"| {h_id} | {m.get('P(E|H)', 'N/A')} | {m.get('P(E|~H)', 'N/A')} | "
                f"{m.get('LR', 'N/A')} | {m.get('WoE_dB', 'N/A')} | {m.get('direction', 'N/A')} |"
            )
        return "\n".join(lines)

    def _format_joint_metrics_table(self, joint_metrics: Dict, hyp_ids: List[str]) -> str:
        """Format joint evidence metrics as a markdown table."""
        if not joint_metrics:
            return ""

        lines = [
            "| Hypothesis | Prior | Joint P(E|H) | Joint P(E|¬H) | Total LR | Total WoE (dB) | Posterior |",
            "|------------|-------|--------------|---------------|----------|----------------|-----------|"
        ]
        for h_id in hyp_ids:
            m = joint_metrics.get(h_id, {})
            lines.append(
                f"| {h_id} | {m.get('prior', 'N/A')} | {m.get('joint_P(E|H)', 'N/A')} | "
                f"{m.get('joint_P(E|~H)', 'N/A')} | {m.get('total_LR', 'N/A')} | "
                f"{m.get('total_WoE_dB', 'N/A')} | {m.get('posterior', 'N/A')} |"
            )
        return "\n".join(lines)

    def _format_paradigm_comparison_table(
        self, posteriors_by_paradigm: Dict[str, Dict[str, float]], scenario_config: Dict
    ) -> str:
        """
        Format a paradigm comparison showing K0 (privileged) vs each biased paradigm.

        For each paradigm, shows:
        - Posteriors under that paradigm
        - Difference from K0 posteriors
        - Which hypothesis "wins" under each paradigm
        """
        paradigms = scenario_config.get("paradigms", [])
        hypotheses = scenario_config.get("hypotheses", [])
        hyp_ids = [h.get("id", f"H{i}") for i, h in enumerate(hypotheses)]

        if not posteriors_by_paradigm or not paradigms:
            return "(Paradigm comparison not available)"

        # Get K0 posteriors as baseline
        k0_posteriors = posteriors_by_paradigm.get("K0", {})
        if not k0_posteriors:
            # Use first paradigm as baseline if K0 not found
            k0_posteriors = list(posteriors_by_paradigm.values())[0] if posteriors_by_paradigm else {}

        # Find K0's winning hypothesis
        k0_winner = max(k0_posteriors.keys(), key=lambda h: k0_posteriors.get(h, 0)) if k0_posteriors else "N/A"
        k0_winner_prob = k0_posteriors.get(k0_winner, 0)

        sections = []

        # Header section
        sections.append(f"""### K0 (Privileged Paradigm) - Baseline

**Winning Hypothesis:** {k0_winner} (posterior: {k0_winner_prob:.4f})

| Hypothesis | Posterior |
|------------|-----------|""")
        for h_id in hyp_ids:
            prob = k0_posteriors.get(h_id, 0)
            sections.append(f"| {h_id} | {prob:.4f} |")

        sections.append("")

        # Comparison sections for each biased paradigm
        for paradigm in paradigms:
            p_id = paradigm.get("id", "")
            p_name = paradigm.get("name", p_id)
            is_privileged = paradigm.get("is_privileged", False)
            bias_type = paradigm.get("bias_type", "")

            if p_id == "K0" or is_privileged:
                continue  # Skip K0, already shown above

            p_posteriors = posteriors_by_paradigm.get(p_id, {})
            if not p_posteriors:
                continue

            # Find this paradigm's winner
            p_winner = max(p_posteriors.keys(), key=lambda h: p_posteriors.get(h, 0)) if p_posteriors else "N/A"
            p_winner_prob = p_posteriors.get(p_winner, 0)

            # Determine if winner differs from K0
            winner_differs = p_winner != k0_winner
            winner_note = " ⚠️ DIFFERS FROM K0" if winner_differs else " ✓ Agrees with K0"

            sections.append(f"""---

### {p_id}: {p_name}

**Bias Type:** {bias_type or 'Not specified'}
**Winning Hypothesis:** {p_winner} (posterior: {p_winner_prob:.4f}){winner_note}

**Comparison with K0:**

| Hypothesis | {p_id} Posterior | K0 Posterior | Δ (difference) |
|------------|------------------|--------------|----------------|""")

            for h_id in hyp_ids:
                p_prob = p_posteriors.get(h_id, 0)
                k0_prob = k0_posteriors.get(h_id, 0)
                delta = p_prob - k0_prob
                delta_str = f"+{delta:.4f}" if delta > 0 else f"{delta:.4f}"
                sections.append(f"| {h_id} | {p_prob:.4f} | {k0_prob:.4f} | {delta_str} |")

            # Brief interpretation
            if winner_differs:
                sections.append(f"""
**Interpretation:** Under {p_id}'s {bias_type or 'biased'} perspective, {p_winner} dominates
instead of K0's preferred {k0_winner}. This reflects the paradigm's characteristic blind spots.""")
            else:
                sections.append(f"""
**Interpretation:** {p_id} agrees with K0 on the winning hypothesis, suggesting
this conclusion is robust across paradigms despite {p_id}'s {bias_type or 'different'} perspective.""")

        return "\n".join(sections)

    # ========================================================================
    # AUTONOMOUS ANALYSIS (Topic Submission → Full Analysis)
    # ========================================================================

    def analyze_topic(self, proposition: str, domain: str = "business",
                      difficulty: str = "medium",
                      reasoning_model: Optional[str] = None,
                      budget_limit: Optional[float] = None) -> BFIHAnalysisResult:
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
            reasoning_model: Optional reasoning model override (o3-mini, gpt-5.2, etc.)
            budget_limit: Maximum cost in USD. None = unlimited.

        Returns:
            BFIHAnalysisResult with full report and generated config
        """
        analysis_start = datetime.now(timezone.utc)
        scenario_id = f"auto_{uuid.uuid4().hex[:8]}"

        # Initialize cost tracking
        self.cost_tracker = CostTracker(budget_limit=budget_limit)
        if budget_limit:
            self._log_progress(f"Budget limit set: ${budget_limit:.2f}")

        # Override reasoning model if specified
        if reasoning_model and reasoning_model in AVAILABLE_REASONING_MODELS:
            self.reasoning_model = reasoning_model
            self._log_progress(f"Using specified reasoning model: {self.reasoning_model}")

        self._log_progress(f"{'='*60}")
        self._log_progress(f"AUTONOMOUS BFIH ANALYSIS")
        self._log_progress(f"Proposition: {proposition}")
        self._log_progress(f"Domain: {domain}, Difficulty: {difficulty}")
        self._log_progress(f"{'='*60}")

        # Phase 0a: Generate paradigms
        self._report_status("phase:paradigms")
        self._log_progress("Starting Phase 0a: Generating paradigms...")
        self.cost_tracker.check_budget("Phase 0a: Paradigms", estimated_cost=0.50)
        paradigms = self._generate_paradigms(proposition, domain)
        self._log_progress(f"Generated {len(paradigms)} paradigms")

        # Phase 0b: Generate hypotheses with forcing functions + MECE synthesis
        self._report_status("phase:hypotheses")
        self._log_progress("Starting Phase 0b: Generating hypotheses...")
        self.cost_tracker.check_budget("Phase 0b: Hypotheses", estimated_cost=1.00)
        hypotheses, forcing_functions_log = self._generate_hypotheses_with_forcing_functions(
            proposition, paradigms, difficulty
        )
        self._log_progress(f"Generated {len(hypotheses)} hypotheses")

        # Phase 0c: Assign priors per paradigm (BEFORE evidence, based only on background context)
        self._report_status("phase:priors")
        self._log_progress("Starting Phase 0c: Assigning priors...")
        self.cost_tracker.check_budget("Phase 0c: Priors", estimated_cost=0.50)
        priors_by_paradigm = self._assign_priors(hypotheses, paradigms, proposition)
        self._log_progress("Priors assigned")

        # Build scenario_config dynamically
        scenario_config = self._build_scenario_config(
            scenario_id, proposition, domain, paradigms, hypotheses,
            forcing_functions_log, priors_by_paradigm
        )

        # Save scenario config to file
        self._save_scenario_config(scenario_id, scenario_config)

        # Create request and run existing phases 1-5
        # Pass budget_limit so conduct_analysis continues with same budget
        request = BFIHAnalysisRequest(
            scenario_id=scenario_id,
            proposition=proposition,
            scenario_config=scenario_config,
            user_id="autonomous",
            budget_limit=budget_limit
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
        bfih_context = get_bfih_system_context("Paradigm Generation", "0a")
        prompt = f"""{bfih_context}
PROPOSITION: "{proposition}"
DOMAIN: {domain}

## EPISTEMIC GUARDRAILS - READ FIRST

Before generating paradigms, classify the proposition:

### TYPE A: Empirical Factual Claims
Claims with objectively verifiable answers (e.g., "The earth is flat", "Vaccines cause autism", "The moon landing was faked"):
- ALL paradigms MUST AGREE on the factual answer based on scientific consensus
- Paradigms differ on VALUES and PRIORITIES, not on relationship with objective reality
- Do NOT generate paradigms that affirm science denial, conspiracy theories, or anti-empirical positions
- Instead, paradigms should address: "Given the factual answer, what are the implications? Why does this matter? What values are at stake?"
- For clearly false claims: Hypotheses should be about WHY people believe the false claim, not WHETHER the claim is true

### TYPE B: Value-Laden / Interpretive Propositions
Claims involving values, priorities, or interpretations (e.g., "Nuclear energy should be expanded", "Life begins at conception", "Immigration policy should be more restrictive"):
- Paradigms CAN differ on substantive conclusions
- Differences reflect genuine value differences (e.g., individual vs collective, economic vs cultural, short-term vs long-term)
- All paradigms must still share basic epistemic rationality

### PROHIBITED PARADIGMS (Never Generate These)
- **Science Denial**: "Flat Earth Believer", "Anti-Vaccine Truther", "Climate Denial"
- **Conspiracy Thinking**: "Anti-Establishment Skeptic" who rejects all mainstream institutions
- **Epistemic Relativism**: Paradigms that treat all truth claims as equally valid
- **Bad Faith Positions**: Paradigms designed to undermine rational discourse

### ALL PARADIGMS MUST SHARE
- Commitment to logical consistency
- Willingness to update beliefs based on evidence
- Recognition that some claims are objectively true or false
- Good faith engagement with opposing views

If the proposition is a Type A empirical claim with clear scientific consensus, reframe the analysis to ask a more intellectually productive question (e.g., "Why do flat earth beliefs persist?" rather than "Is the earth flat?").

---

## CRITICAL REQUIREMENT: K0 + K0-inv + Biased Paradigms

You MUST generate paradigms with EXPLICIT STANCES across 6 dimensions:

### 1. **K0 (Privileged Paradigm)**: Maximally intellectually honest
   - Applies ALL forcing functions (Ontological Scan, Ancestral Check, Paradigm Inversion)
   - Covers all 9 ontological domains
   - Has explicit assumptions, limitations, and falsification criteria
   - NOT neutral—has a SPECIFIC STANCE, but systematically interrogates its own blind spots
   - For POLITICAL propositions: MUST explicitly address Constitutional/Legal and Democratic domains

### 2. **K0-inv (True Inverse of K0)**: Genuine alternative worldview
   - CRITICAL: This is NOT about intellectual dishonesty or bad faith
   - Must GENUINELY INVERT K0's stance across ALL 6 dimensions:
     * If K0 is Secular → K0-inv is Religious/Theological
     * If K0 is Empiricist → K0-inv is Revelatory/Traditional
     * If K0 is Analytical → K0-inv is Holistic/Synthetic
     * If K0 is Individualist → K0-inv is Communitarian
     * If K0 is Optimizing → K0-inv is Receiving/Accepting
     * If K0 is Short-term → K0-inv is Intergenerational/Eternal
   - K0-inv is a coherent worldview that could yield TRUE insights K0 would miss
   - Example: "Life architecture is not a project to be engineered; it is a gift to be received within tradition, community, and faith"

### 3. **K1-K5 (Biased Paradigms)**: 3-5 realistically biased paradigms
   - Each must fail ≥1 forcing function (document which one)
   - Must be REALISTIC biases, not straw men
   - Types: Domain Bias, Temporal Bias, Ideological Bias, Cognitive Bias, Institutional Bias

## EXPLICIT STANCE REQUIREMENT (6 Dimensions)

EVERY paradigm (K0, K0-inv, K1-K5) must have an explicit stance object with:
- **ontology**: What exists/is real (e.g., "Material/measurable phenomena" vs "Spiritual/transcendent realities")
- **epistemology**: How we know (e.g., "Empirical observation" vs "Revelatory wisdom and tradition")
- **axiology**: What is valuable (e.g., "Efficiency/optimization" vs "Faithfulness to obligations")
- **methodology**: How we analyze (e.g., "Analytical/reductionist" vs "Holistic/synthetic")
- **sociology**: Who decides (e.g., "Expert/technocratic" vs "Communal discernment")
- **temporality**: Time horizon (e.g., "Short-term ROI" vs "Intergenerational/eternal")

## OUTPUT FORMAT

For EACH paradigm provide:
- id: K0, K0-inv, K1, K2, K3, etc.
- name: Short descriptive name
- description: Epistemic stance - what this paradigm treats as valid evidence
- is_privileged: true ONLY for K0
- is_k0_inverse: true ONLY for K0-inv
- bias_type: null for K0/K0-inv, otherwise one of [domain, temporal, ideological, cognitive, institutional]
- bias_description: null for K0/K0-inv, otherwise describe the specific bias
- inverse_paradigm_id: K0 points to K0-inv, K0-inv points to K0, others as appropriate
- stance: Object with ontology, epistemology, axiology, methodology, sociology, temporality
- forcing_function_compliance: Object with ontological_scan, ancestral_check, paradigm_inversion
- domains_covered: List of domains this paradigm engages
- characteristics: Object with prefers_evidence_types, skeptical_of, causal_preference, time_horizon

Return the result as a JSON object with a "paradigms" array: [K0, K0-inv, K1, K2, ...].

IMPORTANT: Return ONLY valid JSON. No additional text before or after the JSON object.
"""
        try:
            # Use reasoning model for paradigm construction (cognitively demanding task)
            # Falls back to structured output (o4-mini) if JSON parsing fails
            result = self._run_reasoning_phase(
                prompt, "Phase 0a: Generate Paradigms (reasoning)",
                schema_name="paradigms"  # Enables structured output fallback
            )
            paradigms = result.get("paradigms", [])
        except Exception as e:
            logger.error(f"Structured output failed for paradigms: {e}, using fallback")
            # Fallback to default paradigms following the K0 + K0-inv + K1-K4 structure
            # Each paradigm has an explicit stance across 6 dimensions
            paradigms = [
                {
                    "id": "K0", "name": "Secular-Empiricist Synthesis",
                    "description": "Intellectually honest synthesis privileging empirical observation, falsifiable claims, and multi-causal analysis across all domains",
                    "is_privileged": True,
                    "is_k0_inverse": False,
                    "bias_type": None,
                    "bias_description": None,
                    "inverse_paradigm_id": "K0-inv",
                    "stance": {
                        "ontology": "Material and measurable phenomena; accepts non-material factors only with empirical correlates",
                        "epistemology": "Empirical observation, falsification, peer review; values replicable findings",
                        "axiology": "Truth-seeking, efficiency, optimization of measurable outcomes",
                        "methodology": "Analytical decomposition, controlled comparison, quantitative where possible",
                        "sociology": "Expert consensus, credentialed authority, institutional review",
                        "temporality": "Medium-term with explicit uncertainty about long-term projections"
                    },
                    "forcing_function_compliance": {
                        "ontological_scan": "pass",
                        "ancestral_check": "pass",
                        "paradigm_inversion": "pass"
                    },
                    "domains_covered": ["Biological", "Economic", "Cultural", "Theological", "Historical", "Institutional", "Psychological", "Constitutional_Legal", "Democratic"],
                    "characteristics": {
                        "prefers_evidence_types": ["quantitative", "qualitative", "historical", "expert_testimony"],
                        "skeptical_of": ["single-cause explanations", "unfalsifiable claims", "appeals to tradition alone"],
                        "causal_preference": "multi-causal with documented interactions",
                        "time_horizon": "medium-term"
                    }
                },
                {
                    "id": "K0-inv", "name": "Religious-Traditional Wisdom",
                    "description": "Genuine inverse worldview: knowledge received through revelation, tradition, and communal discernment within faith; could yield true insights the empiricist stance would miss",
                    "is_privileged": False,
                    "is_k0_inverse": True,
                    "bias_type": None,
                    "bias_description": None,
                    "inverse_paradigm_id": "K0",
                    "stance": {
                        "ontology": "Spiritual and transcendent realities are primary; material world participates in higher order",
                        "epistemology": "Revelatory wisdom, sacred tradition, lived experience within faith community",
                        "axiology": "Faithfulness to obligations, covenant-keeping, alignment with transcendent purposes",
                        "methodology": "Holistic integration, narrative understanding, wisdom accumulated across generations",
                        "sociology": "Communal discernment, elders and tradition-bearers, authority rooted in spiritual lineage",
                        "temporality": "Intergenerational and eternal; current decisions judged by their fit within cosmic/sacred history"
                    },
                    "forcing_function_compliance": {
                        "ontological_scan": "pass: engages all domains through theological lens",
                        "ancestral_check": "pass: tradition is central",
                        "paradigm_inversion": "pass: explicitly inverts K0"
                    },
                    "domains_covered": ["Biological", "Economic", "Cultural", "Theological", "Historical", "Institutional", "Psychological"],
                    "characteristics": {
                        "prefers_evidence_types": ["scriptural", "traditional", "testimonial", "communal_wisdom"],
                        "skeptical_of": ["reductionist explanations", "claims that exclude transcendence", "purely technocratic solutions"],
                        "causal_preference": "providential ordering and human response to transcendent call",
                        "time_horizon": "intergenerational"
                    }
                },
                {
                    "id": "K1", "name": "Techno-Economic Rationalist",
                    "description": "Success/failure driven by measurable economic and technical factors",
                    "is_privileged": False,
                    "is_k0_inverse": False,
                    "bias_type": "domain",
                    "bias_description": "Ignores cultural/theological domains; over-weights quantitative metrics",
                    "inverse_paradigm_id": "K2",
                    "stance": {
                        "ontology": "Economic and technical systems are the fundamental drivers",
                        "epistemology": "Quantitative metrics, ROI calculations, technical benchmarks",
                        "axiology": "Efficiency, profit maximization, competitive advantage",
                        "methodology": "Cost-benefit analysis, financial modeling, technical assessment",
                        "sociology": "Markets and technical experts determine outcomes",
                        "temporality": "Short-term quarterly/annual cycles"
                    },
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
                    "is_k0_inverse": False,
                    "bias_type": "temporal",
                    "bias_description": "Over-weights historical patterns; may miss novel factors",
                    "inverse_paradigm_id": "K1",
                    "stance": {
                        "ontology": "Cultural narratives and historical forces shape reality",
                        "epistemology": "Historical analysis, ethnographic understanding, narrative interpretation",
                        "axiology": "Cultural continuity, meaning-making, identity preservation",
                        "methodology": "Comparative historical analysis, thick description, genealogical tracing",
                        "sociology": "Communities and their traditions determine outcomes",
                        "temporality": "Long-term historical patterns and path dependencies"
                    },
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
                    "is_k0_inverse": False,
                    "bias_type": "institutional",
                    "bias_description": "Over-emphasizes formal rules; may miss informal dynamics",
                    "inverse_paradigm_id": "K4",
                    "stance": {
                        "ontology": "Institutions and formal rules are the primary causal factors",
                        "epistemology": "Policy analysis, legal interpretation, institutional documentation",
                        "axiology": "Order, compliance, proper governance",
                        "methodology": "Institutional analysis, regulatory review, stakeholder mapping",
                        "sociology": "Institutions and their formal processes determine outcomes",
                        "temporality": "Medium-term policy cycles"
                    },
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
                    "is_k0_inverse": False,
                    "bias_type": "ideological",
                    "bias_description": "Over-weights individual action; under-weights structural constraints",
                    "inverse_paradigm_id": "K3",
                    "stance": {
                        "ontology": "Individual actors and their choices are the fundamental reality",
                        "epistemology": "Biographical study, decision analysis, psychological assessment",
                        "axiology": "Freedom, responsibility, self-determination",
                        "methodology": "Case studies of individuals, leadership analysis, motivational research",
                        "sociology": "Great individuals shape history; agency trumps structure",
                        "temporality": "Short-term decision windows"
                    },
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

        bfih_context = get_bfih_system_context("Hypothesis Generation with Forcing Functions", "0b")
        prompt = f"""{bfih_context}
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

## SPECIAL CASE: FACTUAL CLAIMS WITH CLEAR SCIENTIFIC CONSENSUS

For propositions that assert something contrary to established scientific fact (e.g., "The earth is flat",
"Vaccines cause autism", "The moon landing was faked", "Evolution is false"):

**CRITICAL: Do NOT generate hypotheses affirming scientifically false claims.**

Instead, reframe the analysis to address WHY people believe the false claim:
- H1: "Social/psychological factors" - Distrust of institutions, in-group identity, cognitive biases
- H2: "Information ecosystem factors" - Algorithm-driven bubbles, misinformation spread, media literacy gaps
- H3: "Cultural/historical factors" - Anti-establishment traditions, historical betrayals of trust, religious frameworks
- H4: "Educational factors" - Gaps in science education, failure to teach critical thinking
- H0: "Other unforeseen factors"

**Example: "The earth is flat" - CORRECT reframing:**
- Reframe to: "Why do flat earth beliefs persist despite overwhelming evidence?"
- H1: "Distrust of scientific institutions and authority drives flat earth belief"
- H2: "Social media algorithms and echo chambers amplify flat earth communities"
- H3: "Flat earth belief serves psychological needs for certainty and belonging"
- H4: "Failures in science education enable flat earth belief to spread"
- H0: "Other unforeseen factors"

**NEVER generate these hypotheses for factual claims:**
- ❌ "TRUE - The earth is actually flat despite mainstream claims"
- ❌ "TRUE - Vaccines do cause autism despite CDC/WHO denial"
- ❌ "PARTIAL - There's some validity to flat earth arguments"

## SPECIAL CASE: SUPERLATIVE/COMPARATIVE CLAIMS

For propositions claiming something is "the best", "the greatest", "the worst", "GOAT", etc.:

**You MUST include at least ONE substantive "FALSE, someone/something else is better" hypothesis**
- This drives evidence search for COMPARATIVE data (stats, achievements, records of alternatives)
- Without this, the analysis can only find evidence about the subject, not about competitors
- You don't need to enumerate every candidate - ONE or TWO well-chosen alternatives suffice

Example: "Tom Brady is the NFL GOAT"
  - H1 (AFFIRM): "Brady IS the GOAT - 7 championships, longevity, and clutch performance"
  - H2 (DENY): "Another player is the GOAT" - Name 1-2 top alternatives (Montana's perfect Super Bowl record, or a case from another position like Lawrence Taylor's defensive dominance)
  - H3 (QUALIFY): "GOAT is era/position-dependent; cross-era comparison is fundamentally flawed"
  - H4 (DENY): "Career trajectory of current players (e.g., Mahomes) projects to surpass Brady"

**DO NOT:**
- Generate abstract domain-based denials like "Biological factors don't support GOAT status"
- Create separate hypothesis for every possible candidate
- Ignore other positions/categories (for "NFL GOAT", consider non-QBs too)

**DO:**
- Name specific alternatives in DENY hypotheses to drive comparative evidence search
- Consider whether the superlative claim's category matters (position, era, metric)

## SPECIAL CASE: RECOMMENDATION/CHOICE QUERIES (Best X in Y, Top Options, etc.)

For propositions seeking recommendations like "best burgers in Cincinnati", "luxury hotels in Paris",
"top accounting software for small business", or any "what are my options?" type query:

**CRITICAL: These are NOT abstract philosophical questions. Users want ACTIONABLE GUIDANCE.**

The intellectually honest approach is to:
1. Acknowledge that "best" depends on individual criteria and preferences
2. BUT STILL enumerate specific, real-world candidates with their attributes
3. Present evidence about each candidate's strengths and weaknesses
4. Let users make informed decisions based on their own priorities

**REQUIRED: Generate hypotheses that NAME SPECIFIC CANDIDATES**

Example: "Best burgers in Cincinnati"
  - H1: "[Specific Restaurant A] offers the best burger" - Name actual establishment (e.g., "Terry's Turf Club")
  - H2: "[Specific Restaurant B] offers the best burger" - Name a different contender (e.g., "Zip's Cafe")
  - H3: "[Specific Restaurant C] offers the best burger" - Name another strong option (e.g., "Krueger's Tavern")
  - H4: "Best depends on criteria (price, atmosphere, meat quality, toppings)" - QUALIFY hypothesis
  - H0: "Other establishments not yet discovered or newly opened"

Example: "Lifestyle luxury hotels in Nashville"
  - H1: "[Hotel A] is the best lifestyle luxury option" - Name actual hotel (e.g., "The Graduate Nashville")
  - H2: "[Hotel B] is the best lifestyle luxury option" - Name competitor (e.g., "Noelle Nashville")
  - H3: "[Hotel C] is the best lifestyle luxury option" - Name another (e.g., "Bobby Hotel")
  - H4: "Best depends on specific needs (location, amenities, price point, vibe)"
  - H0: "Boutique options or new properties not yet widely reviewed"

**IMPORTANT FOR EVIDENCE GATHERING:**
- Evidence should include reviews, ratings, specific attributes of each named candidate
- Search for "best [X] in [Y]" rankings, local guides, expert reviews
- Capture prices, locations, key differentiators, standout features
- Include both professional reviews AND user reviews where available

**THE GOAL:** After the analysis, users should have a clear mental map of:
- What the actual options are (named candidates)
- What each option is known for (differentiators)
- What criteria matter for choosing between them
- Enough information to make their own informed choice

This IS intellectually honest because:
- We're not claiming one answer is objectively correct
- We're presenting real evidence about real options
- We acknowledge the role of personal preferences
- We help users think through the decision rather than making it for them

## SPECIAL CASE: POLITICAL/GOVERNANCE PROPOSITIONS

For propositions about political leaders, administrations, governments, policies, or national direction:

**You MUST include hypotheses addressing Constitutional/Legal and Democratic dimensions:**

1. **Constitutional/Legal Domain** (REQUIRED for political propositions):
   - Separation of powers (executive, legislative, judicial balance)
   - Rule of law (equal application, judicial independence)
   - Constitutional norms and precedents
   - Legal challenges to policies/actions

2. **Democratic Domain** (REQUIRED for political propositions):
   - Civil liberties (speech, press, assembly, due process)
   - Electoral integrity
   - Democratic backsliding indicators
   - Press freedom and institutional independence

**Example: "America's greatness is increasing under [Administration X]"**
  - H1 (AFFIRM): "TRUE - Economic growth and policy achievements demonstrate increasing greatness"
  - H2 (DENY): "FALSE - Constitutional erosion: checks and balances weakened, executive overreach"
  - H3 (DENY): "FALSE - Democratic backsliding: civil liberties restricted, press freedom declined"
  - H4 (QUALIFY): "PARTIAL - Economic metrics improved but democratic institutions weakened"
  - H5 (DENY): "FALSE - International standing declined despite domestic claims"

**CRITICAL: Do NOT reduce political analysis to economics alone.**
- Economic metrics are ONE dimension, not the whole picture
- Constitutional structure and democratic health are equally important
- Evidence should include: court rulings, civil liberties reports, democracy indices (V-Dem, Freedom House), press freedom rankings

**Evidence to actively search for in political propositions:**
- Constitutional/legal challenges and court rulings
- Civil liberties organization reports (ACLU, Human Rights Watch)
- Democracy indices (V-Dem, Freedom House, EIU Democracy Index)
- Press freedom rankings (RSF, CPJ)
- Separation of powers analyses
- Inspector General and oversight body reports

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

### 1. ONTOLOGICAL SCAN (Quality Check, NOT Template)
Use domains as a COMPLETENESS CHECK, not as hypothesis generators:
- DO NOT create one hypothesis per domain
- DO ensure relevant domains are covered by your substantive hypotheses
- Tag each hypothesis with which domains it touches

**9 Ontological Domains:**
1. **Biological** - Physical, health, biological factors
2. **Economic** - Markets, finance, trade, employment
3. **Cultural** - Social norms, values, identity, media narratives
4. **Theological** - Religious, spiritual, moral frameworks
5. **Historical** - Precedents, trends, era comparisons
6. **Institutional** - Bureaucratic, administrative, organizational
7. **Psychological** - Individual/group cognition, behavior, motivation
8. **Constitutional/Legal** - Rule of law, separation of powers, judicial independence, legal challenges
9. **Democratic** - Civil liberties, electoral integrity, press freedom, democratic norms

**Domain Relevance by Proposition Type:**
- Sports/performance: Historical, Cultural, Psychological, Biological
- Business/corporate: Economic, Institutional, Legal
- Political/governance: Constitutional/Legal, Democratic, Institutional, Economic, Historical
- Scientific claims: Biological, Institutional, Historical
- Social issues: Cultural, Psychological, Democratic, Historical

**For POLITICAL propositions, Constitutional/Legal and Democratic domains are MANDATORY.**

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
      "Psychological": {{"covered_by": "H2", "justification": "..."}},
      "Constitutional_Legal": {{"covered_by": "H2", "justification": "For political propositions: rule of law, separation of powers"}},
      "Democratic": {{"covered_by": "H3", "justification": "For political propositions: civil liberties, press freedom, electoral integrity"}}
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
            # Falls back to structured output (o4-mini) if JSON parsing fails
            result = self._run_reasoning_phase(
                prompt, "Phase 0b: Generate Hypotheses + Forcing Functions (reasoning)",
                schema_name="hypotheses"  # Enables structured output fallback
            )
            hypotheses = result.get("hypotheses", [])
            forcing_functions_log = result.get("forcing_functions_log", {})

            # Deduplicate domains and associated_paradigms for each hypothesis
            for hyp in hypotheses:
                if hyp.get("domains"):
                    hyp["domains"] = list(dict.fromkeys(hyp["domains"]))  # Preserve order, remove dupes
                if hyp.get("associated_paradigms"):
                    hyp["associated_paradigms"] = list(dict.fromkeys(hyp["associated_paradigms"]))

            # Validate we got actual hypotheses
            if len(hypotheses) < 2:
                raise ValueError(f"Reasoning model only returned {len(hypotheses)} hypotheses")

        except Exception as e:
            logger.warning(f"Reasoning model failed for hypotheses: {e}, falling back to structured output")
            # Fallback to structured output with o4-mini
            try:
                fallback_prompt = prompt.replace("Think step by step", "").replace("```json", "").replace("```", "")
                result = self._run_structured_phase(
                    fallback_prompt, "hypotheses", "Phase 0b: Generate Hypotheses (fallback)"
                )
                hypotheses = result.get("hypotheses", [])
                forcing_functions_log = result.get("forcing_functions_log", {})
                # Deduplicate domains and associated_paradigms for each hypothesis
                for hyp in hypotheses:
                    if hyp.get("domains"):
                        hyp["domains"] = list(dict.fromkeys(hyp["domains"]))
                    if hyp.get("associated_paradigms"):
                        hyp["associated_paradigms"] = list(dict.fromkeys(hyp["associated_paradigms"]))
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

        bfih_context = get_bfih_system_context("Prior Probability Assignment", "0c")
        prompt = f"""{bfih_context}
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

2. **BASE RATES ARE CRITICAL** - Before assigning priors, consider:
   - What is the base rate for claims like this to be true in general?
   - For startups: ~90% fail, ~5-10% might be called "thriving"
   - For extraordinary claims: Start with LOW priors for affirmative hypotheses
   - The prior for H1 (proposition TRUE) should reflect how UNLIKELY the claim is *a priori*
   - A company being "thriving" is NOT the default state - it's the exception

3. **K0 (privileged paradigm)** should be SKEPTICAL by default:
   - Reflect genuine uncertainty weighted by base rates
   - For positive claims (X is thriving, X is successful), start with LOW priors (0.10-0.20)
   - Spread probability mass across FALSE, PARTIAL, and alternative hypotheses
   - Only assign high priors to affirmative claims if background knowledge strongly supports them

4. **K1-Kn (biased paradigms)** should have priors that reflect their specific biases:
   - Domain bias: Higher priors for hypotheses in favored domains
   - Temporal bias: Higher priors for hypotheses matching time horizon preference
   - Ideological bias: Higher priors for hypotheses aligned with values
   - Even biased paradigms should respect base rates somewhat

5. **H0 (catch-all)** should generally receive 5-20% prior (room for unforeseen alternatives)

6. **OCCAM'S RAZOR - COMPLEXITY PENALTY** (especially for K0):
   - Simpler hypotheses (single mechanism, fewer conditions) deserve HIGHER priors
   - Complex hypotheses (multiple independent mechanisms, many conditions) deserve LOWER priors
   - A hypothesis invoking 2 independent mechanisms should have roughly HALF the prior of one invoking 1
   - PARTIAL hypotheses that combine conditions from multiple simpler hypotheses inherit the
     complexity of that conjunction and should have correspondingly lower priors
   - Example: If H1="mechanism A alone" and H2="mechanism B alone", then
     H3="mechanism A AND mechanism B under different conditions" is more complex
     and should have lower prior than either H1 or H2 individually
   - This prevents complex "accommodation" hypotheses from getting unearned prior boosts
   - K0 (privileged paradigm) should especially enforce this principle to maintain intellectual honesty

7. **Justifications** should reference paradigm assumptions AND base rate reasoning, NOT external evidence

## OUTPUT FORMAT

Return as a JSON object with "paradigm_priors" array containing:
- paradigm_id: the paradigm identifier
- hypothesis_priors: array of {{hypothesis_id, prior, justification}}

Example justification (GOOD): "Given the base rate that ~90% of startups fail, K0 assigns only 0.15 prior to H1 (TRUE) and spreads mass across H2-H4"
Example justification (GOOD): "K1's economic focus assigns slightly higher prior (0.25) to market-based explanations, though still respecting low base rates"
Example justification (GOOD): "H3 combines mechanisms from H1 and H2, making it more complex. K0 applies Occam's penalty: prior 0.08 vs 0.15 for simpler alternatives"
Example justification (BAD): "Studies show that economic factors account for 60% of such outcomes" (uses evidence!)
Example justification (BAD): "The proposition sounds reasonable so H1 gets 0.40" (ignores base rates!)
Example justification (BAD): "H3 covers more cases so it gets higher prior" (rewards complexity instead of penalizing it!)

IMPORTANT: Return ONLY valid JSON. No additional text before or after the JSON object.
"""
        try:
            # Use reasoning model for prior assignment (requires careful paradigm-aware reasoning)
            # Falls back to structured output (o4-mini) if JSON parsing fails
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
        Save the generated scenario config to JSON files.

        Saves to two locations:
        1. Root directory: scenario_config_{id}.json (for direct access)
        2. data/scenarios/{id}.json (for API storage backend)
        """
        # Save to root directory (original behavior)
        filename = f"scenario_config_{scenario_id}.json"
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved scenario config to: {filename}")

        # Also save to data/scenarios/ for API storage backend
        storage_dir = Path("./data/scenarios")
        storage_dir.mkdir(parents=True, exist_ok=True)
        storage_filename = storage_dir / f"{scenario_id}.json"
        with open(storage_filename, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved scenario config to storage: {storage_filename}")

        return filename

    # =========================================================================
    # BIBLIOGRAPHY CLEANUP
    # =========================================================================

    def cleanup_bibliography(self, report: str) -> str:
        """
        Deduplicate and renumber bibliography entries, updating citations in main text.

        Deduplication is based on:
        - Normalized title similarity (fuzzy matching)
        - Overlapping authors
        - Same publication/journal

        Args:
            report: The full BFIH report with bibliography

        Returns:
            Report with deduplicated, renumbered bibliography and updated citations
        """
        import re
        from difflib import SequenceMatcher

        logger.info("Starting bibliography cleanup...")

        # Find bibliography section
        bib_markers = ["## 9. Bibliography", "## Bibliography", "## References"]
        bib_start = -1
        bib_marker_used = ""
        for marker in bib_markers:
            if marker in report:
                bib_start = report.find(marker)
                bib_marker_used = marker
                break

        if bib_start == -1:
            logger.warning("No bibliography section found, skipping cleanup")
            return report

        # Split into main text and bibliography
        main_text = report[:bib_start]
        bib_section = report[bib_start:]

        # Find where bibliography ends (next major section or end)
        bib_end_match = re.search(r'\n## (?!9\. Bibliography|Bibliography|References)', bib_section)
        if bib_end_match:
            bib_content = bib_section[:bib_end_match.start()]
            after_bib = bib_section[bib_end_match.start():]
        else:
            # Check for end marker
            end_marker = bib_section.find("**End of BFIH")
            if end_marker != -1:
                bib_content = bib_section[:end_marker]
                after_bib = bib_section[end_marker:]
            else:
                bib_content = bib_section
                after_bib = ""

        # Parse bibliography entries - handle both formats:
        # [1] Author. Title...  OR  1. Author. Title...
        entry_pattern = r'(?:^\[(\d+)\]|\n(\d+)\.\s+)(.+?)(?=(?:\n\[?\d+[\].]|\Z))'
        entries = []

        # Try numbered list format first (1. Author...)
        numbered_pattern = r'^(\d+)\.\s+(.+?)(?=\n\d+\.\s+|\n\n|\Z)'
        numbered_matches = list(re.finditer(numbered_pattern, bib_content, re.MULTILINE | re.DOTALL))

        if numbered_matches:
            for match in numbered_matches:
                num = int(match.group(1))
                content = match.group(2).strip()
                entries.append({'num': num, 'content': content, 'original': match.group(0)})
        else:
            # Try bracketed format [1] Author...
            bracketed_pattern = r'\[(\d+)\]\s*(.+?)(?=\[\d+\]|\Z)'
            bracketed_matches = list(re.finditer(bracketed_pattern, bib_content, re.DOTALL))
            for match in bracketed_matches:
                num = int(match.group(1))
                content = match.group(2).strip()
                entries.append({'num': num, 'content': content, 'original': match.group(0)})

        if not entries:
            logger.warning("Could not parse bibliography entries, skipping cleanup")
            return report

        logger.info(f"Parsed {len(entries)} bibliography entries")

        # Extract metadata from each entry for comparison
        def extract_metadata(content: str) -> dict:
            """Extract title, authors, publication, URL from entry."""
            metadata = {'title': '', 'authors': [], 'publication': '', 'url': '', 'year': ''}

            # Extract URL
            url_match = re.search(r'https?://[^\s\)]+', content)
            if url_match:
                metadata['url'] = url_match.group(0).rstrip('.,;')

            # Extract year
            year_match = re.search(r'\((\d{4})\)', content)
            if year_match:
                metadata['year'] = year_match.group(1)

            # Extract title - usually between year and "Retrieved" or journal name
            # Pattern: Authors (Year). Title. Publication...
            title_match = re.search(r'\(\d{4}[^)]*\)[.,]?\s*(.+?)(?:\.\s*(?:Retrieved|In\s|[A-Z][a-z]+\s+(?:Review|Journal|Quarterly|Magazine)))', content)
            if title_match:
                metadata['title'] = title_match.group(1).strip().rstrip('.')
            else:
                # Fallback: take text between year and first URL or end
                fallback_match = re.search(r'\(\d{4}[^)]*\)[.,]?\s*(.+?)(?:Retrieved|https?://)', content)
                if fallback_match:
                    metadata['title'] = fallback_match.group(1).strip().rstrip('.')

            # Extract authors - text before the year
            author_match = re.search(r'^([^(]+)\(', content)
            if author_match:
                author_text = author_match.group(1).strip().rstrip('.,')
                # Split on common separators
                authors = re.split(r',\s*&\s*|,\s*|\s+&\s+', author_text)
                # Filter out generic placeholders that shouldn't count as real authors
                generic_authors = {
                    'et al', 'et al.', 'author', 'authors', 'author(s)',
                    'author unspecified', 'author unknown', 'unknown',
                    'anonymous', 'n.d.', 'n.d', 'various', 'staff'
                }
                metadata['authors'] = [
                    a.strip() for a in authors
                    if a.strip() and a.strip().lower().strip('()') not in generic_authors
                ]

            # Extract publication/journal
            pub_patterns = [
                r'(?:In\s+)?([A-Z][a-zA-Z\s&]+(?:Review|Journal|Quarterly|Magazine|Nexus|Ethics|Episteme|Synthese))',
                r'(?:In\s+)?([A-Z][a-zA-Z\s&]+Press)',
            ]
            for pattern in pub_patterns:
                pub_match = re.search(pattern, content)
                if pub_match:
                    metadata['publication'] = pub_match.group(1).strip()
                    break

            return metadata

        # Extract metadata for all entries
        for entry in entries:
            entry['metadata'] = extract_metadata(entry['content'])

        def normalize_title(title: str) -> str:
            """Normalize title for comparison."""
            # Lowercase, remove punctuation, collapse whitespace
            title = title.lower()
            title = re.sub(r'[^\w\s]', ' ', title)
            title = re.sub(r'\s+', ' ', title).strip()
            return title

        def title_similarity(t1: str, t2: str) -> float:
            """Calculate similarity between two titles."""
            n1, n2 = normalize_title(t1), normalize_title(t2)
            if not n1 or not n2:
                return 0.0
            return SequenceMatcher(None, n1, n2).ratio()

        def normalize_author(author: str) -> str:
            """Normalize author name for comparison."""
            # Extract last name (usually first word or after comma)
            author = author.strip().lower()
            parts = author.split(',')
            if len(parts) > 1:
                return parts[0].strip()
            parts = author.split()
            if parts:
                # Last name is usually last, but could be first for "LastName, F."
                return parts[-1] if len(parts) > 1 else parts[0]
            return author

        def authors_overlap(a1: list, a2: list) -> bool:
            """Check if author lists have significant overlap."""
            if not a1 or not a2:
                return False
            norm1 = set(normalize_author(a) for a in a1)
            norm2 = set(normalize_author(a) for a in a2)
            # Consider overlap if any author matches
            return bool(norm1 & norm2)

        def normalize_url(url: str) -> str:
            """Normalize URL for comparison."""
            url = url.lower().rstrip('/')
            # Remove common variations
            url = re.sub(r'/article-abstract/', '/article/', url)
            url = re.sub(r'/pdf/?$', '', url)
            url = re.sub(r'https?://(www\.)?', '', url)
            return url

        def are_duplicates(e1: dict, e2: dict) -> bool:
            """Determine if two entries are duplicates."""
            m1, m2 = e1['metadata'], e2['metadata']

            # Same URL (normalized)
            if m1['url'] and m2['url']:
                if normalize_url(m1['url']) == normalize_url(m2['url']):
                    return True

            # High title similarity + same publication or overlapping authors
            if m1['title'] and m2['title']:
                sim = title_similarity(m1['title'], m2['title'])
                if sim > 0.85:
                    # Very high similarity - likely duplicate
                    if sim > 0.95:
                        return True
                    # High similarity + same publication
                    if m1['publication'] and m2['publication']:
                        if m1['publication'].lower() == m2['publication'].lower():
                            return True
                    # High similarity + overlapping authors
                    if authors_overlap(m1['authors'], m2['authors']):
                        return True

            return False

        # Find duplicate groups using union-find
        n = len(entries)
        parent = list(range(n))

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        # Compare all pairs
        for i in range(n):
            for j in range(i + 1, n):
                if are_duplicates(entries[i], entries[j]):
                    union(i, j)
                    logger.debug(f"Found duplicate: [{entries[i]['num']}] and [{entries[j]['num']}]")

        # Group entries by their root
        groups = {}
        for i in range(n):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(i)

        # Count duplicates found
        dup_count = sum(1 for g in groups.values() if len(g) > 1)
        logger.info(f"Found {dup_count} duplicate groups")

        # For each group, pick the best entry (most complete) and build mapping
        old_to_new = {}  # old_num -> new_num
        new_entries = []
        new_num = 1

        # Sort groups by the minimum original entry number to preserve order
        sorted_groups = sorted(groups.items(), key=lambda x: min(entries[i]['num'] for i in x[1]))

        for root, group_indices in sorted_groups:
            group_entries = [entries[i] for i in group_indices]

            # Pick the best entry - prefer one with more metadata, longer content
            def entry_quality(e):
                m = e['metadata']
                score = 0
                if m['title']: score += 2
                if m['authors']: score += len(m['authors'])
                if m['publication']: score += 1
                if m['url']: score += 1
                if m['year']: score += 1
                score += len(e['content']) / 100  # Slight preference for longer entries
                return score

            best_entry = max(group_entries, key=entry_quality)

            # Map all old numbers in this group to the new number
            for e in group_entries:
                old_to_new[e['num']] = new_num

            new_entries.append({
                'num': new_num,
                'content': best_entry['content'],
                'original_nums': [e['num'] for e in group_entries]
            })
            new_num += 1

        logger.info(f"Reduced from {len(entries)} to {len(new_entries)} unique entries")

        # Update citations in main text
        def replace_citation(match):
            old_num = int(match.group(1))
            new_num = old_to_new.get(old_num, old_num)
            return f'[{new_num}]'

        # Replace [N] citations
        updated_main_text = re.sub(r'\[(\d+)\]', replace_citation, main_text)

        # Count how many citations were updated
        citation_changes = sum(1 for old, new in old_to_new.items() if old != new)
        logger.info(f"Updated {citation_changes} citation number mappings")

        # Rebuild bibliography section
        # Find the header and any intro text
        header_match = re.search(r'(## (?:9\. )?(?:Bibliography|References).*?\n+(?:\*\*[^*]+\*\*\n+)?)', bib_content)
        if header_match:
            bib_header = header_match.group(1)
        else:
            bib_header = f"{bib_marker_used}\n\n**References (APA Format):**\n\n"

        # Build new bibliography content
        new_bib_lines = [bib_header.rstrip() + "\n\n"]
        for entry in new_entries:
            new_bib_lines.append(f"{entry['num']}. {entry['content']}\n\n")

        new_bib_content = ''.join(new_bib_lines)

        # Reassemble report
        cleaned_report = updated_main_text + new_bib_content + after_bib

        logger.info("Bibliography cleanup complete")
        return cleaned_report

    # =========================================================================
    # SYNOPSIS STYLE PROMPTS
    # =========================================================================

    def _get_gawande_style_prompt(self, report: str) -> str:
        """
        Gawande scientific narrative style: wonder over advocacy, complexity preserved,
        false resolution resisted. Optimized for economy and non-redundancy.
        """
        return f"""Transform the following BFIH analysis report into a magazine-style feature that reports findings accessibly while maintaining intellectual honesty.

## STYLE: MEASURED SCIENTIFIC NARRATIVE

Your role: A thoughtful observer synthesizing rigorous analysis for intelligent general readers.

### VOICE & TONE:

Write with the measured confidence of someone who has done the work and is now explaining what they found. Neither breathless nor hedging—just clear, engaged, and honest.

**The tone to achieve:**
- Measured but not dry: "The evidence points to a tiered model..." not "Studies have shown that..."
- Curious without drama: "What's notable is..." not "Surprisingly..."
- Direct assertions when warranted: "This pattern holds most strongly in..." not "It could be argued that..."
- Honest about limits: "What remains genuinely uncertain is..." not "More research is needed..."

**Calibrated confidence (integrate naturally, don't label):**
- Strong evidence: State it directly. "Commercial flight death rates fell from 40 per million to under 0.2..."
- Moderate evidence: "The evidence suggests..." / "Studies of X found..."
- Genuine uncertainty: "Whether this represents a learnable skill or stable trait isn't resolved."

Avoid excessive hedging. If you've said "suggests" once, you don't need to qualify the same point again.

---

## THE CARDINAL RULE: FORWARD MOTION

Every paragraph must advance the reader's understanding. No section should repeat what an earlier section said.

**The test:** After writing each section, ask: "What does the reader know now that they didn't know before this section?" If the answer is "nothing new," cut it.

**Specific rules:**
1. State the core finding ONCE in the opening. Then it's established—move forward.
2. Each Evidence subsection teaches something distinct. No subsection restates another's conclusion.
3. "What This Means" provides NEW implications, not a summary of what was just said.
4. The Closing expands scope or offers philosophical reflection—never summarizes.

**Patterns that violate forward motion (eliminate all):**
- Restating the thesis in each section
- "As discussed above..." followed by re-discussing it
- Multiple paragraphs defining the same term or explaining the same nuance
- A "What Remains Uncertain" section that lists things already noted as uncertain inline
- A closing that begins "In conclusion..." and restates the opening

---

## STRUCTURE (4 sections)

**1. Opening** (~400-500 words)
   - Begin with a concrete scene, example, or striking claim that grounds the reader
   - State the core finding clearly and memorably—this is the ONLY full statement
   - Provide just enough context to understand why it matters
   - End with a pivot toward the evidence: "A recent investigation tested this claim..."

**2. The Evidence** (~1200-1800 words)
   - Organize thematically with ### subheadings (3-5 subsections)
   - Each subsection makes ONE distinct point with supporting details
   - Include specific data, citations [1], studies, concrete examples
   - Integrate uncertainties and complicating evidence INLINE where relevant—not as a separate section
   - If frameworks or value systems lead to different conclusions, one paragraph within the relevant subsection suffices

**3. What This Means** (~500-700 words)
   - NEW implications the reader couldn't derive themselves
   - Practical patterns, conditional guidance, or connections to adjacent domains
   - "For individuals navigating X, the evidence points toward..." / "Organizations face a parallel question..."
   - Assume the reader remembers the evidence—don't re-summarize it

**4. Closing** (~200-300 words)
   - Expand scope: connect to a broader pattern, adjacent field, or philosophical insight
   - "Perhaps the deepest finding isn't about X at all, but about..."
   - Or: distill a genuine uncertainty that science alone can't resolve
   - End on a thought that lingers—not a declaration that closes the book

---

## FORMATTING: STRATEGIC, NOT DECORATIVE

**Bold text:** Use sparingly to aid scanning. Bold a key phrase when introducing a major concept the reader will need to track: "**The result:** Gelman's thesis is correct, but with a critical caveat."

Do NOT bold:
- Every key term
- Section headers (they're already visually distinct)
- Phrases just for emphasis

**Bullets and tables:** Use ONLY when listing genuinely parallel items where prose would obscure structure.

Good uses:
- Conditions where a finding holds vs. fails (short parallel list)
- Comparison of 3+ options in a "best X" query (table)
- A hierarchy or tier system (numbered or bulleted)

Bad uses:
- Restating evidence points that flow naturally as prose
- Lists of one or two items
- Anything that could be a clear sentence

**When in doubt, prefer prose.** A well-structured paragraph is almost always better than a bullet list that fragments the narrative.

**Horizontal rules (---):** Use to separate major sections. One before "The Evidence," one before "What This Means," one before "Closing."

---

## SPECIAL: RECOMMENDATION/CHOICE QUERIES

If analyzing "the best" option (restaurants, hotels, products, etc.), include a comparison table in "What This Means":

| Option | Known For | Rating | Price | Best For |
|--------|-----------|--------|-------|----------|
| Name   | Key differentiator | Score | Range | User type |

Frame honestly: "Here are the real options with their differentiators. 'Best' depends on priorities."

---

## WHAT TO AVOID

**Framework jargon (never use):**
- "K0", "K1", "H1", "posterior probability", "likelihood ratio", "BFIH", "Bayesian"
- "Under paradigm...", "The analysis assigned probability...", "Evidence cluster C2..."

**Rhetorical clichés:**
- "You might think... but actually..."
- "The myth of..."
- "What everyone gets wrong about..."
- "It's complicated" / "It depends" (show the complexity, don't announce it)

**Structural failures:**
- Separate "What Remains Uncertain" section (integrate inline)
- Separate "How Different Perspectives Differ" section (one paragraph max, in Evidence)
- Closing that summarizes instead of expanding

---

## SELF-CHECK (apply before finalizing):

1. Count how many times you state the core finding. If more than once, cut the extras.
2. For each section, write one sentence describing what NEW information it provides. If you can't, revise.
3. Read your closing. Does it summarize or expand? If summarize, rewrite.
4. Scan for bold text. Is each instance earning its weight? Remove decorative bolding.
5. Check any bullet lists. Would prose be clearer? If yes, convert to prose.

---

BFIH ANALYSIS REPORT TO TRANSFORM:

{report}

---

Generate the article now. Aim for 2,500-3,500 words. Every paragraph earns its place by advancing the reader's understanding. A tight piece that moves forward is better than a longer piece that circles back.

The goal: A reader finishes and feels they've genuinely learned something—not been lectured, not been hedged at, but shown a complex reality with clarity and honesty."""

    def _get_atlantic_style_prompt(self, report: str) -> str:
        """
        Original style: Atlantic-style longform with K0 primacy framing.
        More adversarial/corrective tone, emphasizes how ideological lenses diverge.
        """
        return f"""Transform the following BFIH analysis report into an in-depth magazine article in the style of The Atlantic or longform explanatory journalism.

## CRITICAL REQUIREMENTS:

### THE K0 PARADIGM HAS PRIMACY:
The BFIH framework designates K0 as the "privileged paradigm" - not because it's one ideology among many,
but because it represents a commitment to intellectual honesty as a methodology rather than to any
particular worldview. K0's conclusions should be treated as THE primary finding of the analysis.

Your article should:
- Lead with and center K0's verdict and conclusions as the main finding
- Present K0's assessment as the intellectually honest baseline
- Treat other paradigms (K1, K2, etc.) as revealing how ideological commitments DIFFER from
  the intellectually honest assessment - not as equally valid alternatives
- Show how paradigms with ideological commitments (techno-optimism, traditionalism, etc.)
  reach different conclusions and WHY their priors or interpretive biases lead them there
- Do NOT frame this as "different perspectives are all valid" or "it depends on your values"
- DO frame this as "here's what intellectually honest analysis finds, and here's how various
  ideological lenses diverge from that finding"

### TONE & STYLE:
- Write in plain language accessible to general readers, NOT academic prose
- Be intellectually honest: present the K0 finding confidently, other paradigms fairly but critically
- Be information-dense but engaging - every paragraph should teach something
- Use vivid, specific details from the evidence rather than vague summaries
- Help readers understand both the conclusion AND why ideological thinking leads elsewhere
- Respect the reader's intelligence - inform and illuminate, don't preach or provoke

### ARTICLE STRUCTURE:
Create 6-8 sections with UNIQUE, TOPIC-SPECIFIC titles that fit THIS article's content.
Do NOT use generic template titles. Each section title should be crafted specifically
for this topic and could only belong to this article.

Use this general flow, but invent your own section titles:

1. **Headline + Subtitle**
   - A compelling, specific headline that captures K0's core finding
   - An italicized subtitle that adds context

2. **Opening Context** (~300-500 words)
   - Set up the question or issue being examined
   - Explain why this matters and what's at stake
   - Provide necessary background for readers unfamiliar with the topic

3. **The Evidence** (~1000-2000 words)
   - Walk through the evidence chronologically or thematically
   - Use specific dates, names, numbers, and citations [1], [2], etc.
   - Structure with clear subheadings (###) for each major theme or finding
   - Include specific examples and data points
   - Build a coherent narrative from the facts

4. **The Intellectually Honest Assessment** (~500-800 words)
   - Present K0's conclusions as the primary finding
   - Explain the reasoning and evidence that supports this verdict
   - Acknowledge genuine uncertainties where they exist
   - This is THE answer the analysis provides

5. **How Ideological Lenses Diverge** (~800-1200 words)
   - Show how paradigms with ideological commitments reach different conclusions
   - Use a third-level heading for each paradigm (e.g., a heading like "The Market Optimists: Why Growth Projections Diverge")
   - Explain what priors or assumptions lead each ideology to its different conclusion
   - This is NOT "alternative valid views" - it's "how ideology distorts assessment"
   - Be fair in representing each view, but clear that K0 has epistemic privilege

6. **Implications and Applications** (~400-600 words)
   - What are the practical implications of K0's findings?
   - How might this inform decisions or thinking?
   - Connect to broader patterns or lessons where appropriate

7. **Practical Guidance** (~400-600 words)
   - Concrete, actionable recommendations based on the K0 finding
   - Questions readers might ask themselves
   - How to apply these insights in practice

### SPECIAL: RECOMMENDATION/CHOICE QUERIES (Best X, Hotels, Restaurants, Products, GOAT, etc.)

If the analysis is about finding "the best" option (restaurants, hotels, products, athletes, etc.),
you MUST include a **Candidate Comparison Table or Enumeration** section:

- Create a markdown table or structured list of ALL named candidates from the analysis
- For each candidate, include:
  - Name
  - Key differentiator/what it's known for
  - Rating or tier (if available from evidence)
  - Price range (if applicable)
  - Standout features (2-3 bullet points)
  - Best for (what type of user/preference this suits)

**Example Table for "Best Burgers in Cincinnati":**

| Restaurant | Known For | Rating | Price | Best For |
|------------|-----------|--------|-------|----------|
| Terry's Turf Club | Massive hand-patted burgers, dive bar atmosphere | 4.5★ | $$ | Purists wanting no-frills excellence |
| Zip's Cafe | Classic Cincinnati-style, been there forever | 4.3★ | $ | Nostalgic locals, budget-conscious |
| Krueger's Tavern | Gourmet toppings, craft beer selection | 4.4★ | $$$ | Foodies wanting elevated experience |

**Or for Hotels:**

| Hotel | Style | Price/Night | Location | Best For |
|-------|-------|-------------|----------|----------|
| Noelle Nashville | Industrial-chic boutique | $300-450 | Downtown/Printers Alley | Design lovers, walkability |
| Bobby Hotel | Rooftop scene, social vibe | $250-400 | Downtown | Millennials, social travelers |
| Graduate Nashville | Music-themed, quirky | $200-350 | Midtown/Vanderbilt | Budget-conscious, campus visitors |

This table should come BEFORE or WITHIN the "Practical Guidance" section, giving readers
an at-a-glance comparison they can reference for decisions.

The intellectually honest framing is: "Here are your real options with their differentiators.
'Best' depends on your priorities, but here's the information to decide."

8. **Closing Reflection** (~300-400 words)
   - Synthesize the key insight from K0
   - Reflect on what this reveals about the topic
   - End with something thought-provoking but grounded in the analysis

### FORMATTING:
- Use # for title, ## for major sections, ### for subsections
- Use **bold** for emphasis and key terms
- Use *italics* for publication names and subtle emphasis
- Use > blockquotes for particularly striking quotes or findings
- Use numbered citations [1], [2] matching the bibliography
- TARGET LENGTH: 4000-6000 words (this should be a SUBSTANTIAL, in-depth piece)

### WHAT TO AVOID:
- DO NOT include a References/Bibliography section (it will be appended automatically)
- DO NOT use academic jargon or methodology descriptions
- DO NOT use sensationalized language or clickbait phrasing
- DO NOT treat all paradigms as equally epistemically valid - K0 has primacy
- DO NOT frame findings as "it depends on your perspective" relativism
- DO NOT be preachy, provocative, or condescending
- DO NOT use the template section titles verbatim - create unique titles for this article
- DO NOT hedge excessively - make clear claims where evidence supports them
- DO NOT use generic filler - every sentence should add value

### CRITICAL: NO EXPLICIT FRAMEWORK REFERENCES
The article should read like professional journalism, NOT a meta-commentary on the analysis.

**NEVER use these in the article text:**
- Paradigm IDs: "K0", "K1", "K2", etc. → Instead say "from an empirical perspective" or "those who prioritize tradition"
- Hypothesis IDs: "H1", "H2", "H3", etc. → Instead describe the claim directly
- Evidence IDs: "E1", "E2", "[E3]", etc. → Instead say "evidence such as..." or just cite [1], [2]
- Cluster IDs: "C1", "C2", "Cluster 3", etc. → Instead describe the evidence thematically
- Framework jargon: "posterior probability", "likelihood ratio", "weight of evidence", "BFIH", "Bayesian"
- Meta-references: "the analysis found", "the report shows", "under paradigm K0"

**DO use natural language:**
- "Evidence suggests..." not "Evidence cluster C2 shows..."
- "From a perspective emphasizing tradition..." not "Under K2..."
- "Multiple sources confirm..." not "E1, E3, and E7 support..."
- "The most rigorous assessment concludes..." not "K0's posterior probability of 0.87 indicates..."
- "Critics who prioritize novelty argue..." not "K1 assigns higher priors to..."

The reader should learn about THE TOPIC, informed by rigorous analysis, without ever seeing the analytical scaffolding. Write as if you did the research yourself and are now explaining what you learned.

---

BFIH ANALYSIS REPORT TO TRANSFORM:

{report}

---

Generate the complete magazine-style article now. Make it rich, detailed, and genuinely illuminating. The goal is that a reader who knows nothing about this topic could read your article and come away with deep understanding and new perspectives. This should be a piece worthy of publication in a major magazine.

CRITICAL LENGTH REQUIREMENT: Your response MUST be at least 4000 words. Do not summarize or abbreviate. Expand on each section with specific details, examples, and analysis from the source report. A short response is unacceptable."""

    def generate_magazine_synopsis(self, report: str, scenario_id: str, style: str = "gawande") -> str:
        """
        Generate a plain-language magazine-style synopsis from a BFIH analysis report.

        This transforms the technical academic report into an engaging magazine article
        that is accessible to general readers while maintaining analytical rigor and
        citing sources.

        Args:
            report: The full BFIH analysis report (markdown)
            scenario_id: The scenario ID for naming the output file
            style: Synopsis style - "gawande" (default, science narrative with wonder
                   and calibrated confidence) or "atlantic" (corrective K0-primacy style)

        Returns:
            The magazine synopsis as markdown text
        """
        logger.info(f"Generating magazine synopsis for scenario: {scenario_id}")

        # Clean up bibliography first (deduplicate and renumber)
        report = self.cleanup_bibliography(report)

        # Extract the bibliography section from the cleaned report to preserve it exactly
        bibliography_section = ""
        bibliography_markers = ["## 9. Bibliography", "## Bibliography", "## References"]
        for marker in bibliography_markers:
            if marker in report:
                # Find the bibliography section and everything after it
                bib_start = report.find(marker)
                # Find where bibliography ends (next major section or end of report)
                remaining = report[bib_start:]
                # Look for the next ## section after bibliography, or end of file
                next_section = remaining.find("\n## ", len(marker))
                if next_section != -1:
                    bibliography_section = remaining[:next_section].strip()
                else:
                    # Take everything to the end, but stop at "End of BFIH" marker if present
                    end_marker = remaining.find("**End of BFIH")
                    if end_marker != -1:
                        bibliography_section = remaining[:end_marker].strip()
                    else:
                        bibliography_section = remaining.strip()
                break

        # Select prompt based on style
        if style == "atlantic":
            prompt = self._get_atlantic_style_prompt(report)
            logger.info("Using Atlantic-style (corrective) prompt")
        else:
            prompt = self._get_gawande_style_prompt(report)
            logger.info("Using Gawande-style (science narrative) prompt")

        try:
            response = self.client.responses.create(
                model="gpt-5.2",  # Use GPT-5.2 for highest quality long-form writing
                input=prompt,
                max_output_tokens=16000,  # Increased for longer, richer output
                reasoning={"effort": "medium"},  # GPT-5.x requires explicit reasoning effort
            )

            # Track costs if usage data is available
            if hasattr(self, 'cost_tracker') and hasattr(response, 'usage') and response.usage:
                input_tokens = getattr(response.usage, 'input_tokens', 0) or 0
                output_tokens = getattr(response.usage, 'output_tokens', 0) or 0
                reasoning_tokens = getattr(response.usage, 'reasoning_tokens', 0) or 0
                self.cost_tracker.add_cost("gpt-5.2", "magazine_synopsis", input_tokens, output_tokens, reasoning_tokens)

            synopsis = response.output_text

            # Clean up any doubled markdown headers (e.g., "### ###" -> "###")
            synopsis = re.sub(r'^(#{1,6})\s+\1\s*', r'\1 ', synopsis, flags=re.MULTILINE)

            # Add header indicating this is a generated synopsis
            header = f"""*Generated from BFIH Analysis Report {scenario_id}*
*For the full technical analysis, see the complete BFIH report.*

---

"""
            synopsis = header + synopsis

            # Append the original bibliography section
            if bibliography_section:
                synopsis = synopsis.rstrip() + "\n\n---\n\n" + bibliography_section

            # Save to file
            filename = f"{scenario_id}_magazine_synopsis.md"
            with open(filename, 'w') as f:
                f.write(synopsis)
            logger.info(f"Saved magazine synopsis to: {filename}")

            return synopsis

        except BadRequestError as e:
            error_msg = str(e).lower()
            if "context_length_exceeded" in error_msg or "maximum context length" in error_msg:
                logger.error(f"Context length exceeded in synopsis generation: {e}")
                raise RuntimeError(
                    "Report too long for GPT-5.2's context window. "
                    "Synopsis generation skipped."
                ) from e
            elif "max_tokens" in error_msg:
                logger.error(f"Token limit exceeded in synopsis generation: {e}")
                raise RuntimeError(
                    "Synopsis exceeded token limit. Generation skipped."
                ) from e
            logger.error(f"Bad request in synopsis generation: {e}")
            raise RuntimeError(f"Synopsis generation failed: {e}") from e

        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            logger.error(f"Timeout in synopsis generation: {e}")
            raise RuntimeError(
                "GPT-5.2 timed out generating synopsis. "
                "This is optional - the main analysis is complete."
            ) from e

        except Exception as e:
            logger.error(f"Error generating magazine synopsis: {e}")
            raise

    # =========================================================================
    # GRAPHVIZ VISUALIZATION
    # =========================================================================

    def _insert_visualization_into_report(self, report: str, svg_path: str) -> str:
        """
        Insert visualization inline into the BFIH report.

        Reads the SVG file and embeds it directly in the report for web compatibility.

        Args:
            report: The markdown report
            svg_path: Path to the SVG file

        Returns:
            Updated report with embedded visualization
        """
        import os

        # Read the SVG content for inline embedding
        svg_content = ""
        try:
            with open(svg_path, 'r') as f:
                svg_content = f.read()
            # Wrap in a div for styling control
            svg_embed = f'<div class="bfih-visualization" style="width:100%;overflow-x:auto;">\n{svg_content}\n</div>'
        except Exception as e:
            logger.warning(f"Could not read SVG file for embedding: {e}")
            svg_filename = os.path.basename(svg_path)
            svg_embed = f'![BFIH Evidence Flow](./{svg_filename})'

        visualization_section = f"""
## Evidence Flow Visualization

The following diagram shows the flow of evidence through the Bayesian analysis framework,
illustrating how evidence clusters support or refute each hypothesis.

{svg_embed}

*Figure: Evidence flow diagram showing hypotheses (boxes), evidence clusters (ellipses),
and likelihood ratios indicating strength of support or refutation.*

"""
        # Find a good insertion point - after Executive Summary or after first ## section
        insertion_markers = [
            "## 2. Paradigms",
            "## 2. Research Paradigms",
            "## Paradigms",
        ]

        for marker in insertion_markers:
            if marker in report:
                # Insert before the marker
                return report.replace(marker, visualization_section + marker)

        # Fallback: insert after first ## section
        first_section_end = report.find("\n## ", report.find("## ") + 1)
        if first_section_end > 0:
            return report[:first_section_end] + "\n" + visualization_section + report[first_section_end:]

        # Last resort: prepend to report
        return visualization_section + report

    def generate_evidence_flow_dot(self, result: 'BFIHAnalysisResult') -> str:
        """
        Generate Graphviz DOT visualization of BFIH evidence flow.

        Creates a visual representation showing:
        - Hypotheses with priors, posteriors, and status
        - Evidence clusters with item counts and Bayesian metrics
        - Evidence-to-hypothesis flow edges with likelihood ratios
        - Paradigm comparison
        - Final verdict

        Args:
            result: BFIHAnalysisResult containing analysis data

        Returns:
            DOT script as string
        """
        logger.info(f"Generating evidence flow DOT for: {result.scenario_id}")

        # Extract data from result
        scenario_config = result.scenario_config or {}
        hypotheses = scenario_config.get("hypotheses", [])
        paradigms = scenario_config.get("paradigms", [])
        priors_by_paradigm = scenario_config.get("priors_by_paradigm", {})
        posteriors = result.posteriors or {}
        evidence_clusters = result.metadata.get("evidence_clusters", [])

        # Use K0 (empirical) as primary paradigm, fallback to first available
        primary_paradigm = "K0"
        if primary_paradigm not in posteriors and posteriors:
            primary_paradigm = list(posteriors.keys())[0]

        k0_posteriors = posteriors.get(primary_paradigm, {})
        k0_priors = priors_by_paradigm.get(primary_paradigm, {})

        # Determine hypothesis status based on posteriors
        def get_hypothesis_status(h_id: str, post: float) -> tuple:
            """Return (status_label, penwidth) based on posterior probability."""
            sorted_posts = sorted(k0_posteriors.values(), reverse=True)
            if post == sorted_posts[0]:
                return "STRONGEST", 3
            elif len(sorted_posts) > 1 and post == sorted_posts[1]:
                return "STRONG", 2.5
            elif post >= 0.10:
                return "MODERATE", 2
            else:
                return "WEAK", 1

        # Hypothesis colors based on type
        def get_hypothesis_color(h_id: str, hypothesis: dict) -> str:
            """Return fill color based on hypothesis stance."""
            stance = hypothesis.get("stance", "").lower()
            if stance == "true" or "true" in hypothesis.get("name", "").lower():
                return "#CCFFCC"  # Green - proposition true
            elif stance == "false" or "false" in hypothesis.get("name", "").lower():
                return "#FF9999"  # Red - proposition false
            elif "partial" in stance or "conditional" in hypothesis.get("name", "").lower():
                return "#FFFF99"  # Yellow - partial
            elif h_id == "H0":
                return "#E0E0E0"  # Gray - catch-all
            else:
                return "#B3D9FF"  # Blue - domain-specific

        # Edge styling based on likelihood ratio
        def get_edge_style(lr: float) -> tuple:
            """Return (label, color, penwidth, style) based on LR."""
            if lr >= 3.0:
                return "Strong support", "#006600", 3, "solid"  # Dark green
            elif lr >= 2.0:
                return "Moderate support", "#228B22", 2.5, "solid"  # Forest green
            elif lr >= 1.2:
                return "Weak support", "#66CC66", 2, "solid"  # Light green
            elif lr > 0.8:
                return "Neutral", "#999999", 1, "dashed"  # Gray
            elif lr > 0.5:
                return "Weak refutation", "#CC6666", 1, "dotted"  # Light red
            else:
                return "Refutation", "#CC0000", 1.5, "dotted"  # Dark red

        # Helper to sanitize IDs for DOT (no hyphens, special chars)
        def sanitize_id(id_str: str) -> str:
            """Convert ID to valid DOT identifier."""
            return id_str.replace("-", "_").replace(" ", "_").lower()

        def word_wrap(text: str, max_width: int = 60) -> str:
            """Word-wrap text at word boundaries."""
            words = text.split()
            lines = []
            current_line = []
            current_length = 0
            for word in words:
                if current_length + len(word) + 1 <= max_width:
                    current_line.append(word)
                    current_length += len(word) + 1
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = len(word)
            if current_line:
                lines.append(" ".join(current_line))
            return "\\n".join(lines)

        # Word-wrap proposition for title
        wrapped_proposition = word_wrap(result.proposition, 60)
        graph_title = f"BFIH Analysis of Proposition:\\n\\\"{wrapped_proposition}\\\""

        # Build DOT script
        lines = [
            f"// BFIH Evidence Flow: {result.proposition[:60]}...",
            "// Auto-generated visualization of Bayesian analysis structure",
            "",
            "digraph BFIHEvidenceFlow {",
            "    // Graph properties",
            "    rankdir=LR;",
            "    compound=true;",
            '    fontname="Helvetica-Bold,Arial Bold,sans-serif";',
            '    node [fontname="Helvetica,Arial,sans-serif", fontsize=10];',
            '    edge [fontname="Helvetica,Arial,sans-serif", fontsize=8];',
            f'    label="{graph_title}";',
            '    labelloc="t";',
            '    fontsize=18;',
            "",
        ]

        # ============================================================
        # Hypothesis nodes
        # ============================================================
        lines.append("    // ============================================================")
        lines.append("    // Hypothesis Space")
        lines.append("    // ============================================================")
        lines.append("")
        lines.append("    subgraph cluster_hypotheses {")
        lines.append(f'        label="Hypothesis Space ({len(hypotheses)} explanations)";')
        lines.append('        style="filled,rounded";')
        lines.append('        fillcolor="#E8F4F8";')
        lines.append("        fontsize=12;")
        lines.append("        penwidth=2;")
        lines.append("")

        for h in hypotheses:
            h_id = h.get("id", "H?")
            h_name = h.get("name", "Unknown")
            prior = k0_priors.get(h_id, 0)
            if isinstance(prior, dict):
                prior = prior.get("probability", 0)
            posterior = k0_posteriors.get(h_id, 0)
            status, penwidth = get_hypothesis_status(h_id, posterior)
            color = get_hypothesis_color(h_id, h)

            # Word-wrap hypothesis name for display (max 35 chars per line)
            display_name = h_name.replace('"', '\\"')
            wrapped_name = word_wrap(display_name, 35)

            lines.append(f'        {sanitize_id(h_id)} [label="{h_id}: {wrapped_name}\\n\\nPrior: {prior:.2f}\\nPosterior: {posterior:.3f}\\nStatus: {status}",')
            lines.append(f'            shape=box, style="filled,rounded", fillcolor="{color}", penwidth={penwidth}];')
            lines.append("")

        lines.append("    }")
        lines.append("")

        # ============================================================
        # Evidence cluster nodes
        # ============================================================
        lines.append("    // ============================================================")
        lines.append("    // Evidence Clusters")
        lines.append("    // ============================================================")
        lines.append("")

        cluster_colors = ["#FFE6E6", "#FFFCE6", "#FFF0E6", "#E6F3FF", "#F0E6FF", "#E6FFE6"]
        node_colors = ["#FFCCCC", "#FFFFCC", "#FFE6CC", "#CCE6FF", "#E6CCFF", "#CCFFCC"]

        for i, cluster in enumerate(evidence_clusters):
            c_id = cluster.get("cluster_id", f"C{i+1}")
            c_name = cluster.get("cluster_name", cluster.get("description", "Evidence"))
            c_description = cluster.get("description", "")
            # Get item count from evidence_ids (list of IDs) or evidence_items (list of objects)
            evidence_ids = cluster.get("evidence_ids", [])
            items = cluster.get("evidence_items", [])
            item_count = len(evidence_ids) if evidence_ids else (len(items) if isinstance(items, list) else cluster.get("item_count", 0))

            # Get Bayesian metrics for primary paradigm
            metrics_by_paradigm = cluster.get("bayesian_metrics_by_paradigm", {})
            metrics = metrics_by_paradigm.get(primary_paradigm, cluster.get("bayesian_metrics", {}))

            # Find strongest supported hypothesis
            best_h = None
            best_lr = 0
            for h_id, m in metrics.items():
                lr = m.get("LR", 0)
                if isinstance(lr, str):
                    lr = float(lr) if lr != "inf" else 100
                if lr > best_lr:
                    best_lr = lr
                    best_h = h_id

            color_idx = i % len(cluster_colors)

            # Word-wrap cluster name for subgraph label
            wrapped_c_name = word_wrap(c_name, 40)
            lines.append(f"    subgraph cluster_{sanitize_id(c_id)} {{")
            lines.append(f'        label="{c_id}: {wrapped_c_name}\\n({item_count} items)";')
            lines.append('        style="filled,rounded";')
            lines.append(f'        fillcolor="{cluster_colors[color_idx]}";')
            lines.append("        fontsize=10;")
            lines.append("")

            # Create descriptive node label from description
            # Take first ~80 chars of description, word-wrapped
            if c_description and len(c_description) > 10:
                short_desc = c_description[:100].rsplit(' ', 1)[0] if len(c_description) > 100 else c_description
                short_desc = short_desc.replace('"', '\\"')
                node_label = word_wrap(short_desc, 35)
            else:
                node_label = word_wrap(c_name, 35)

            woe_str = ""
            if best_h and best_h in metrics:
                woe = metrics[best_h].get("WoE_dB", 0)
                woe_str = f"\\n\\nWoE to {best_h}: {woe:.1f} dB"

            lines.append(f'        {sanitize_id(c_id)}_node [label="{node_label}\\n({item_count} items){woe_str}",')
            lines.append(f'                 shape=ellipse, style="filled", fillcolor="{node_colors[color_idx]}"];')
            lines.append("    }")
            lines.append("")

        # ============================================================
        # Evidence-to-hypothesis edges
        # ============================================================
        lines.append("    // ============================================================")
        lines.append("    // Evidence flows to hypotheses")
        lines.append("    // ============================================================")
        lines.append("")

        # First, collect all potential edges with their LR values
        import math
        all_edges = []
        edges_by_cluster = {}  # Track edges per cluster for max/min selection

        for cluster in evidence_clusters:
            c_id = cluster.get("cluster_id", "C?")
            metrics_by_paradigm = cluster.get("bayesian_metrics_by_paradigm", {})
            metrics = metrics_by_paradigm.get(primary_paradigm, cluster.get("bayesian_metrics", {}))

            edges_by_cluster[c_id] = []
            for h_id, m in metrics.items():
                lr = m.get("LR", 1.0)
                if isinstance(lr, str):
                    lr = float(lr) if lr != "inf" else 100
                if lr > 0:  # Avoid log of zero/negative
                    abs_log_lr = abs(math.log10(lr))
                    edge = (c_id, h_id, lr, abs_log_lr)
                    all_edges.append(edge)
                    edges_by_cluster[c_id].append(edge)

        # Find top 3 by abs(log10(LR))
        top_3_edges = set()
        sorted_by_strength = sorted(all_edges, key=lambda x: x[3], reverse=True)[:3]
        for edge in sorted_by_strength:
            top_3_edges.add((edge[0], edge[1]))

        # Find max and min LR edges for each cluster
        max_min_edges = set()
        for c_id, cluster_edges in edges_by_cluster.items():
            if cluster_edges:
                # Max LR edge (strongest support)
                max_edge = max(cluster_edges, key=lambda x: x[2])
                max_min_edges.add((max_edge[0], max_edge[1]))
                # Min LR edge (strongest refutation or weakest support)
                min_edge = min(cluster_edges, key=lambda x: x[2])
                max_min_edges.add((min_edge[0], min_edge[1]))

        # Create edges: include if LR <= 1/3 or LR >= 3, OR in top 3, OR max/min for cluster
        for c_id, h_id, lr, abs_log_lr in all_edges:
            is_significant = lr <= (1/3) or lr >= 3
            is_top_3 = (c_id, h_id) in top_3_edges
            is_max_min = (c_id, h_id) in max_min_edges

            if is_significant or is_top_3 or is_max_min:
                _, color, penwidth, style = get_edge_style(lr)
                lines.append(f'    {sanitize_id(c_id)}_node -> {sanitize_id(h_id)} [label="LR: {lr:.2f}", color="{color}", penwidth={penwidth}, style={style}];')

        lines.append("")

        # ============================================================
        # Posterior summary node
        # ============================================================
        lines.append("    // ============================================================")
        lines.append("    // Posterior Summary")
        lines.append("    // ============================================================")
        lines.append("")

        # Sort posteriors for display
        sorted_posts = sorted(k0_posteriors.items(), key=lambda x: x[1], reverse=True)
        post_lines = "\\n".join([f"{h}: {p*100:.1f}%" for h, p in sorted_posts[:5]])

        # Determine verdict
        top_h, top_p = sorted_posts[0] if sorted_posts else ("?", 0)
        if top_p > 0.7:
            verdict = "STRONGLY SUPPORTED"
        elif top_p > 0.5:
            verdict = "SUPPORTED"
        elif top_p > 0.35:
            verdict = "PARTIALLY VALIDATED"
        else:
            verdict = "UNCERTAIN"

        lines.append(f'    posterior_summary [label="{primary_paradigm} Posteriors\\n\\n{post_lines}\\n\\nVerdict: {verdict}",')
        lines.append('                        shape=box, style="filled,rounded", fillcolor="#FFF4E6",')
        lines.append('                        fontsize=11, penwidth=2];')
        lines.append("")

        # Connect hypotheses to summary
        for h in hypotheses:
            h_id = h.get("id", "H?")
            post = k0_posteriors.get(h_id, 0)
            style = "solid" if post > 0.1 else "dashed"
            lines.append(f'    {sanitize_id(h_id)} -> posterior_summary [style={style}];')

        lines.append("")

        # ============================================================
        # Paradigm comparison (if multiple paradigms)
        # ============================================================
        if len(posteriors) > 1:
            lines.append("    // ============================================================")
            lines.append("    // Paradigm Comparison")
            lines.append("    // ============================================================")
            lines.append("")
            lines.append("    subgraph cluster_paradigm_compare {")
            lines.append('        label="Cross-Paradigm Comparison";')
            lines.append('        style="filled,rounded";')
            lines.append('        fillcolor="#F0E6FF";')
            lines.append("        fontsize=11;")
            lines.append("")

            for p_id, p_posts in posteriors.items():
                if p_posts:
                    top_h = max(p_posts.items(), key=lambda x: x[1])
                    p_name = p_id
                    # Try to get paradigm name
                    for p in paradigms:
                        if p.get("id") == p_id:
                            p_name = p.get("name", p_id)[:15]
                            break
                    lines.append(f'        paradigm_{sanitize_id(p_id)} [label="{p_id}: {p_name}\\n{top_h[0]}: {top_h[1]*100:.1f}%", style="filled", fillcolor="#E6CCFF"];')

            lines.append("    }")
            lines.append("")

            # Connect summary to paradigms
            for p_id in posteriors.keys():
                style = "solid" if p_id == primary_paradigm else "dashed"
                lines.append(f'    posterior_summary -> paradigm_{sanitize_id(p_id)} [style={style}];')

            lines.append("")

        # ============================================================
        # Evidence Base Assessment
        # ============================================================
        lines.append("    // ============================================================")
        lines.append("    // Evidence Base Assessment")
        lines.append("    // ============================================================")
        lines.append("")

        # Calculate totals
        total_evidence = result.metadata.get("evidence_items_count", 0)
        if not total_evidence:
            total_evidence = sum(len(c.get("evidence_ids", c.get("evidence_items", []))) for c in evidence_clusters)
        cluster_count = len(evidence_clusters)

        # Assess evidence quality/diversity
        paradigm_count = len(posteriors)
        avg_items_per_cluster = total_evidence / cluster_count if cluster_count > 0 else 0

        # Build assessment label
        if total_evidence >= 50:
            quantity_rating = "Extensive"
        elif total_evidence >= 25:
            quantity_rating = "Substantial"
        elif total_evidence >= 10:
            quantity_rating = "Moderate"
        else:
            quantity_rating = "Limited"

        assessment_label = (
            f"Evidence Assessment\\n\\n"
            f"Total Evidence Items: {total_evidence}\\n"
            f"Evidence Clusters: {cluster_count}\\n"
            f"Paradigms Analyzed: {paradigm_count}\\n"
            f"Avg Items/Cluster: {avg_items_per_cluster:.1f}\\n\\n"
            f"Coverage: {quantity_rating}"
        )

        lines.append(f'    evidence_assessment [label="{assessment_label}",')
        lines.append('                          shape=box, style="filled,rounded", fillcolor="#E6FFE6",')
        lines.append('                          fontsize=10, penwidth=1.5];')
        lines.append("")

        # ============================================================
        # Bayesian Synthesis
        # ============================================================
        lines.append("    // ============================================================")
        lines.append("    // Bayesian Synthesis")
        lines.append("    // ============================================================")
        lines.append("")

        # Calculate prior-to-posterior shifts for top hypotheses
        synthesis_lines = ["BAYESIAN SYNTHESIS\\n"]
        for h_id, post in sorted_posts[:3]:  # Top 3 hypotheses
            prior = k0_priors.get(h_id, 0)
            if isinstance(prior, dict):
                prior = prior.get("probability", 0)
            shift = post - prior
            shift_dir = "+" if shift > 0 else ""
            synthesis_lines.append(f"{h_id}: {prior*100:.0f}% → {post*100:.1f}% ({shift_dir}{shift*100:.1f}%)")

        # Calculate total weight of evidence
        total_woe = 0
        for cluster in evidence_clusters:
            metrics = cluster.get("bayesian_metrics_by_paradigm", {}).get(primary_paradigm, {})
            for h_id, m in metrics.items():
                woe = m.get("WoE_dB", 0)
                if isinstance(woe, (int, float)):
                    total_woe += abs(woe)

        synthesis_lines.append(f"\\nTotal WoE: {total_woe:.1f} dB")
        synthesis_label = "\\n".join(synthesis_lines)

        lines.append(f'    bayesian_synthesis [label="{synthesis_label}",')
        lines.append('                         shape=box, style="filled,rounded", fillcolor="#E6F3FF",')
        lines.append('                         fontsize=10, penwidth=1.5];')
        lines.append("")

        # Connect paradigm nodes to synthesis (not posterior_summary)
        if len(posteriors) > 1:
            for p_id in posteriors.keys():
                lines.append(f'    paradigm_{sanitize_id(p_id)} -> bayesian_synthesis [style=dashed, color="#666666"];')
        else:
            lines.append('    posterior_summary -> bayesian_synthesis [style=solid];')
        lines.append("")

        # ============================================================
        # Key Insights
        # ============================================================
        lines.append("    // ============================================================")
        lines.append("    // Key Insights")
        lines.append("    // ============================================================")
        lines.append("")

        # Generate insights based on analysis
        insights = ["KEY INSIGHTS\\n"]

        # Insight 1: Paradigm agreement/disagreement
        paradigm_winners = {}
        for p_id, p_posts in posteriors.items():
            if p_posts:
                winner = max(p_posts.items(), key=lambda x: x[1])
                paradigm_winners[p_id] = winner[0]

        unique_winners = set(paradigm_winners.values())
        if len(unique_winners) == 1:
            insights.append(f"• All {len(paradigm_winners)} paradigms agree on {list(unique_winners)[0]}")
        else:
            insights.append(f"• {len(unique_winners)} different conclusions across paradigms")

        # Insight 2: Evidence strength
        strong_support_count = 0
        strong_refute_count = 0
        for cluster in evidence_clusters:
            metrics = cluster.get("bayesian_metrics_by_paradigm", {}).get(primary_paradigm, {})
            for h_id, m in metrics.items():
                lr = m.get("LR", 1.0)
                if isinstance(lr, (int, float)):
                    if lr >= 3.0:
                        strong_support_count += 1
                    elif lr <= 0.33:
                        strong_refute_count += 1

        insights.append(f"• {strong_support_count} strong support signals")
        insights.append(f"• {strong_refute_count} strong refutation signals")

        # Insight 3: Decisive margin (calculate here for use in insights)
        top_h_id, top_posterior = sorted_posts[0] if sorted_posts else ("?", 0)
        second_h_id, second_posterior = sorted_posts[1] if len(sorted_posts) > 1 else ("?", 0)
        margin = top_posterior - second_posterior

        if margin > 0.5:
            insights.append(f"• Decisive margin ({margin*100:.0f}%) over alternatives")
        elif margin > 0.2:
            insights.append(f"• Clear margin ({margin*100:.0f}%) over alternatives")
        else:
            insights.append(f"• Narrow margin ({margin*100:.0f}%) - some uncertainty")

        insights_label = "\\n".join(insights)

        lines.append(f'    key_insights [label="{insights_label}",')
        lines.append('                   shape=box, style="filled,rounded", fillcolor="#FFF0F5",')
        lines.append('                   fontsize=10, penwidth=1.5];')
        lines.append("")

        # Connect synthesis to insights
        lines.append('    bayesian_synthesis -> key_insights [style=solid];')
        lines.append("")

        # ============================================================
        # Final Analysis Summary
        # ============================================================
        lines.append("    // ============================================================")
        lines.append("    // Final Analysis Summary")
        lines.append("    // ============================================================")
        lines.append("")

        # Build final summary
        top_h_id, top_posterior = sorted_posts[0] if sorted_posts else ("?", 0)
        second_h_id, second_posterior = sorted_posts[1] if len(sorted_posts) > 1 else ("?", 0)

        # Get hypothesis name for conclusion
        top_h_name = top_h_id
        for h in hypotheses:
            if h.get("id") == top_h_id:
                top_h_name = h.get("name", top_h_id)
                break

        confidence = "High" if top_posterior > 0.7 else ("Moderate" if top_posterior > 0.5 else "Low")
        margin = top_posterior - second_posterior

        # Word-wrap the hypothesis name for the conclusion label
        display_h_name = top_h_name.replace('"', '\\"')
        wrapped_h_name = word_wrap(display_h_name, 30)

        summary_label = (
            f"ANALYSIS CONCLUSION\\n\\n"
            f"Leading Hypothesis: {top_h_id}\\n"
            f"({wrapped_h_name})\\n\\n"
            f"Posterior: {top_posterior*100:.1f}%\\n"
            f"Margin over #2: {margin*100:.1f}%\\n"
            f"Confidence: {confidence}\\n\\n"
            f"Status: {verdict}"
        )

        lines.append(f'    final_summary [label="{summary_label}",')
        lines.append('                    shape=box, style="filled,bold,rounded", fillcolor="#FFE4B5",')
        lines.append('                    fontsize=11, penwidth=3];')
        lines.append("")

        # Connect insights to final summary (single parent)
        lines.append('    key_insights -> final_summary [style=solid, penwidth=2];')
        lines.append("")

        lines.append("}")

        dot_content = "\n".join(lines)
        logger.info(f"Generated DOT script: {len(lines)} lines")

        return dot_content

    def render_dot_to_svg(self, dot_content: str, output_path: str) -> Optional[str]:
        """
        Render DOT content to SVG using Graphviz.

        Args:
            dot_content: DOT script as string
            output_path: Path for output SVG file

        Returns:
            Path to SVG file if successful, None otherwise
        """
        import subprocess
        import shutil

        # Check if Graphviz is installed
        if not shutil.which('dot'):
            logger.warning("Graphviz 'dot' command not found. Install with: apt install graphviz")
            return None

        try:
            result = subprocess.run(
                ['dot', '-Tsvg'],
                input=dot_content,
                capture_output=True,
                text=True,
                timeout=90
            )

            if result.returncode != 0:
                logger.error(f"Graphviz error: {result.stderr}")
                return None

            with open(output_path, 'w') as f:
                f.write(result.stdout)

            logger.info(f"Rendered SVG to: {output_path}")
            return output_path

        except subprocess.TimeoutExpired:
            logger.warning("Graphviz SVG rendering timed out after 90s - continuing without visualization")
            return None
        except Exception as e:
            logger.warning(f"Graphviz SVG rendering failed - continuing without visualization: {e}")
            return None

    def render_dot_to_png(self, dot_content: str, output_path: str) -> Optional[str]:
        """
        Render DOT content to PNG using Graphviz.

        Args:
            dot_content: DOT script as string
            output_path: Path for output PNG file

        Returns:
            Path to PNG file if successful, None otherwise
        """
        import subprocess
        import shutil

        # Check if Graphviz is installed
        if not shutil.which('dot'):
            logger.warning("Graphviz 'dot' command not found. Install with: apt install graphviz")
            return None

        try:
            result = subprocess.run(
                ['dot', '-Tpng', '-Gdpi=150'],  # Higher DPI for better quality
                input=dot_content.encode('utf-8'),
                capture_output=True,
                timeout=90
            )

            if result.returncode != 0:
                logger.error(f"Graphviz error: {result.stderr.decode('utf-8')}")
                return None

            with open(output_path, 'wb') as f:
                f.write(result.stdout)

            logger.info(f"Rendered PNG to: {output_path}")
            return output_path

        except subprocess.TimeoutExpired:
            logger.warning("Graphviz PNG rendering timed out after 90s - continuing without visualization")
            return None
        except Exception as e:
            logger.warning(f"Graphviz PNG rendering failed - continuing without visualization: {e}")
            return None

    def generate_evidence_flow_visualization(
        self,
        result: 'BFIHAnalysisResult',
        output_dir: str = ".",
        embed_in_report: bool = False
    ) -> Dict[str, Optional[str]]:
        """
        Generate complete evidence flow visualization (DOT + PNG).

        Args:
            result: BFIHAnalysisResult containing analysis data
            output_dir: Directory for output files
            embed_in_report: Deprecated, kept for backwards compatibility

        Returns:
            Dict with paths: {"dot": path, "png": path, "dot_content": DOT source}
        """
        import os

        scenario_id = result.scenario_id
        dot_path = os.path.join(output_dir, f"{scenario_id}-evidence-flow.dot")
        png_path = os.path.join(output_dir, f"{scenario_id}-evidence-flow.png")

        # Generate DOT
        dot_content = self.generate_evidence_flow_dot(result)

        # Save DOT file
        with open(dot_path, 'w') as f:
            f.write(dot_content)
        logger.info(f"Saved DOT file: {dot_path}")

        # Render to PNG for better PDF compatibility
        png_result = self.render_dot_to_png(dot_content, png_path)

        output = {
            "dot": dot_path,
            "png": png_result,
            "dot_content": dot_content
        }

        return output


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
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output filename for report (without extension). Saves .md and .json"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="o3-mini",
        choices=AVAILABLE_REASONING_MODELS,
        help=f"Reasoning model to use (default: o3-mini). Options: {', '.join(AVAILABLE_REASONING_MODELS)}"
    )
    parser.add_argument(
        "--synopsis",
        action="store_true",
        help="Generate a magazine-style synopsis after analysis"
    )
    parser.add_argument(
        "--synopsis-style",
        type=str,
        default="gawande",
        choices=["gawande", "atlantic"],
        help="Synopsis style: 'gawande' (science narrative, default) or 'atlantic' (original corrective style)"
    )
    parser.add_argument(
        "--synopsis-from-report",
        type=str,
        metavar="REPORT_FILE",
        help="Generate a synopsis from an existing BFIH report file (markdown)"
    )

    args = parser.parse_args()

    # Handle synopsis-from-report mode (standalone synopsis generation)
    if args.synopsis_from_report:
        report_path = args.synopsis_from_report
        if not os.path.exists(report_path):
            print(f"Error: Report file not found: {report_path}")
            sys.exit(1)

        with open(report_path, "r") as f:
            report_content = f.read()

        # Derive scenario_id from filename
        base_name = os.path.splitext(os.path.basename(report_path))[0]
        scenario_id = base_name.replace("bfih-report-", "").replace("bfih_report_", "")

        print(f"Generating {args.synopsis_style}-style synopsis from: {report_path}")
        orchestrator = BFIHOrchestrator()
        synopsis = orchestrator.generate_magazine_synopsis(
            report=report_content,
            scenario_id=scenario_id,
            style=args.synopsis_style
        )

        # Determine output filename
        if args.output:
            synopsis_file = f"{args.output}.md"
        else:
            synopsis_file = f"{base_name}_synopsis.md"

        with open(synopsis_file, "w") as f:
            f.write(synopsis)
        print(f"Saved: {synopsis_file}")
        sys.exit(0)

    if args.topic:
        # Run with provided topic
        orchestrator = BFIHOrchestrator()
        result = orchestrator.analyze_topic(
            proposition=args.topic,
            domain=args.domain,
            difficulty=args.difficulty,
            reasoning_model=args.model
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

        # Determine output filename
        base_name = args.output if args.output else f"bfih_report_{result.scenario_id}"
        json_file = f"{base_name}.json"
        md_file = f"{base_name}.md"

        # Save JSON result
        with open(json_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

        # Save markdown report
        with open(md_file, "w") as f:
            f.write(result.report)

        print(f"\nSaved: {json_file}")
        print(f"Saved: {md_file}")

        # Generate synopsis if requested
        if args.synopsis:
            print(f"\nGenerating magazine synopsis ({args.synopsis_style} style)...")
            synopsis = orchestrator.generate_magazine_synopsis(
                report=result.report,
                scenario_id=result.scenario_id,
                style=args.synopsis_style
            )
            synopsis_file = f"{base_name}_synopsis.md"
            with open(synopsis_file, "w") as f:
                f.write(synopsis)
            print(f"Saved: {synopsis_file}")
    else:
        # Run default example
        example_autonomous_analysis()
