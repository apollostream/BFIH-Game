#!/usr/bin/env python3
"""
BFIH Cross-Analysis Integrator

Integrates findings across multiple BFIH analyses, identifying tensions,
reinforcements, and generating meta-evidence for synthesis.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Tension:
    """Represents a tension or conflict between analysis findings."""
    topic_a: str
    topic_b: str
    description: str
    severity: str  # "minor", "moderate", "major"
    hypothesis_a: str
    hypothesis_b: str
    resolution_hints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_a": self.topic_a,
            "topic_b": self.topic_b,
            "description": self.description,
            "severity": self.severity,
            "hypothesis_a": self.hypothesis_a,
            "hypothesis_b": self.hypothesis_b,
            "resolution_hints": self.resolution_hints
        }


@dataclass
class Reinforcement:
    """Represents mutual support between analysis findings."""
    topics: List[str]
    description: str
    strength: str  # "weak", "moderate", "strong"
    supporting_hypotheses: List[str]
    combined_confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topics": self.topics,
            "description": self.description,
            "strength": self.strength,
            "supporting_hypotheses": self.supporting_hypotheses,
            "combined_confidence": self.combined_confidence
        }


@dataclass
class UnifiedFindings:
    """Aggregated findings from multiple BFIH analyses."""
    verdicts: Dict[str, str]  # topic_id -> verdict
    winning_hypotheses: Dict[str, Tuple[str, float]]  # topic_id -> (hypothesis, posterior)
    posterior_distributions: Dict[str, Dict[str, Dict[str, float]]]  # topic_id -> paradigm -> hyp -> posterior
    key_evidence: Dict[str, List[str]]  # topic_id -> key evidence descriptions
    paradigm_sensitivities: Dict[str, Dict[str, str]]  # topic_id -> paradigm -> winning_hyp
    tensions: List[Tension]
    reinforcements: List[Reinforcement]
    total_evidence_items: int
    total_analyses: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdicts": self.verdicts,
            "winning_hypotheses": {k: {"hypothesis": v[0], "posterior": v[1]}
                                   for k, v in self.winning_hypotheses.items()},
            "posterior_distributions": self.posterior_distributions,
            "key_evidence": self.key_evidence,
            "paradigm_sensitivities": self.paradigm_sensitivities,
            "tensions": [t.to_dict() for t in self.tensions],
            "reinforcements": [r.to_dict() for r in self.reinforcements],
            "total_evidence_items": self.total_evidence_items,
            "total_analyses": self.total_analyses
        }

    def save(self, path: str) -> None:
        """Save unified findings to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class CrossAnalysisIntegrator:
    """
    Integrates findings across multiple BFIH analyses.

    Capabilities:
    - Extract verdicts, posteriors, and key findings from each analysis
    - Identify logical tensions between conclusions
    - Identify reinforcing patterns across analyses
    - Generate meta-evidence items for synthesis analysis
    """

    def __init__(self, results: Dict[str, Any]):
        """
        Initialize with analysis results.

        Args:
            results: Dictionary mapping topic_id to AnalysisResult objects or dicts
        """
        self.results = results

    def extract_unified_findings(self) -> UnifiedFindings:
        """
        Extract structured findings from all analyses.

        Returns:
            UnifiedFindings object containing integrated data
        """
        verdicts = self._extract_verdicts()
        winning_hypotheses = self._extract_winners()
        posterior_distributions = self._extract_posteriors()
        key_evidence = self._extract_key_evidence()
        paradigm_sensitivities = self._extract_sensitivities()
        tensions = self._identify_tensions()
        reinforcements = self._identify_reinforcements()
        total_evidence = self._count_total_evidence()

        return UnifiedFindings(
            verdicts=verdicts,
            winning_hypotheses=winning_hypotheses,
            posterior_distributions=posterior_distributions,
            key_evidence=key_evidence,
            paradigm_sensitivities=paradigm_sensitivities,
            tensions=tensions,
            reinforcements=reinforcements,
            total_evidence_items=total_evidence,
            total_analyses=len(self.results)
        )

    def _extract_verdicts(self) -> Dict[str, str]:
        """Extract verdict from each analysis."""
        verdicts = {}
        for topic_id, result in self.results.items():
            if hasattr(result, 'verdict'):
                verdicts[topic_id] = result.verdict
            elif isinstance(result, dict):
                verdicts[topic_id] = result.get('verdict', 'UNKNOWN')
        return verdicts

    def _extract_winners(self) -> Dict[str, Tuple[str, float]]:
        """Extract winning hypothesis and posterior from each analysis."""
        winners = {}
        for topic_id, result in self.results.items():
            if hasattr(result, 'winning_hypothesis'):
                winners[topic_id] = (result.winning_hypothesis, result.winning_posterior)
            elif isinstance(result, dict):
                winners[topic_id] = (
                    result.get('winning_hypothesis', 'Unknown'),
                    result.get('winning_posterior', 0.0)
                )
        return winners

    def _extract_posteriors(self) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Extract full posterior distributions from each analysis."""
        posteriors = {}
        for topic_id, result in self.results.items():
            if hasattr(result, 'posteriors'):
                posteriors[topic_id] = result.posteriors
            elif isinstance(result, dict):
                posteriors[topic_id] = result.get('posteriors', {})
        return posteriors

    def _extract_key_evidence(self) -> Dict[str, List[str]]:
        """Extract key evidence descriptions from each analysis."""
        evidence = {}
        for topic_id, result in self.results.items():
            key_findings = []
            if hasattr(result, 'key_findings'):
                key_findings = result.key_findings
            elif isinstance(result, dict):
                key_findings = result.get('key_findings', [])

            # Also extract from summary if available
            summary = ""
            if hasattr(result, 'summary'):
                summary = result.summary
            elif isinstance(result, dict):
                summary = result.get('summary', '')

            if summary and summary not in key_findings:
                key_findings.insert(0, summary[:300])

            evidence[topic_id] = key_findings
        return evidence

    def _extract_sensitivities(self) -> Dict[str, Dict[str, str]]:
        """Extract paradigm sensitivity (which hypothesis wins under each paradigm)."""
        sensitivities = {}
        for topic_id, result in self.results.items():
            posteriors = {}
            if hasattr(result, 'posteriors'):
                posteriors = result.posteriors
            elif isinstance(result, dict):
                posteriors = result.get('posteriors', {})

            paradigm_winners = {}
            for paradigm_id, hyp_posteriors in posteriors.items():
                if hyp_posteriors:
                    winner = max(hyp_posteriors.items(), key=lambda x: x[1])
                    paradigm_winners[paradigm_id] = winner[0]

            sensitivities[topic_id] = paradigm_winners
        return sensitivities

    def _identify_tensions(self) -> List[Tension]:
        """
        Identify logical tensions between analysis conclusions.

        Tension types:
        - Direct contradiction: One analysis supports X, another refutes X
        - Paradigm conflict: Same paradigm yields opposite conclusions
        - Dependency conflict: Dependent analysis contradicts its dependency
        """
        tensions = []

        # Define semantic tension mappings
        # These are conceptual oppositions that might indicate tensions
        tension_pairs = [
            # Consciousness-related
            ("functionalist", "biological"),
            ("computational", "embodied"),
            ("illusionist", "realist"),
            ("continuous", "discontinuous"),
            # General epistemic
            ("validated", "refuted"),
            ("true", "false"),
            ("possible", "impossible")
        ]

        topic_ids = list(self.results.keys())

        for i, topic_a in enumerate(topic_ids):
            for topic_b in topic_ids[i+1:]:
                result_a = self.results[topic_a]
                result_b = self.results[topic_b]

                # Get winning hypotheses
                hyp_a = self._get_winning_hypothesis_name(result_a)
                hyp_b = self._get_winning_hypothesis_name(result_b)
                verdict_a = self._get_verdict(result_a)
                verdict_b = self._get_verdict(result_b)

                # Check for direct verdict conflicts
                if self._verdicts_conflict(verdict_a, verdict_b, topic_a, topic_b):
                    tensions.append(Tension(
                        topic_a=topic_a,
                        topic_b=topic_b,
                        description=f"Verdict conflict: {topic_a} is {verdict_a} while {topic_b} is {verdict_b}",
                        severity="moderate",
                        hypothesis_a=hyp_a,
                        hypothesis_b=hyp_b,
                        resolution_hints=[
                            "Consider whether the topics address different aspects of the same question",
                            "Check if paradigm differences explain the divergence"
                        ]
                    ))

                # Check for semantic tensions in hypothesis names
                for term_a, term_b in tension_pairs:
                    if (term_a in hyp_a.lower() and term_b in hyp_b.lower()) or \
                       (term_b in hyp_a.lower() and term_a in hyp_b.lower()):
                        tensions.append(Tension(
                            topic_a=topic_a,
                            topic_b=topic_b,
                            description=f"Conceptual tension: {hyp_a} vs {hyp_b}",
                            severity="minor",
                            hypothesis_a=hyp_a,
                            hypothesis_b=hyp_b,
                            resolution_hints=[
                                f"The '{term_a}' and '{term_b}' positions may not be mutually exclusive",
                                "A synthesis might accommodate both findings"
                            ]
                        ))
                        break  # Only report one tension type per pair

        return tensions

    def _identify_reinforcements(self) -> List[Reinforcement]:
        """
        Identify mutually reinforcing patterns across analyses.

        Reinforcement types:
        - Concordant verdicts: Multiple analyses reach similar conclusions
        - Paradigm consistency: Same conclusion across paradigms
        - Conceptual alignment: Hypotheses that logically support each other
        """
        reinforcements = []

        # Group by verdict
        verdict_groups: Dict[str, List[str]] = {}
        for topic_id, result in self.results.items():
            verdict = self._get_verdict(result)
            if verdict not in verdict_groups:
                verdict_groups[verdict] = []
            verdict_groups[verdict].append(topic_id)

        # Report concordant verdicts
        for verdict, topics in verdict_groups.items():
            if len(topics) > 1 and verdict not in ["UNKNOWN", "INDETERMINATE"]:
                avg_confidence = self._compute_average_confidence(topics)
                reinforcements.append(Reinforcement(
                    topics=topics,
                    description=f"Concordant {verdict} verdicts across {len(topics)} analyses",
                    strength="strong" if avg_confidence > 0.6 else "moderate",
                    supporting_hypotheses=[self._get_winning_hypothesis_name(self.results[t]) for t in topics],
                    combined_confidence=avg_confidence
                ))

        # Check for paradigm consistency
        consistent_topics = self._find_paradigm_consistent_topics()
        if len(consistent_topics) > 1:
            reinforcements.append(Reinforcement(
                topics=consistent_topics,
                description="Conclusions robust across multiple paradigms",
                strength="strong",
                supporting_hypotheses=[self._get_winning_hypothesis_name(self.results[t]) for t in consistent_topics],
                combined_confidence=self._compute_average_confidence(consistent_topics)
            ))

        # Check for conceptual alignment
        alignments = self._find_conceptual_alignments()
        for aligned_topics, description in alignments:
            if len(aligned_topics) > 1:
                reinforcements.append(Reinforcement(
                    topics=aligned_topics,
                    description=description,
                    strength="moderate",
                    supporting_hypotheses=[self._get_winning_hypothesis_name(self.results[t]) for t in aligned_topics],
                    combined_confidence=self._compute_average_confidence(aligned_topics)
                ))

        return reinforcements

    def _verdicts_conflict(self, verdict_a: str, verdict_b: str, topic_a: str, topic_b: str) -> bool:
        """Determine if two verdicts are in conflict given their topics."""
        # Direct opposites
        if (verdict_a == "VALIDATED" and verdict_b == "REFUTED") or \
           (verdict_a == "REFUTED" and verdict_b == "VALIDATED"):
            # Only a real conflict if topics are related
            return self._topics_related(topic_a, topic_b)
        return False

    def _topics_related(self, topic_a: str, topic_b: str) -> bool:
        """Heuristic check if two topics are semantically related."""
        # Simple keyword overlap check
        words_a = set(topic_a.lower().replace("_", " ").split())
        words_b = set(topic_b.lower().replace("_", " ").split())
        overlap = words_a & words_b
        # Related if they share meaningful words
        stopwords = {"the", "a", "an", "is", "are", "can", "do", "does", "of", "and", "or"}
        meaningful_overlap = overlap - stopwords
        return len(meaningful_overlap) > 0

    def _find_paradigm_consistent_topics(self) -> List[str]:
        """Find topics where the winning hypothesis is consistent across paradigms."""
        consistent = []
        for topic_id, result in self.results.items():
            posteriors = {}
            if hasattr(result, 'posteriors'):
                posteriors = result.posteriors
            elif isinstance(result, dict):
                posteriors = result.get('posteriors', {})

            if not posteriors:
                continue

            # Check if same hypothesis wins across all paradigms
            winners = set()
            for paradigm_id, hyp_posteriors in posteriors.items():
                if hyp_posteriors:
                    winner = max(hyp_posteriors.items(), key=lambda x: x[1])
                    winners.add(winner[0])

            if len(winners) == 1:  # Same winner across all paradigms
                consistent.append(topic_id)

        return consistent

    def _find_conceptual_alignments(self) -> List[Tuple[List[str], str]]:
        """Find topics with conceptually aligned conclusions."""
        alignments = []

        # Define alignment patterns
        alignment_keywords = {
            "partial": ["conditional", "contextual", "qualified"],
            "negative": ["refuted", "false", "no", "cannot"],
            "positive": ["validated", "true", "yes", "can"],
            "uncertain": ["indeterminate", "unknown", "unclear"]
        }

        for category, keywords in alignment_keywords.items():
            aligned = []
            for topic_id, result in self.results.items():
                hyp = self._get_winning_hypothesis_name(result).lower()
                verdict = self._get_verdict(result).lower()
                if any(kw in hyp or kw in verdict for kw in keywords):
                    aligned.append(topic_id)

            if len(aligned) > 1:
                alignments.append((aligned, f"Conceptually aligned conclusions ({category})"))

        return alignments

    def _get_winning_hypothesis_name(self, result: Any) -> str:
        """Extract winning hypothesis name from result."""
        if hasattr(result, 'winning_hypothesis'):
            return result.winning_hypothesis
        elif isinstance(result, dict):
            return result.get('winning_hypothesis', 'Unknown')
        return 'Unknown'

    def _get_verdict(self, result: Any) -> str:
        """Extract verdict from result."""
        if hasattr(result, 'verdict'):
            return result.verdict
        elif isinstance(result, dict):
            return result.get('verdict', 'UNKNOWN')
        return 'UNKNOWN'

    def _compute_average_confidence(self, topics: List[str]) -> float:
        """Compute average winning posterior across topics."""
        posteriors = []
        for topic_id in topics:
            result = self.results[topic_id]
            if hasattr(result, 'winning_posterior'):
                posteriors.append(result.winning_posterior)
            elif isinstance(result, dict):
                posteriors.append(result.get('winning_posterior', 0.0))

        return sum(posteriors) / len(posteriors) if posteriors else 0.0

    def _count_total_evidence(self) -> int:
        """Count total evidence items across all analyses."""
        total = 0
        for result in self.results.values():
            if hasattr(result, 'evidence_count'):
                total += result.evidence_count
            elif isinstance(result, dict):
                total += result.get('evidence_count', 0)
        return total

    def generate_meta_evidence(self) -> List[Dict]:
        """
        Convert analysis conclusions into evidence items for meta-analysis.

        Each component analysis becomes an evidence item with its conclusion
        as the description. The meta-analysis then evaluates which grand
        synthesis hypothesis best accounts for these findings.

        Returns:
            List of evidence items in standard BFIH format
        """
        evidence_items = []

        for topic_id, result in self.results.items():
            # Extract result data
            if hasattr(result, 'proposition'):
                proposition = result.proposition
            elif isinstance(result, dict):
                proposition = result.get('proposition', topic_id)
            else:
                proposition = topic_id

            verdict = self._get_verdict(result)
            hyp_name = self._get_winning_hypothesis_name(result)

            if hasattr(result, 'winning_posterior'):
                posterior = result.winning_posterior
            elif isinstance(result, dict):
                posterior = result.get('winning_posterior', 0.0)
            else:
                posterior = 0.0

            summary = ""
            if hasattr(result, 'summary'):
                summary = result.summary
            elif isinstance(result, dict):
                summary = result.get('summary', '')

            # Build evidence item
            description = f"""BFIH Analysis of "{proposition}"
