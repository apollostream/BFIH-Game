#!/usr/bin/env python3
"""
Calibration test: Homeopathy efficacy (expected: FALSE) - CACHED VERSION

This version loads evidence from a previous run to skip the web search phase,
allowing fast comparison of different reasoning models on identical evidence.
"""

import sys
import os
import json
import uuid
import argparse
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(override=True)

from bfih_orchestrator_fixed import BFIHOrchestrator, BFIHAnalysisRequest

# Forced hypothesis set for homeopathy efficacy
FORCED_SCENARIO_CONFIG = {
    "proposition": "Does homeopathy work better than placebo for treating medical conditions?",
    "domain": "medicine",
    "difficulty": "hard",

    # Forced paradigms
    "paradigms": [
        {
            "id": "K0",
            "name": "Scientific Consensus",
            "description": "Mainstream scientific and medical consensus based on RCTs, meta-analyses, and mechanistic understanding.",
            "ontology": "Material, measurable biological and chemical processes",
            "epistemology": "Empirical observation, RCTs, systematic reviews, falsification",
            "axiology": "Evidence-based medicine, patient safety, reproducibility"
        },
        {
            "id": "K1",
            "name": "Integrative Medicine Advocate",
            "description": "Perspective that values holistic approaches and considers patient-reported outcomes alongside RCTs.",
            "ontology": "Mind-body connection, vitalistic principles",
            "epistemology": "Clinical experience, patient narratives, holistic assessment",
            "axiology": "Patient autonomy, whole-person care, therapeutic relationship"
        },
        {
            "id": "K2",
            "name": "Skeptical Empiricist",
            "description": "Strictly materialist view that demands mechanistic explanations and rejects implausible claims.",
            "ontology": "Physical matter and measurable forces only",
            "epistemology": "Mechanism-first, extraordinary claims require extraordinary evidence",
            "axiology": "Scientific rigor, preventing harm from ineffective treatments"
        }
    ],

    # FORCED HYPOTHESES - TRUE/FALSE/PARTIAL options
    "hypotheses": [
        {
            "id": "H0",
            "name": "OTHER - Unforeseen explanation",
            "short_name": "Unforeseen",
            "description": "Some unknown mechanism not captured by the other hypotheses explains homeopathy's observed effects (or lack thereof).",
            "verdict_type": "OTHER"
        },
        {
            "id": "H1",
            "name": "TRUE - Homeopathy has specific therapeutic effects",
            "short_name": "Specific Effects",
            "description": "Homeopathic remedies have specific therapeutic effects beyond placebo through an as-yet-unknown mechanism (e.g., water memory, quantum effects, nanoparticles).",
            "verdict_type": "TRUE"
        },
        {
            "id": "H2",
            "name": "FALSE - No effect beyond placebo",
            "short_name": "No Effect",
            "description": "Homeopathic remedies have no specific therapeutic effect beyond placebo. Any perceived benefits are due to placebo effect, regression to mean, natural recovery, or concurrent conventional treatment.",
            "verdict_type": "FALSE"
        },
        {
            "id": "H3",
            "name": "PARTIAL - Works for some conditions only",
            "short_name": "Condition-Specific",
            "description": "Homeopathy has specific effects for certain conditions (e.g., allergies, anxiety) but not others. The mechanism may be placebo-enhanced or condition-specific.",
            "verdict_type": "PARTIAL"
        },
        {
            "id": "H4",
            "name": "PARTIAL - Therapeutic ritual effect",
            "short_name": "Ritual Effect",
            "description": "Homeopathy's effects come not from the remedies themselves but from the extended consultation, individualized attention, and therapeutic relationship - a real but non-specific effect.",
            "verdict_type": "PARTIAL"
        },
        {
            "id": "H5",
            "name": "PARTIAL - Low-dose hormesis",
            "short_name": "Hormesis",
            "description": "Some homeopathic preparations at lower dilutions (not ultra-diluted) may have hormetic effects - beneficial responses to low-dose stressors - but this doesn't apply to standard ultra-diluted preparations.",
            "verdict_type": "PARTIAL"
        }
    ],

    # Priors by paradigm - designed for clear test
    "priors_by_paradigm": {
        "K0": {
            "H0": 0.05,   # Low - well-studied topic
            "H1": 0.05,   # Low - contradicts physics/chemistry
            "H2": 0.60,   # High - matches scientific consensus
            "H3": 0.10,   # Low but possible
            "H4": 0.15,   # Plausible - consultation effect is real
            "H5": 0.05    # Low - doesn't apply to standard homeopathy
        },
        "K1": {
            "H0": 0.10,
            "H1": 0.30,   # Integrative view more open to alternative mechanisms
            "H2": 0.15,   # Lower credence in pure placebo
            "H3": 0.20,
            "H4": 0.20,
            "H5": 0.05
        },
        "K2": {
            "H0": 0.05,
            "H1": 0.02,   # Skeptic strongly doubts specific effects
            "H2": 0.75,   # Strong prior for no effect
            "H3": 0.05,
            "H4": 0.10,   # Accepts consultation effect
            "H5": 0.03
        }
    }
}


