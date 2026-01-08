"""
BFIH Structured Output Schemas

Pydantic models for OpenAI structured outputs to ensure reliable JSON generation.
These schemas enforce correct structure, required fields, and type validation.

IMPORTANT: OpenAI structured outputs in strict mode require ALL properties to be
in the 'required' array. No default values allowed. Use Union[X, None] for nullable.
"""

from typing import List, Union, Literal
from pydantic import BaseModel, Field, ConfigDict


class StrictModel(BaseModel):
    """Base model with strict OpenAI-compatible JSON schema"""
    model_config = ConfigDict(
        extra='forbid'  # This adds additionalProperties: false
    )


# ============================================================================
# SHARED TYPE DEFINITIONS
# ============================================================================

DomainType = Literal[
    "Economic", "Institutional", "Psychological", "Cultural",
    "Historical", "Technical", "Biological", "Theological"
]

BiasType = Literal["domain", "temporal", "ideological", "cognitive", "institutional"]

TimeHorizon = Literal["short-term", "medium-term", "long-term", "intergenerational"]

TruthValueType = Literal["other", "affirm", "deny", "qualify"]


# ============================================================================
# PARADIGM SCHEMAS (Phase 0a)
# ============================================================================


class ForcingFunctionCompliance(StrictModel):
    """Compliance status for forcing functions"""
    ontological_scan: str = Field(
        description="'pass' or 'fail: [reason]' - whether paradigm covers all 7 domains"
    )
    ancestral_check: str = Field(
        description="'pass' or 'fail: [reason]' - whether paradigm considers historical precedent"
    )
    paradigm_inversion: str = Field(
        description="'pass' or 'fail: [reason]' - whether paradigm engages with inverse views"
    )


class ParadigmCharacteristics(StrictModel):
    """Characteristics that define how a paradigm evaluates evidence"""
    prefers_evidence_types: List[str] = Field(
        description="Types of evidence this paradigm values highly"
    )
    skeptical_of: List[str] = Field(
        description="Factors or evidence types this paradigm discounts"
    )
    causal_preference: str = Field(
        description="Primary causal mechanism this paradigm favors"
    )
    time_horizon: Union[TimeHorizon, None] = Field(
        description="Temporal focus: short-term, medium-term, long-term, or intergenerational"
    )


class Paradigm(StrictModel):
    """A paradigm represents an epistemic viewpoint/worldview.

    Following BFIH Paradigm Construction Manual:
    - K0: Privileged paradigm (maximally intellectually honest, passes all forcing functions)
    - K1-K5: Biased paradigms (realistically biased, fail >= 1 forcing function)
    """
    id: str = Field(description="Unique identifier: K0 for privileged, K1-K5 for biased")
    name: str = Field(description="Short descriptive name")
    description: str = Field(description="Epistemic stance and what counts as valid evidence")
    is_privileged: bool = Field(
        description="True only for K0 (maximally intellectually honest paradigm)"
    )
    bias_type: Union[BiasType, None] = Field(
        description="Type of bias: domain, temporal, ideological, cognitive, institutional (null for K0)"
    )
    bias_description: Union[str, None] = Field(
        description="Specific description of the bias (null for K0)"
    )
    inverse_paradigm_id: Union[str, None] = Field(
        description="ID of the inverse/opposing paradigm if applicable, or null"
    )
    forcing_function_compliance: ForcingFunctionCompliance = Field(
        description="How this paradigm handles forcing functions (K0 should pass all)"
    )
    domains_covered: List[DomainType] = Field(
        description="Ontological domains this paradigm engages (K0 should have all 7)"
    )
    characteristics: ParadigmCharacteristics


class ParadigmList(StrictModel):
    """List of paradigms for analysis.

    Must include K0 (privileged) + K1-K5 (3-5 biased paradigms).
    """
    paradigms: List[Paradigm] = Field(
        description="K0 (privileged) + K1-K5 (biased) paradigms"
    )


# ============================================================================
# HYPOTHESIS SCHEMAS (Phase 0b)
# ============================================================================