Verdict: {verdict}
Winning Hypothesis: {hyp_name} (posterior: {posterior:.1%})
Summary: {summary[:500]}"""

            evidence_items.append({
                "evidence_id": f"META_{topic_id}",
                "description": description,
                "source_name": f"BFIH Analysis: {topic_id}",
                "source_url": f"internal://{topic_id}",
                "evidence_type": "systematic_analysis",
                "supports_hypotheses": [],  # To be filled by meta-analysis
                "refutes_hypotheses": [],
                "meta_data": {
                    "original_topic": topic_id,
                    "original_proposition": proposition,
                    "original_verdict": verdict,
                    "original_winner": hyp_name,
                    "original_posterior": posterior
                }
            })

        return evidence_items


def integrate_results(results: Dict[str, Any]) -> Tuple[UnifiedFindings, List[Dict]]:
    """
    Convenience function to integrate analysis results.

    Args:
        results: Dictionary mapping topic_id to AnalysisResult

    Returns:
        Tuple of (UnifiedFindings, meta_evidence_items)
    """
    integrator = CrossAnalysisIntegrator(results)
    findings = integrator.extract_unified_findings()
    meta_evidence = integrator.generate_meta_evidence()
    return findings, meta_evidence


if __name__ == "__main__":
    # Test with mock data
    mock_results = {
        "consciousness": {
            "proposition": "Can LLMs have subjective experience?",
            "verdict": "INDETERMINATE",
            "winning_hypothesis": "Other/Unforeseen",
            "winning_posterior": 0.20,
            "posteriors": {"K0": {"H0": 0.20, "H1": 0.15}},
            "summary": "No existing theory adequately accounts for the evidence.",
            "evidence_count": 82
        },
        "illusionism": {
            "proposition": "Is phenomenal consciousness illusory?",
            "verdict": "PARTIALLY_SUPPORTED",
            "winning_hypothesis": "Moderate Illusionism",
            "winning_posterior": 0.35,
            "posteriors": {"K0": {"H0": 0.35, "H1": 0.30}},
            "summary": "Evidence supports that qualia may be introspective constructs.",
            "evidence_count": 45
        }
    }

    findings, meta_evidence = integrate_results(mock_results)

    print("=== Unified Findings ===")
    print(f"Analyses: {findings.total_analyses}")
    print(f"Total evidence: {findings.total_evidence_items}")
    print(f"Tensions: {len(findings.tensions)}")
    print(f"Reinforcements: {len(findings.reinforcements)}")

    print("\n=== Meta-Evidence ===")
    for item in meta_evidence:
        print(f"  {item['evidence_id']}: {item['description'][:100]}...")
