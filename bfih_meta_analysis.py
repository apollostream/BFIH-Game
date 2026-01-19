#!/usr/bin/env python3
"""
BFIH Meta-Analysis Engine

Performs BFIH analysis at the meta-level, treating component analysis
conclusions as evidence to evaluate grand synthesis hypotheses.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

from bfih_cross_analysis import UnifiedFindings, Tension, Reinforcement
from hermeneutic_config_schema import MetaAnalysisConfig

logger = logging.getLogger(__name__)


class MetaAnalysisEngine:
    """
    Performs BFIH analysis at the meta-level.

    The meta-analysis treats conclusions from component analyses as evidence
    and evaluates which grand synthesis hypothesis best accounts for the
    pattern of findings.
    """

    # Default meta-paradigms for philosophical synthesis
    DEFAULT_META_PARADIGMS = [
        {
            "id": "K0",
            "name": "Integrative Naturalist",
            "description": "Seeks coherent naturalistic account that unifies findings across domains",
            "epistemic_stance": {
                "ontology": "Material and emergent phenomena",
                "epistemology": "Empirical integration with theoretical coherence",
                "methodology": "Synthesis of evidence across paradigms"
            }
        },
        {
            "id": "K1",
            "name": "Reductive Physicalist",
            "description": "All mental and social phenomena reduce to physical processes",
            "epistemic_stance": {
                "ontology": "Physical substrate as fundamental",
                "epistemology": "Bottom-up explanation from physics",
                "methodology": "Reduction to lower-level mechanisms"
            }
        },
        {
            "id": "K2",
            "name": "Property Dualist",
            "description": "Mental properties are ontologically distinct but depend on physical",
            "epistemic_stance": {
                "ontology": "Physical and mental as distinct but related",
                "epistemology": "Both physical and phenomenological methods valid",
                "methodology": "Dual-aspect analysis"
            }
        },
        {
            "id": "K3",
            "name": "Pragmatic Functionalist",
            "description": "Focus on functional roles and practical implications, bracket metaphysics",
            "epistemic_stance": {
                "ontology": "Functional organization as primary",
                "epistemology": "Pragmatic truth via successful prediction",
                "methodology": "Functional analysis without metaphysical commitment"
            }
        },
        {
            "id": "K4",
            "name": "Phenomenological Traditionalist",
            "description": "First-person experience as irreducible primary datum",
            "epistemic_stance": {
                "ontology": "Consciousness as foundational",
                "epistemology": "Phenomenological investigation primary",
                "methodology": "Descriptive analysis of experience"
            }
        }
    ]

    def __init__(
        self,
        unified_findings: UnifiedFindings,
        meta_config: MetaAnalysisConfig,
        orchestrator: Optional[Any] = None
    ):
        """
        Initialize the meta-analysis engine.

        Args:
            unified_findings: Integrated findings from component analyses
            meta_config: Configuration for the meta-analysis
            orchestrator: Optional BFIHOrchestrator instance (created if not provided)
        """
        self.findings = unified_findings
        self.config = meta_config

        if orchestrator is None:
            from bfih_orchestrator_fixed import BFIHOrchestrator
            self.orchestrator = BFIHOrchestrator()
        else:
            self.orchestrator = orchestrator

    def run_meta_analysis(self, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Run BFIH analysis with component findings as evidence.

        Args:
            output_dir: Directory to save output files

        Returns:
            Analysis result dictionary
        """
        logger.info("Starting meta-analysis")
        logger.info(f"Proposition: {self.config.proposition}")
        logger.info(f"Input analyses: {self.findings.total_analyses}")
        logger.info(f"Total evidence items: {self.findings.total_evidence_items}")

        # Prepare meta-evidence from component findings
        meta_evidence = self._prepare_meta_evidence()
        logger.info(f"Generated {len(meta_evidence)} meta-evidence items")

        # Generate paradigms (use custom if provided, else defaults)
        paradigms = self._generate_meta_paradigms()
        logger.info(f"Using {len(paradigms)} meta-paradigms")

        # Generate hypotheses from config
        hypotheses = self._generate_meta_hypotheses()
        logger.info(f"Testing {len(hypotheses)} meta-hypotheses")

        # Generate priors
        priors_by_paradigm = self._generate_meta_priors(paradigms, hypotheses)

        # Build scenario config
        scenario_id = f"meta_{uuid.uuid4().hex[:8]}"
        scenario_config = {
            "schema_version": "1.0",
            "scenario_metadata": {
                "scenario_id": scenario_id,
                "title": "Meta-Analysis Synthesis",
                "description": f"Synthesizing {self.findings.total_analyses} component analyses",
                "domain": "philosophy",
                "difficulty": "hard"
            },
            "paradigms": paradigms,
            "hypotheses": hypotheses,
            "priors_by_paradigm": priors_by_paradigm,
            "meta_analysis_context": {
                "component_analyses": self.findings.total_analyses,
                "total_evidence": self.findings.total_evidence_items,
                "tensions": [t.to_dict() for t in self.findings.tensions],
                "reinforcements": [r.to_dict() for r in self.findings.reinforcements],
                "verdicts": self.findings.verdicts,
                "winning_hypotheses": {k: {"hypothesis": v[0], "posterior": v[1]}
                                       for k, v in self.findings.winning_hypotheses.items()}
            }
        }

        # Create analysis request
        from bfih_orchestrator_fixed import BFIHAnalysisRequest
        request = BFIHAnalysisRequest(
            scenario_id=scenario_id,
            proposition=self.config.proposition,
            scenario_config=scenario_config,
            reasoning_model=self.config.model
        )

        # Run analysis with injected evidence
        result = self.orchestrator.conduct_analysis_with_injected_evidence(
            request=request,
            injected_evidence=meta_evidence,
            skip_methodology=True
        )

        # Save outputs if directory provided
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Save report
            report_path = output_path / f"meta_analysis_{scenario_id}.md"
            with open(report_path, 'w') as f:
                f.write(result.report)

            # Save JSON
            json_path = output_path / f"meta_analysis_{scenario_id}.json"
            with open(json_path, 'w') as f:
                json.dump({
                    "analysis_id": result.analysis_id,
                    "scenario_id": result.scenario_id,
                    "proposition": result.proposition,
                    "posteriors": result.posteriors,
                    "metadata": result.metadata,
                    "created_at": result.created_at
                }, f, indent=2)

            logger.info(f"Saved meta-analysis report to: {report_path}")

        # Convert to dictionary for return
        return {
            "analysis_id": result.analysis_id,
            "scenario_id": result.scenario_id,
            "proposition": result.proposition,
            "report": result.report,
            "posteriors": result.posteriors,
            "metadata": result.metadata,
            "created_at": result.created_at,
            "scenario_config": scenario_config
        }

    def _prepare_meta_evidence(self) -> List[Dict]:
        """
        Prepare evidence items from component analysis conclusions.

        Each component analysis becomes an evidence item, with its verdict,
        winning hypothesis, and key findings as the evidence description.
        """
        evidence_items = []

        for topic_id, (hyp_name, posterior) in self.findings.winning_hypotheses.items():
            verdict = self.findings.verdicts.get(topic_id, "UNKNOWN")
            key_evidence = self.findings.key_evidence.get(topic_id, [])

            # Build detailed description
            description = f"""Component Analysis: {topic_id}
Verdict: {verdict}
Leading Hypothesis: {hyp_name}
Posterior Probability: {posterior:.1%}
Key Findings: {'; '.join(key_evidence[:3]) if key_evidence else 'None extracted'}"""

            # Determine which meta-hypotheses this might support/refute
            # This is a heuristic mapping based on hypothesis keywords
            supports = []
            refutes = []

            # Add evidence item
            evidence_items.append({
                "evidence_id": f"META_{topic_id}",
                "description": description,
                "source_name": f"BFIH Analysis: {topic_id}",
                "source_url": f"internal://analysis/{topic_id}",
                "evidence_type": "systematic_analysis",
                "supports_hypotheses": supports,
                "refutes_hypotheses": refutes,
                "metadata": {
                    "topic_id": topic_id,
                    "verdict": verdict,
                    "winning_hypothesis": hyp_name,
                    "posterior": posterior
                }
            })

        # Add tension evidence
        for i, tension in enumerate(self.findings.tensions):
            evidence_items.append({
                "evidence_id": f"TENSION_{i}",
                "description": f"Identified Tension: {tension.description} (Severity: {tension.severity})",
                "source_name": "Cross-Analysis Integration",
                "source_url": "internal://cross_analysis",
                "evidence_type": "analytical_finding",
                "supports_hypotheses": [],
                "refutes_hypotheses": [],
                "metadata": tension.to_dict()
            })

        # Add reinforcement evidence
        for i, reinforcement in enumerate(self.findings.reinforcements):
            evidence_items.append({
                "evidence_id": f"REINFORCE_{i}",
                "description": f"Identified Reinforcement: {reinforcement.description} (Strength: {reinforcement.strength})",
                "source_name": "Cross-Analysis Integration",
                "source_url": "internal://cross_analysis",
                "evidence_type": "analytical_finding",
                "supports_hypotheses": [],
                "refutes_hypotheses": [],
                "metadata": reinforcement.to_dict()
            })

        return evidence_items

    def _generate_meta_paradigms(self) -> List[Dict]:
        """Generate paradigms for meta-analysis."""
        if self.config.custom_paradigms:
            return self.config.custom_paradigms
        return self.DEFAULT_META_PARADIGMS

    def _generate_meta_hypotheses(self) -> List[Dict]:
        """Generate hypotheses from configuration."""
        hypotheses = []

        # Always include H0 as catch-all
        hypotheses.append({
            "id": "H0",
            "name": "Other/Unforeseen",
            "short_name": "OTHER",
            "description": "None of the specified hypotheses adequately accounts for the pattern of findings; an alternative framework is needed.",
            "verdict_if_true": "INDETERMINATE"
        })

        for i, h in enumerate(self.config.hypotheses, 1):
            if isinstance(h, dict):
                hypotheses.append({
                    "id": h.get("id", f"H{i}"),
                    "name": h.get("name", f"Hypothesis {i}"),
                    "short_name": h.get("short_name", h.get("name", f"H{i}")[:20]),
                    "description": h.get("description", ""),
                    "verdict_if_true": h.get("verdict_if_true", "PARTIALLY_SUPPORTED")
                })
            else:
                # String hypothesis - parse "Name: Description" format
                if ":" in str(h):
                    parts = str(h).split(":", 1)
                    name = parts[0].strip()
                    description = parts[1].strip()
                else:
                    name = f"Hypothesis {i}"
                    description = str(h)

                hypotheses.append({
                    "id": f"H{i}",
                    "name": name,
                    "short_name": name[:20],
                    "description": description,
                    "verdict_if_true": "PARTIALLY_SUPPORTED"
                })

        return hypotheses

    def _generate_meta_priors(
        self,
        paradigms: List[Dict],
        hypotheses: List[Dict]
    ) -> Dict[str, Dict[str, float]]:
        """
        Generate prior probabilities for meta-hypotheses under each paradigm.

        Uses a principled approach where:
        - H0 (Other) gets moderate prior (acknowledging our uncertainty)
        - Remaining probability distributed based on paradigm alignment
        """
        priors_by_paradigm = {}
        n_hyp = len(hypotheses)

        for paradigm in paradigms:
            paradigm_id = paradigm["id"]
            paradigm_name = paradigm.get("name", "").lower()

            # Start with uniform priors
            priors = {h["id"]: 1.0 / n_hyp for h in hypotheses}

            # Adjust based on paradigm-hypothesis alignment
            for h in hypotheses:
                h_name = h.get("name", "").lower()
                h_desc = h.get("description", "").lower()

                # Boost aligned hypotheses
                if "naturalist" in paradigm_name:
                    if "naturalist" in h_name or "integrative" in h_desc:
                        priors[h["id"]] *= 1.3
                elif "physicalist" in paradigm_name or "reductive" in paradigm_name:
                    if "physical" in h_name or "reductive" in h_desc or "biological" in h_desc:
                        priors[h["id"]] *= 1.3
                elif "dualist" in paradigm_name:
                    if "dual" in h_name or "property" in h_desc:
                        priors[h["id"]] *= 1.3
                elif "functionalist" in paradigm_name:
                    if "function" in h_name or "pragmatic" in h_desc:
                        priors[h["id"]] *= 1.3
                elif "phenomenolog" in paradigm_name:
                    if "phenomeno" in h_name or "experience" in h_desc or "conscious" in h_desc:
                        priors[h["id"]] *= 1.3

            # Normalize
            total = sum(priors.values())
            priors = {k: v / total for k, v in priors.items()}

            priors_by_paradigm[paradigm_id] = priors

        return priors_by_paradigm