class Hypothesis(StrictModel):
    """A hypothesis is a TRUTH-VALUE CLAIM about the proposition.

    Following BFIH Paradigm Construction Manual:
    - H0: Other/Unforeseen - catch-all for unspecified alternatives (truth_value_type = "other")
    - H1: Affirms proposition is TRUE (truth_value_type = "affirm")
    - H2: Denies proposition is FALSE (truth_value_type = "deny")
    - H3: Qualifies proposition as PARTIAL (truth_value_type = "qualify")
    - H4+: Additional domain-specific or inversion hypotheses

    IMPORTANT: H0 is NOT "unknown/insufficient evidence". It captures unforeseen
    factors or alternatives not covered by H1-H4+.
    """
    id: str = Field(description="Unique identifier like H0, H1, H2")
    name: str = Field(
        description="Format: '[TRUE/FALSE/PARTIAL] - [Mechanism]' e.g., 'TRUE - Safety Culture Degradation'"
    )
    truth_value_type: TruthValueType = Field(
        description="What this hypothesis claims about the proposition: unknown, affirm, deny, or qualify"
    )
    statement: str = Field(
        description="Full statement: 'The proposition is TRUE/FALSE/PARTIALLY TRUE because...'"
    )
    mechanism_if_true: Union[str, None] = Field(
        description="The causal mechanism if this hypothesis is correct (null for H0)"
    )
    domains: List[DomainType] = Field(
        description="Ontological domains this hypothesis touches"
    )
    testable_predictions: List[str] = Field(
        description="Observable predictions if this hypothesis is true"
    )
    is_catch_all: bool = Field(
        description="True only for H0 (unforeseen/unspecified alternatives)"
    )
    is_ancestral_solution: bool = Field(
        description="True if informed by historical analogues (Ancestral Check)"
    )
    is_paradigm_inversion: bool = Field(
        description="True if this hypothesis captures a view that biased paradigms would dismiss"
    )
    inverted_from_paradigm: Union[str, None] = Field(
        description="If is_paradigm_inversion, which paradigm's blind spot does this capture (e.g., 'K1')"
    )


class OntologicalDomainCoverage(StrictModel):
    """How a domain is covered by hypotheses"""
    covered_by: str = Field(description="Hypothesis IDs that cover this domain (e.g., 'H1, H3')")
    justification: str = Field(description="Why this domain is relevant and how it's covered")


class OntologicalScan(StrictModel):
    """Forcing function: ensure all relevant domains are covered"""
    Economic: Union[OntologicalDomainCoverage, None] = Field(description="Economic domain coverage or null")
    Institutional: Union[OntologicalDomainCoverage, None] = Field(description="Institutional domain coverage or null")
    Psychological: Union[OntologicalDomainCoverage, None] = Field(description="Psychological domain coverage or null")
    Cultural: Union[OntologicalDomainCoverage, None] = Field(description="Cultural domain coverage or null")
    Historical: Union[OntologicalDomainCoverage, None] = Field(description="Historical domain coverage or null")
    Technical: Union[OntologicalDomainCoverage, None] = Field(description="Technical domain coverage or null")
    Biological: Union[OntologicalDomainCoverage, None] = Field(description="Biological domain coverage or null")
    Theological: Union[OntologicalDomainCoverage, None] = Field(description="Theological domain coverage or null")


class AncestralCheck(StrictModel):
    """Forcing function: identify historical analogues"""
    historical_analogues: List[str] = Field(
        description="Historical cases similar to this situation"
    )
    lessons_applied: str = Field(
        description="How historical lessons inform our hypotheses"
    )
    hypothesis_informed: Union[str, None] = Field(
        description="Which hypothesis was informed by ancestral check (e.g., 'H3')"
    )


class ParadigmInversionEntry(StrictModel):
    """Record of a hypothesis generated through paradigm inversion"""
    paradigm: str = Field(description="Which biased paradigm's blind spot this addresses (e.g., 'K1')")
    dismissed_view: str = Field(description="What view this paradigm would dismiss")
    captured_in: str = Field(description="Which hypothesis captures this dismissed view (e.g., 'H2')")


class ParadigmInversionLog(StrictModel):
    """Log of paradigm inversions applied"""
    inversions_generated: List[ParadigmInversionEntry] = Field(
        description="List of hypotheses generated by inverting biased paradigms"
    )


class MECEVerification(StrictModel):
    """Forcing function: verify MECE property on truth values"""
    mutual_exclusivity: str = Field(
        description="Explanation of why hypotheses represent different truth values (TRUE/FALSE/PARTIAL/UNKNOWN)"
    )
    collective_exhaustiveness: str = Field(
        description="Explanation of why all truth values are covered (affirm + deny + qualify + unknown = complete)"
    )
    sum_to_one_possible: bool = Field(
        description="Whether probabilities can sum to 1.0 (should be true for MECE)"
    )


class ForcingFunctionsLog(StrictModel):
    """Log of all three forcing functions applied"""
    ontological_scan: OntologicalScan
    ancestral_check: AncestralCheck
    paradigm_inversion: ParadigmInversionLog
    mece_verification: MECEVerification


class HypothesesWithForcingFunctions(StrictModel):
    """Complete hypothesis generation output"""
    hypotheses: List[Hypothesis] = Field(
        description="MECE set of propositional hypotheses (3-10 hypotheses)"
    )
    forcing_functions_log: ForcingFunctionsLog


# ============================================================================
# PRIORS SCHEMAS (Phase 0c)
# ============================================================================

class HypothesisPrior(StrictModel):
    """Prior probability for a single hypothesis"""
    hypothesis_id: str = Field(description="Hypothesis identifier like H0, H1")
    prior: float = Field(ge=0.0, le=1.0, description="Prior probability P(H|K)")
    justification: str = Field(description="Brief justification for this prior")


class ParadigmPriorSet(StrictModel):
    """Prior assignments for all hypotheses under one paradigm"""
    paradigm_id: str = Field(description="Paradigm identifier like K1, K2")
    hypothesis_priors: List[HypothesisPrior] = Field(
        description="Prior assignments for each hypothesis"
    )


