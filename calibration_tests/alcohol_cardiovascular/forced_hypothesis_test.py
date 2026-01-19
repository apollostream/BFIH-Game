#!/usr/bin/env python3
"""
Calibration test: Moderate alcohol and cardiovascular health (CONTESTED)

This tests a genuinely contested scientific question where PARTIAL hypotheses
may legitimately win. Unlike homeopathy/vaccines, this has real scientific debate.

Expected: NOT clear-cut. Could be H2 (FALSE), H3 (PARTIAL-dose), or H4 (PARTIAL-confounding)
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

# Forced hypothesis set for alcohol-cardiovascular question
FORCED_SCENARIO_CONFIG = {
    "proposition": "Does moderate alcohol consumption provide cardiovascular health benefits?",
    "domain": "medicine",
    "difficulty": "hard",

    "paradigms": [
        {
            "id": "K0",
            "name": "Scientific Consensus",
            "description": "Mainstream epidemiological and clinical perspective based on observational studies, meta-analyses, and mechanistic research.",
            "ontology": "Material, measurable biological and behavioral processes",
            "epistemology": "Epidemiological evidence, RCTs where available, mechanistic plausibility",
            "axiology": "Public health guidance, harm reduction, evidence-based recommendations"
        },
        {
            "id": "K1",
            "name": "Traditional/Cultural",
            "description": "Perspective that values long-standing cultural practices (Mediterranean diet, French paradox) and observational patterns.",
            "ontology": "Holistic lifestyle factors, cultural wisdom",
            "epistemology": "Historical patterns, population-level observations, traditional knowledge",
            "axiology": "Quality of life, cultural practices, moderate enjoyment"
        },
        {
            "id": "K2",
            "name": "Strict Precautionary",
            "description": "Emphasizes that alcohol is a known carcinogen and toxin; any benefit claims should be viewed with extreme skepticism.",
            "ontology": "Biochemical toxicity, dose-response relationships",
            "epistemology": "Mechanistic toxicology, no safe level for carcinogens",
            "axiology": "Absolute harm minimization, precautionary principle"
        }
    ],

    "hypotheses": [
        {
            "id": "H0",
            "name": "OTHER - Unforeseen explanation",
            "short_name": "Unforeseen",
            "description": "Some unknown mechanism not captured by the other hypotheses explains the observed associations between moderate alcohol and cardiovascular outcomes.",
            "verdict_type": "OTHER"
        },
        {
            "id": "H1",
            "name": "TRUE - Moderate alcohol is cardioprotective",
            "short_name": "Cardioprotective",
            "description": "Moderate alcohol consumption (1-2 drinks/day) provides genuine cardiovascular benefits through mechanisms like HDL elevation, reduced platelet aggregation, and improved endothelial function. The J-curve relationship is real.",
            "verdict_type": "TRUE"
        },
        {
            "id": "H2",
            "name": "FALSE - No cardiovascular benefit",
            "short_name": "No Benefit",
            "description": "Moderate alcohol provides no net cardiovascular benefit. Previous observational findings were confounded by the 'sick quitter' effect, healthy user bias, and other methodological issues. Any benefits are outweighed by cancer and other risks.",
            "verdict_type": "FALSE"
        },
        {
            "id": "H3",
            "name": "PARTIAL - Dose and pattern dependent",
            "short_name": "Dose-Dependent",
            "description": "Benefits exist but are highly dose and pattern dependent. Light drinking (≤1 drink/day) with meals may provide modest benefits, but these disappear or reverse at higher doses or with binge patterns. The therapeutic window is narrow.",
            "verdict_type": "PARTIAL"
        },
        {
            "id": "H4",
            "name": "PARTIAL - Confounded by lifestyle",
            "short_name": "Lifestyle Confounding",
            "description": "Apparent benefits are largely due to confounding - moderate drinkers tend to have healthier lifestyles, better socioeconomic status, and more social connections. When properly controlled, the benefit disappears or becomes minimal.",
            "verdict_type": "PARTIAL"
        },
        {
            "id": "H5",
            "name": "PARTIAL - Beverage-type specific",
            "short_name": "Beverage-Specific",
            "description": "Benefits are specific to certain beverages (particularly red wine) due to polyphenols, resveratrol, or other compounds - not alcohol itself. Beer and spirits may not provide the same benefits.",
            "verdict_type": "PARTIAL"
        }
    ],

    # Priors reflect genuine uncertainty - no strong favorite
    "priors_by_paradigm": {
        "K0": {
            "H0": 0.05,
            "H1": 0.20,   # Historical view supported J-curve
            "H2": 0.25,   # Recent studies cast doubt
            "H3": 0.25,   # Dose-dependence is plausible
            "H4": 0.15,   # Confounding is a known issue
            "H5": 0.10    # Wine-specific effects debated
        },
        "K1": {
            "H0": 0.05,
            "H1": 0.40,   # Traditional view favors benefits
            "H2": 0.10,
            "H3": 0.25,
            "H4": 0.10,
            "H5": 0.10
        },
        "K2": {
            "H0": 0.05,
            "H1": 0.05,   # Precautionary view skeptical of benefits
            "H2": 0.45,   # Favors no benefit
            "H3": 0.15,
            "H4": 0.25,   # Confounding explanation preferred
            "H5": 0.05
        }
    }
}


def run_forced_hypothesis_test(
    reasoning_model: str = "o3",
    output_dir: str = "calibration_tests/alcohol_cardiovascular"
):
    """Run BFIH analysis with forced hypothesis set."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"BFIH CONTESTED TOPIC TEST: Alcohol & Cardiovascular Health ({reasoning_model})")
    print("=" * 70)
    print(f"\nProposition: {FORCED_SCENARIO_CONFIG['proposition']}")
    print(f"Reasoning Model: {reasoning_model}")
    print(f"\nThis is a CONTESTED topic - no single 'correct' answer expected.")
    print(f"\nForced Hypotheses:")
    for h in FORCED_SCENARIO_CONFIG['hypotheses']:
        print(f"  {h['id']}: {h['name']}")
    print(f"\nOutput: {output_dir}")
    print("=" * 70)

    # Initialize orchestrator
    orchestrator = BFIHOrchestrator()

    # Create scenario ID
    model_tag = reasoning_model.replace(".", "_").replace("-", "_")
    scenario_id = f"alcohol_cv_{model_tag}_{uuid.uuid4().hex[:8]}"

    # Build the analysis request with forced scenario config
    request = BFIHAnalysisRequest(
        scenario_id=scenario_id,
        proposition=FORCED_SCENARIO_CONFIG["proposition"],
        scenario_config=FORCED_SCENARIO_CONFIG.copy(),
        reasoning_model=reasoning_model
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
    print(f"CONTESTED TOPIC RESULTS ({reasoning_model})")
    print("=" * 70)

    print(f"\nProposition: {FORCED_SCENARIO_CONFIG['proposition']}")
    print(f"\nNOTE: This is a genuinely contested topic. Multiple outcomes are valid:")
    print(f"  - H1 (TRUE): Traditional J-curve view")
    print(f"  - H2 (FALSE): Recent skeptical view")
    print(f"  - H3/H4/H5 (PARTIAL): Nuanced positions")

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

    # Analysis of result
    print("\n" + "-" * 40)
    print("ANALYSIS:")
    print("-" * 40)

    h0_prob = k0_posteriors.get('H0', 0)
    h1_prob = k0_posteriors.get('H1', 0)
    h2_prob = k0_posteriors.get('H2', 0)
    partial_probs = sum(k0_posteriors.get(h, 0) for h in ['H3', 'H4', 'H5'])

    print(f"H0 (Unforeseen): {h0_prob*100:.1f}% - should be low (~5%)")
    print(f"H1 (TRUE - Cardioprotective): {h1_prob*100:.1f}%")
    print(f"H2 (FALSE - No Benefit): {h2_prob*100:.1f}%")
    print(f"Total PARTIAL (H3+H4+H5): {partial_probs*100:.1f}%")

    if h0_prob > 0.15:
        print("\n⚠ WARNING: H0 (Unforeseen) is elevated - may indicate hedging bias")

    if winner[0] == 'H0':
        print("\n⚠ CONCERN: H0 won - non-predictive hypothesis should not win")
    elif winner[0] == 'H1':
        print("\n→ Result: Traditional J-curve view supported")
    elif winner[0] == 'H2':
        print("\n→ Result: Skeptical view supported (no benefit)")
    elif winner[0] in ['H3', 'H4', 'H5']:
        print(f"\n→ Result: Nuanced/partial view ({winner[0]}) - appropriate for contested topic")

    # Cross-paradigm comparison
    print("\n" + "-" * 40)
    print("Cross-Paradigm Winners:")
    print("-" * 40)
    for paradigm in ['K0', 'K1', 'K2']:
        p_posteriors = result.posteriors.get(paradigm, {})
        if p_posteriors:
            p_winner = max(p_posteriors.items(), key=lambda x: x[1])
            h_name = next((h['short_name'] for h in FORCED_SCENARIO_CONFIG['hypotheses'] if h['id'] == p_winner[0]), p_winner[0])
            print(f"  {paradigm}: {p_winner[0]} ({h_name}) at {p_winner[1]*100:.1f}%")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run BFIH contested topic test")
    parser.add_argument("--model", "-m", default="o3", help="Reasoning model to use (default: o3)")
    parser.add_argument("--output", "-o", default="calibration_tests/alcohol_cardiovascular", help="Output directory")

    args = parser.parse_args()

    result = run_forced_hypothesis_test(
        reasoning_model=args.model,
        output_dir=args.output
    )
