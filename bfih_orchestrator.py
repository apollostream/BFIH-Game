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
from typing import Dict, List, Optional, Tuple
from datetime import datetime
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
        Main entry point: Conduct full BFIH analysis
        
        Args:
            request: BFIHAnalysisRequest with scenario config and proposition
            
        Returns:
            BFIHAnalysisResult with report and posteriors
        """
        logger.info(f"Starting BFIH analysis for scenario: {request.scenario_id}")
        
        try:
            # Build the orchestration prompt
            prompt = self._build_orchestration_prompt(request)
            
            # Call OpenAI Responses API with all tools
            logger.info("Calling OpenAI Responses API with web_search, file_search, code_interpreter")
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
                tools=[
                    {
                        "type": "web_search",
                        "search_context_size": "low"
                    },
                    {
                        "type": "file_search",
                        "vector_store_ids": [self.vector_store_id]
                    },
                    {
                        "type": "code_interpreter",
                        "container": {"type": "auto"}
                    }
                ],
                include=["file_search_call.results"]
            )
            
            # Extract report and posteriors from response
            bfih_report = response.output_text
            posteriors = self._extract_posteriors_from_report(bfih_report, request.scenario_config)
            
            # Create result object
            analysis_id = str(uuid.uuid4())
            result = BFIHAnalysisResult(
                analysis_id=analysis_id,
                scenario_id=request.scenario_id,
                proposition=request.proposition,
                report=bfih_report,
                posteriors=posteriors,
                metadata={
                    "model": self.model,
                    "user_id": request.user_id
                },
                created_at=datetime.utcnow().isoformat()
            )
            
            logger.info(f"BFIH analysis completed successfully: {analysis_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error conducting BFIH analysis: {str(e)}")
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

YOUR TASK - Execute systematically in this order:

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
- Use code_execution to run Python script computing:
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
- Include all computed values from code_execution
- NO markdown code blocks for Python code (show results only)
- All posteriors must match code_execution output exactly
- Include at least 3-5 evidence items per paradigm

## PYTHON BAYESIAN CALCULATION TEMPLATE (will execute):

```python
import numpy as np
from collections import OrderedDict

# Hypotheses and priors (from scenario_config)
hypotheses = {{hypotheses_list}}
priors = {{priors_dict}}

# Evidence likelihoods (assigned by analysis)
evidence_items = {{evidence_likelihoods}}

# Compute posteriors
unnormalized_posteriors = {{}}
for h_i in hypotheses:
    prior_hi = priors[h_i]
    joint_likelihood = 1.0
    for Ek, lh_dict in evidence_items.items():
        pk_hi = lh_dict.get(h_i, 1.0)
        pk_not_hi = sum(lh_dict.get(h_j, 1.0) * (priors[h_j] / (1 - priors.get(h_i, 0.001))) 
                       for h_j in hypotheses if h_j != h_i)
        joint_likelihood *= pk_hi
    unnormalized_posteriors[h_i] = prior_hi * joint_likelihood

# Normalize
normalization = sum(unnormalized_posteriors.values())
posteriors = {{h: unnormalized_posteriors[h] / normalization for h in hypotheses}}

# Print results
for h in sorted(posteriors.keys(), key=lambda x: posteriors[x], reverse=True):
    print(f"{{h}}: {{posteriors[h]:.6f}}")
```

NOW BEGIN YOUR ANALYSIS. Work through each phase systematically.
"""
        return prompt
    
    def _extract_posteriors_from_report(self, report: str, scenario_config: Dict) -> Dict:
        """
        Extract posterior probabilities from the generated report
        Returns dict of {paradigm_id: {hypothesis_id: posterior_value}}
        """
        posteriors = {}
        
        # Parse paradigm-specific posterior sections from report
        # This is a simplified extraction; in production, use more robust parsing
        for paradigm in scenario_config.get("paradigms", []):
            paradigm_id = paradigm.get("id")
            posteriors[paradigm_id] = {}
            
            # Look for posterior values in report
            # In production: use regex or structured output parsing
            for hypothesis in scenario_config.get("hypotheses", []):
                hypothesis_id = hypothesis.get("id")
                # Placeholder: posteriors would be extracted from actual report
                posteriors[paradigm_id][hypothesis_id] = 0.0
        
        return posteriors


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
    
    proposition = "Why did Startup X succeed while competitors Y and Z failed?"
    
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


if __name__ == "__main__":
    # Run example analysis
    example_conduct_analysis()
