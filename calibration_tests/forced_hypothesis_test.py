#!/usr/bin/env python3
"""
Calibration test with forced hypotheses to test for hedging bias.

This script forces a specific hypothesis set with TRUE/FALSE/PARTIAL options
to test whether the BFIH methodology has a structural bias toward hedged conclusions.
"""

import sys
import os
import json
import uuid
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(override=True)

from bfih_orchestrator_fixed import BFIHOrchestrator, BFIHAnalysisRequest

# Forced hypothesis set for vaccines/autism question
FORCED_SCENARIO_CONFIG = {
    "proposition": "Do vaccines cause autism in children?",
    "domain": "medicine",
    "difficulty": "hard",

    # Forced paradigms - keep it simpler for clearer test
    "paradigms": [
        {
            "id": "K0",
            "name": "Scientific Consensus",
            "description": "Mainstream scientific and medical consensus based on epidemiological evidence, meta-analyses, and mechanistic biology.",
            "ontology": "Material, measurable biological processes",
            "epistemology": "Empirical observation, RCTs, systematic reviews, falsification",
            "axiology": "Public health, harm reduction, evidence-based medicine"
        },
        {
            "id": "K1",
            "name": "Vaccine Skeptic",
            "description": "Perspective that questions vaccine safety claims, emphasizes anecdotal reports, and distrusts pharmaceutical/regulatory institutions.",
            "ontology": "Individual experiences and observable outcomes",
            "epistemology": "Personal testimony, pattern recognition in adverse event reports",
            "axiology": "Parental autonomy, precaution, distrust of authority"
        },
        {
            "id": "K2",
            "name": "Precautionary",
            "description": "Accepts most vaccine science but emphasizes unknown long-term risks and subgroup vulnerabilities.",
            "ontology": "Complex systems with emergent effects",
            "epistemology": "Scenario modeling, acknowledging uncertainty",
            "axiology": "Precautionary principle, intergenerational responsibility"
        }
    ],

    # FORCED HYPOTHESES - This is the key test
    # We explicitly include TRUE, FALSE, and PARTIAL options
    "hypotheses": [
        {
            "id": "H0",
            "name": "OTHER - Unforeseen explanation",
            "short_name": "Unforeseen",
            "description": "Some unknown factor not captured by the other hypotheses explains the relationship (or lack thereof) between vaccines and autism.",
            "verdict_type": "OTHER"
        },
        {
            "id": "H1",
            "name": "TRUE - Vaccines directly cause autism",
            "short_name": "Direct Causation",
            "description": "Vaccines (or their components like thimerosal, aluminum adjuvants, or antigens) directly cause autism through biological mechanisms such as immune activation, neurotoxicity, or gut-brain axis disruption.",
            "verdict_type": "TRUE"
        },
        {
            "id": "H2",
            "name": "FALSE - No causal link exists",
            "short_name": "No Causation",
            "description": "There is no causal relationship between vaccines and autism. The temporal correlation (vaccines given around age when autism symptoms appear) is coincidental. Large epidemiological studies consistently show no increased risk.",
            "verdict_type": "FALSE"
        },
        {
            "id": "H3",
            "name": "PARTIAL - Rare subgroup vulnerability",
            "short_name": "Subgroup Effect",
            "description": "While vaccines don't cause autism in the general population, a small subset of genetically or immunologically vulnerable children may experience adverse neurodevelopmental effects. This subgroup is too small to detect in population studies.",
            "verdict_type": "PARTIAL"
        },
        {
            "id": "H4",
            "name": "PARTIAL - Indirect pathway via immune activation",
            "short_name": "Indirect Pathway",
            "description": "Vaccines don't directly cause autism, but in rare cases, the immune response they trigger may interact with pre-existing conditions to affect neurodevelopment. The effect is real but indirect and context-dependent.",
            "verdict_type": "PARTIAL"
        },
        {
            "id": "H5",
            "name": "PARTIAL - Timing/schedule effects only",
            "short_name": "Timing Effects",
            "description": "Individual vaccines are safe, but the cumulative effect of the vaccination schedule (multiple vaccines in short timeframes) may overwhelm some children's immune systems, contributing to developmental issues in susceptible individuals.",
            "verdict_type": "PARTIAL"
        }
    ],

    # Priors by paradigm - designed to test if evidence can overcome paradigm bias
    "priors_by_paradigm": {
        "K0": {
            "H0": 0.05,   # Low - well-studied topic
            "H1": 0.05,   # Low - contradicts consensus
            "H2": 0.60,   # High - matches consensus
            "H3": 0.10,   # Low but possible
            "H4": 0.10,   # Low but possible
            "H5": 0.10    # Low but possible
        },
        "K1": {
            "H0": 0.10,
            "H1": 0.35,   # Skeptics believe causation more likely
            "H2": 0.10,   # Skeptics doubt no-causation claim
            "H3": 0.20,
            "H4": 0.15,
            "H5": 0.10
        },
        "K2": {
            "H0": 0.10,
            "H1": 0.10,
            "H2": 0.30,   # Accepts likely no causation
            "H3": 0.20,   # But emphasizes possible subgroups
            "H4": 0.15,
            "H5": 0.15
        }
    }
}


