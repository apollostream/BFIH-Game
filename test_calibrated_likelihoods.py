#!/usr/bin/env python3
"""
Test the calibrated likelihood elicitation method using cached evidence.
"""

import json
import sys
from datetime import datetime, timezone

from bfih_orchestrator_fixed import BFIHOrchestrator, BFIHAnalysisRequest

def main():
    # Load checkpoint with cached evidence
    checkpoint_path = "auto_f3c4c756_checkpoint_20260119_184626.json"
    print(f"Loading checkpoint: {checkpoint_path}")

    with open(checkpoint_path) as f:
        checkpoint = json.load(f)

    scenario_id = checkpoint["scenario_id"]
    proposition = checkpoint["proposition"]
    scenario_config = checkpoint["scenario_config"]
    evidence_items = checkpoint["completed_phases"].get("evidence_items", [])

    print(f"Scenario ID: {scenario_id}")
    print(f"Proposition: {proposition[:80]}...")
    print(f"Evidence items: {len(evidence_items)}")
    print(f"Hypotheses: {len(scenario_config.get('hypotheses', []))}")
    print(f"Paradigms: {len(scenario_config.get('paradigms', []))}")

    # Create analysis request
    request = BFIHAnalysisRequest(
        scenario_id=f"calibration_test_{scenario_id}",
        proposition=proposition,
        scenario_config=scenario_config,
        reasoning_model="gpt-5.2",
        budget_limit=5.0  # $5 budget limit for testing
    )

    # Initialize orchestrator
    print("\nInitializing orchestrator...")
    orchestrator = BFIHOrchestrator()

    # Run analysis with injected evidence (skips Phase 2 web search)
    print("\n" + "=" * 60)
    print("STARTING CALIBRATED LIKELIHOOD TEST")
    print("=" * 60)

    try:
        result = orchestrator.conduct_analysis_with_injected_evidence(
            request=request,
            injected_evidence=evidence_items,
            skip_methodology=True  # Skip Phase 1 too for faster testing
        )

        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)

        # Print results summary
        print(f"\nVerdict: {result.metadata.get('verdict', 'N/A')}")
        print(f"Winning hypothesis: {result.metadata.get('winning_hypothesis', 'N/A')}")
        print(f"Winning posterior: {result.metadata.get('winning_posterior', 0):.3f}")

        # Print posteriors for K0
        posteriors = result.metadata.get('posteriors_by_paradigm', {}).get('K0', {})
        if posteriors:
            print("\nK0 Posteriors:")
            sorted_posteriors = sorted(posteriors.items(), key=lambda x: x[1], reverse=True)
            for h_id, p in sorted_posteriors:
                print(f"  {h_id}: {p:.4f}")

        # Check for likelihood spread
        if result.metadata.get('evidence_clusters'):
            print("\nLikelihood Analysis:")
            for cluster in result.metadata['evidence_clusters']:
                cal = cluster.get('calibration_info', {})
                if cal:
                    print(f"  {cluster['cluster_id']}: LR={cal.get('lr_range_value', '?')}x, "
                          f"H_max={cal.get('h_max', '?')}, H_min={cal.get('h_min', '?')}")

                    # Calculate actual spread
                    k0_lh = cluster.get('likelihoods_by_paradigm', {}).get('K0', {})
                    if k0_lh:
                        probs = [lh.get('probability', 0.5) for lh in k0_lh.values() if isinstance(lh, dict)]
                        if probs:
                            print(f"       Range: [{min(probs):.3f}, {max(probs):.3f}], spread={max(probs)-min(probs):.3f}")

        # Save result
        output_path = f"calibration_test_result_{scenario_id}.json"
        with open(output_path, 'w') as f:
            json.dump({
                'analysis_id': result.analysis_id,
                'scenario_id': result.scenario_id,
                'verdict': result.metadata.get('verdict'),
                'posteriors': result.metadata.get('posteriors_by_paradigm', {}),
                'evidence_clusters': result.metadata.get('evidence_clusters', []),
                'cost': result.metadata.get('cost', {})
            }, f, indent=2)
        print(f"\nResult saved to: {output_path}")

        # Print cost
        cost = result.metadata.get('cost', {})
        print(f"\nTotal cost: ${cost.get('total_cost_usd', 0):.2f}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