class PriorsByParadigm(StrictModel):
    """Complete prior assignments for all paradigms"""
    paradigm_priors: List[ParadigmPriorSet] = Field(
        description="Prior assignments organized by paradigm"
    )


# ============================================================================
# EVIDENCE SCHEMAS (Phase 2)
# ============================================================================

EvidenceType = Literal[
    "quantitative", "qualitative", "expert_testimony",
    "historical_analogy", "policy", "institutional"
]


class EvidenceItem(StrictModel):
    """A single piece of evidence gathered from research"""
    evidence_id: str = Field(description="Unique identifier like E1, E2")
    description: str = Field(description="Brief description of the evidence")
    source_name: str = Field(description="Publication or website name")
    source_url: str = Field(description="Full URL to the source")
    citation_apa: str = Field(description="APA format citation")
    date_accessed: str = Field(description="Date accessed in YYYY-MM-DD format")
    supports_hypotheses: List[str] = Field(
        description="Hypothesis IDs this evidence supports"
    )
    refutes_hypotheses: List[str] = Field(
        description="Hypothesis IDs this evidence refutes"
    )
    evidence_type: EvidenceType


class EvidenceList(StrictModel):
    """Complete list of evidence items"""
    evidence_items: List[EvidenceItem] = Field(
        description="15-25 evidence items across all hypotheses"
    )


# ============================================================================
# LIKELIHOOD SCHEMAS (Phase 3)
# ============================================================================

class HypothesisLikelihood(StrictModel):
    """Likelihood for a single hypothesis"""
    hypothesis_id: str = Field(description="Hypothesis identifier like H0, H1")
    probability: float = Field(ge=0.0, le=1.0, description="Likelihood probability P(E|H,K)")
    justification: str = Field(description="Brief justification for this likelihood")


class ParadigmLikelihoodSet(StrictModel):
    """Likelihoods for all hypotheses under one paradigm"""
    paradigm_id: str = Field(description="Paradigm identifier like K1, K2")
    hypothesis_likelihoods: List[HypothesisLikelihood] = Field(
        description="Likelihood assignments for each hypothesis"
    )


class EvidenceCluster(StrictModel):
    """A cluster of related evidence items"""
    cluster_id: str = Field(description="Unique identifier like C1, C2")
    cluster_name: str = Field(description="Short descriptive name")
    description: str = Field(description="What evidence this cluster contains")
    evidence_ids: List[str] = Field(description="IDs of evidence items in this cluster")
    paradigm_likelihoods: List[ParadigmLikelihoodSet] = Field(
        description="Likelihood assignments organized by paradigm"
    )


class EvidenceClusterList(StrictModel):
    """Complete list of evidence clusters with likelihoods"""
    clusters: List[EvidenceCluster] = Field(
        description="3-5 evidence clusters"
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_paradigm_schema() -> dict:
    """Get JSON schema for paradigm generation"""
    return ParadigmList.model_json_schema()


def get_hypotheses_schema() -> dict:
    """Get JSON schema for hypothesis generation"""
    return HypothesesWithForcingFunctions.model_json_schema()


def get_priors_schema() -> dict:
    """Get JSON schema for prior assignment"""
    return PriorsByParadigm.model_json_schema()


def get_evidence_schema() -> dict:
    """Get JSON schema for evidence gathering"""
    return EvidenceList.model_json_schema()


def get_clusters_schema() -> dict:
    """Get JSON schema for likelihood clusters"""
    return EvidenceClusterList.model_json_schema()


# ============================================================================
# SCHEMA DEFINITIONS FOR OPENAI API
# ============================================================================

def get_openai_schema(schema_name: str) -> dict:
    """
    Get OpenAI-formatted JSON schema for response_format.

    Usage:
        response = client.responses.create(
            model="gpt-4o",
            input=prompt,
            response_format=get_openai_schema("paradigms")
        )
    """
    schemas = {
        "paradigms": {
            "type": "json_schema",
            "json_schema": {
                "name": "paradigm_list",
                "strict": True,
                "schema": ParadigmList.model_json_schema()
            }
        },
        "hypotheses": {
            "type": "json_schema",
            "json_schema": {
                "name": "hypotheses_with_forcing_functions",
                "strict": True,
                "schema": HypothesesWithForcingFunctions.model_json_schema()
            }
        },
        "priors": {
            "type": "json_schema",
            "json_schema": {
                "name": "priors_by_paradigm",
                "strict": True,
                "schema": PriorsByParadigm.model_json_schema()
            }
        },
        "evidence": {
            "type": "json_schema",
            "json_schema": {
                "name": "evidence_list",
                "strict": True,
                "schema": EvidenceList.model_json_schema()
            }
        },
        "clusters": {
            "type": "json_schema",
            "json_schema": {
                "name": "evidence_cluster_list",
                "strict": True,
                "schema": EvidenceClusterList.model_json_schema()
            }
        }
    }

    return schemas.get(schema_name, {"type": "text"})