def load_cached_evidence(cache_file: str) -> list:
    """Load evidence items from a previous run's JSON output."""
    with open(cache_file, 'r') as f:
        data = json.load(f)

    evidence_items = data.get("metadata", {}).get("evidence_items", [])
    if not evidence_items:
        raise ValueError(f"No evidence_items found in {cache_file}")

    return evidence_items


def run_forced_hypothesis_test_cached(
    reasoning_model: str = "o3",
    cache_file: str = None,
    output_dir: str = "calibration_tests/homeopathy_forced"
):
    """Run BFIH analysis with forced hypothesis set using cached evidence."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Find cache file if not specified
    if cache_file is None:
        json_files = list(output_path.glob("bfih_report_*.json"))
        if not json_files:
            raise ValueError(f"No cached evidence files found in {output_dir}. Run the full test first.")
        cache_file = str(sorted(json_files)[-1])  # Use most recent

    print("=" * 70)
    print(f"BFIH CALIBRATION TEST: Homeopathy Efficacy (CACHED - {reasoning_model})")
    print("=" * 70)
    print(f"\nProposition: {FORCED_SCENARIO_CONFIG['proposition']}")
    print(f"Reasoning Model: {reasoning_model}")
    print(f"Evidence Cache: {cache_file}")
    print(f"\nForced Hypotheses:")
    for h in FORCED_SCENARIO_CONFIG['hypotheses']:
        print(f"  {h['id']}: {h['name']}")
    print(f"\nOutput: {output_dir}")
    print("=" * 70)

    # Load cached evidence
    print(f"\nLoading cached evidence from: {cache_file}")
    evidence_items = load_cached_evidence(cache_file)
    print(f"Loaded {len(evidence_items)} evidence items")

    # Initialize orchestrator
    orchestrator = BFIHOrchestrator()

    # Create scenario ID with model identifier
    model_tag = reasoning_model.replace(".", "_").replace("-", "_")
    scenario_id = f"homeopathy_cached_{model_tag}_{uuid.uuid4().hex[:8]}"

    # Build the analysis request with forced scenario config
    request = BFIHAnalysisRequest(
        scenario_id=scenario_id,
        proposition=FORCED_SCENARIO_CONFIG["proposition"],
        scenario_config=FORCED_SCENARIO_CONFIG.copy(),
        reasoning_model=reasoning_model
    )

    print(f"\nScenario ID: {scenario_id}")
    print("Starting analysis with cached evidence...")
    print("(Skipping Phase 2 - using cached evidence)")

    # Run the analysis with injected evidence
    result = orchestrator.conduct_analysis_with_injected_evidence(
        request,
        injected_evidence=evidence_items,
        skip_methodology=True
    )

    # Save results
    report_path = output_path / f"bfih_report_{scenario_id}.md"
    json_path = output_path / f"bfih_report_{scenario_id}.json"
    config_path = output_path / f"scenario_config_{scenario_id}.json"

    with open(report_path, 'w') as f:
        f.write(result.report)
    print(f"\nSaved report: {report_path}")

    with open(json_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2, default=str)
    print(f"Saved JSON: {json_path}")

    with open(config_path, 'w') as f:
        json.dump(FORCED_SCENARIO_CONFIG, f, indent=2)
    print(f"Saved config: {config_path}")

    # Print summary
    print("\n" + "=" * 70)
    print(f"CALIBRATION TEST RESULTS ({reasoning_model})")
    print("=" * 70)

    print(f"\nProposition: {FORCED_SCENARIO_CONFIG['proposition']}")
    print(f"\nExpected Result: H2 (FALSE - No effect beyond placebo) should WIN decisively")
    print(f"                 H1 (TRUE) and H3-H5 (PARTIAL) should have low posteriors")

    print("\n" + "-" * 40)
    print("K0 (Scientific Consensus) Posteriors:")
    print("-" * 40)

    k0_posteriors = result.posteriors.get('K0', {})
    sorted_posteriors = sorted(k0_posteriors.items(), key=lambda x: x[1], reverse=True)

    winner = sorted_posteriors[0] if sorted_posteriors else (None, 0)

    for h_id, prob in sorted_posteriors:
        h_name = next((h['short_name'] for h in FORCED_SCENARIO_CONFIG['hypotheses'] if h['id'] == h_id), h_id)
        marker = " <-- WINNER" if h_id == winner[0] else ""
        print(f"  {h_id} ({h_name}): {prob:.4f} ({prob*100:.1f}%){marker}")

    # Determine if test passed
    print("\n" + "-" * 40)
    print("CALIBRATION ASSESSMENT:")
    print("-" * 40)

    h2_prob = k0_posteriors.get('H2', 0)
    h0_prob = k0_posteriors.get('H0', 0)
    partial_probs = sum(k0_posteriors.get(h, 0) for h in ['H3', 'H4', 'H5'])

    if winner[0] == 'H2':
        print("✓ PASS: H2 (No Effect Beyond Placebo) is the winner")
        if h2_prob > 0.5:
            print(f"✓ STRONG PASS: H2 has majority ({h2_prob*100:.1f}%)")
        else:
            print(f"⚠ WEAK PASS: H2 wins but without majority ({h2_prob*100:.1f}%)")
    elif winner[0] in ['H3', 'H4', 'H5']:
        print(f"✗ FAIL: A PARTIAL hypothesis ({winner[0]}) won!")
        print(f"  This indicates hedging bias may still be present.")
    elif winner[0] == 'H1':
        print(f"✗ FAIL: H1 (Specific Effects) won - methodology error")
    elif winner[0] == 'H0':
        print(f"⚠ UNCLEAR: H0 (Unforeseen) won with {h0_prob*100:.1f}%")
        print(f"  Check if LR ≈ 1 (non-predictive hypothesis should not win)")
    else:
        print(f"? UNCLEAR: {winner[0]} won - unexpected result")

    print(f"\nTotal PARTIAL hypothesis probability: {partial_probs*100:.1f}%")
    if partial_probs > h2_prob:
        print("⚠ WARNING: Combined PARTIAL > FALSE probability - possible hedging bias")

    # Print LR summary if available
    print("\n" + "-" * 40)
    print("Likelihood Ratio Check (from report):")
    print("-" * 40)
    print("Check the report for H0's LR - should be ≈ 1.0 if two-stage prompting is working")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run BFIH calibration test with cached evidence")
    parser.add_argument("--model", "-m", default="o3", help="Reasoning model to use (default: o3)")
    parser.add_argument("--cache", "-c", help="Path to cached evidence JSON file")
    parser.add_argument("--output", "-o", default="calibration_tests/homeopathy_forced", help="Output directory")

    args = parser.parse_args()

    result = run_forced_hypothesis_test_cached(
        reasoning_model=args.model,
        cache_file=args.cache,
        output_dir=args.output
    )