def run_meta_analysis(
    unified_findings: UnifiedFindings,
    proposition: str,
    hypotheses: List[Dict],
    model: str = "o3",
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to run a meta-analysis.

    Args:
        unified_findings: Integrated findings from component analyses
        proposition: The meta-analysis proposition
        hypotheses: List of meta-hypotheses to evaluate
        model: Model to use for reasoning
        output_dir: Directory to save outputs

    Returns:
        Meta-analysis result dictionary
    """
    config = MetaAnalysisConfig(
        proposition=proposition,
        hypotheses=hypotheses,
        model=model
    )

    engine = MetaAnalysisEngine(unified_findings, config)
    return engine.run_meta_analysis(output_dir)


if __name__ == "__main__":
    # Test with mock unified findings
    from bfih_cross_analysis import UnifiedFindings, Tension, Reinforcement

    mock_findings = UnifiedFindings(
        verdicts={"consciousness": "INDETERMINATE", "illusionism": "PARTIALLY_SUPPORTED"},
        winning_hypotheses={
            "consciousness": ("Other/Unforeseen", 0.20),
            "illusionism": ("Moderate Illusionism", 0.35)
        },
        posterior_distributions={},
        key_evidence={
            "consciousness": ["No existing theory adequate"],
            "illusionism": ["Qualia may be introspective constructs"]
        },
        paradigm_sensitivities={},
        tensions=[],
        reinforcements=[],
        total_evidence_items=127,
        total_analyses=2
    )

    config = MetaAnalysisConfig(
        proposition="What unified theory of mind best accounts for these findings?",
        hypotheses=[
            {"id": "H1", "name": "Functionalist Coherentism", "description": "Computational organization is sufficient"},
            {"id": "H2", "name": "Biological Exceptionalism", "description": "Only biological systems can be conscious"},
            {"id": "H3", "name": "Graded Mentality", "description": "Mental properties exist on a continuum"}
        ],
        model="o3-mini"  # Use cheaper model for test
    )

    print("Meta-analysis configuration ready")
    print(f"  Proposition: {config.proposition}")
    print(f"  Hypotheses: {len(config.hypotheses)}")
    print(f"  Model: {config.model}")