def run_forced_hypothesis_test(output_dir: str = "calibration_tests/vaccines_autism_forced"):
    """Run BFIH analysis with forced hypothesis set."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("BFIH CALIBRATION TEST: Forced Hypothesis Set")
    print("=" * 70)
    print(f"\nProposition: {FORCED_SCENARIO_CONFIG['proposition']}")
    print(f"\nForced Hypotheses:")
    for h in FORCED_SCENARIO_CONFIG['hypotheses']:
        print(f"  {h['id']}: {h['name']}")
    print(f"\nOutput: {output_dir}")
    print("=" * 70)

    # Initialize orchestrator
    orchestrator = BFIHOrchestrator()

    # Create scenario ID
    scenario_id = f"forced_{uuid.uuid4().hex[:8]}"

    # Build the analysis request with forced scenario config
    request = BFIHAnalysisRequest(
        scenario_id=scenario_id,
        proposition=FORCED_SCENARIO_CONFIG["proposition"],
        scenario_config=FORCED_SCENARIO_CONFIG.copy(),
        reasoning_model="o3"
    )

    print(f"\nScenario ID: {scenario_id}")
    print("Starting analysis with forced hypotheses...")
    print("(Skipping Phase 0 - using predefined paradigms/hypotheses/priors)")

    # Run the analysis
    result = orchestrator.conduct_analysis(request)

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
    print("CALIBRATION TEST RESULTS")
    print("=" * 70)

    print(f"\nProposition: {FORCED_SCENARIO_CONFIG['proposition']}")
    print(f"\nExpected Result: H2 (FALSE - No causal link) should WIN decisively")
    print(f"                 H3-H5 (PARTIAL hypotheses) should NOT win")

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
    partial_probs = sum(k0_posteriors.get(h, 0) for h in ['H3', 'H4', 'H5'])

    if winner[0] == 'H2':
        print("✓ PASS: H2 (No Causation) is the winner")
        if h2_prob > 0.5:
            print(f"✓ STRONG PASS: H2 has majority ({h2_prob*100:.1f}%)")
        else:
            print(f"⚠ WEAK PASS: H2 wins but without majority ({h2_prob*100:.1f}%)")
    elif winner[0] in ['H3', 'H4', 'H5']:
        print(f"✗ FAIL: A PARTIAL hypothesis ({winner[0]}) won!")
        print(f"  This confirms the hedging bias concern.")
    elif winner[0] == 'H1':
        print(f"✗ FAIL: H1 (Direct Causation) won - methodology error")
    else:
        print(f"? UNCLEAR: {winner[0]} won - unexpected result")

    print(f"\nTotal PARTIAL hypothesis probability: {partial_probs*100:.1f}%")
    if partial_probs > h2_prob:
        print("⚠ WARNING: Combined PARTIAL > FALSE probability - possible hedging bias")

    return result


if __name__ == "__main__":
    result = run_forced_hypothesis_test()
