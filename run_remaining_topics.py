#!/usr/bin/env python3
"""
Run remaining Nature of Mind v2 topics with fresh evidence gathering.
Uses calibrated likelihood elicitation.
"""

import json
import os
import sys
from datetime import datetime, timezone

from bfih_orchestrator_fixed import BFIHOrchestrator, BFIHAnalysisRequest

# Topics that need fresh evidence gathering
TOPICS = [
    {
        "id": "consciousness_llm",
        "proposition": "Can artificial systems like large language models have genuine subjective experience?",
    },
    {
        "id": "illusionism",
        "proposition": "Is phenomenal consciousness an introspective illusion rather than an irreducible feature of reality?",
    },
    {
        "id": "understanding_vs_mimicry",
        "proposition": "Does sophisticated language use require genuine understanding, or can it emerge from pattern matching alone?",
    },
]

TOTAL_BUDGET = 12.0  # $12 total budget for these 3 topics
OUTPUT_DIR = "synthesis_output/nature_of_mind_v2_calibrated"


def run_topic(topic: dict, budget: float, orchestrator: BFIHOrchestrator) -> dict:
    """Run a single topic analysis with fresh evidence gathering."""
    topic_id = topic["id"]
    proposition = topic["proposition"]

    print(f"\n{'='*60}")
    print(f"TOPIC: {topic_id}")
    print(f"Proposition: {proposition[:70]}...")
    print(f"Budget: ${budget:.2f}")
    print(f"{'='*60}")

    # Run full analysis with evidence gathering
    # analyze_topic generates paradigms, hypotheses, gathers evidence, etc.
    result = orchestrator.analyze_topic(
        proposition=proposition,
        domain="philosophy",
        difficulty="hard",
        reasoning_model="gpt-5.2",
        budget_limit=budget
    )

    # Extract results
    cost = result.metadata.get('cost', {}).get('total_cost_usd', 0)
    verdict = result.metadata.get('verdict', 'N/A')
    winning_h = result.metadata.get('winning_hypothesis', 'N/A')
    winning_p = result.metadata.get('winning_posterior', 0)

    # Get calibration info
    clusters = result.metadata.get('evidence_clusters', [])
    calibration_summary = []
    for c in clusters:
        cal = c.get('calibration_info', {})
        if cal:
            calibration_summary.append({
                'cluster': c.get('cluster_id', 'C?'),
                'lr_range': cal.get('lr_range_value'),
                'h_max': cal.get('h_max'),
                'h_max_rationale': cal.get('h_max_rationale', ''),
                'h_min': cal.get('h_min'),
                'h_min_rationale': cal.get('h_min_rationale', ''),
                'key_evidence': cal.get('key_evidence', []),
                'coherence_verified': cal.get('coherence_verified', True)
            })

    # Save report
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_DIR, f"bfih_report_calibrated_{topic_id}.md")
    with open(report_path, 'w') as f:
        f.write(result.report)

    json_path = os.path.join(OUTPUT_DIR, f"bfih_report_calibrated_{topic_id}.json")
    with open(json_path, 'w') as f:
        json.dump({
            'analysis_id': result.analysis_id,
            'scenario_id': result.scenario_id,
            'proposition': proposition,
            'verdict': verdict,
            'winning_hypothesis': winning_h,
            'winning_posterior': winning_p,
            'posteriors': result.metadata.get('posteriors_by_paradigm', {}),
            'calibration': calibration_summary,
            'evidence_count': result.metadata.get('evidence_count', 0),
            'cost': cost
        }, f, indent=2)

    print(f"\nResults:")
    print(f"  Verdict: {verdict}")
    print(f"  Winner: {winning_h[:50] if winning_h else 'N/A'}...")
    print(f"  Posterior: {winning_p:.4f}")
    print(f"  Cost: ${cost:.2f}")
    print(f"  Calibration: {calibration_summary}")
    print(f"  Report: {report_path}")

    return {
        'topic': topic_id,
        'verdict': verdict,
        'winning_hypothesis': winning_h,
        'winning_posterior': winning_p,
        'cost': cost,
        'calibration': calibration_summary
    }


def main():
    remaining_budget = TOTAL_BUDGET
    results = []

    print(f"Starting remaining Nature of Mind v2 analyses")
    print(f"Total budget: ${TOTAL_BUDGET:.2f}")
    print(f"Topics to run: {len(TOPICS)}")

    # Initialize orchestrator once
    orchestrator = BFIHOrchestrator()

    for topic in TOPICS:
        if remaining_budget <= 1.0:  # Need at least $1 to run
            print(f"\nBudget too low (${remaining_budget:.2f}), skipping {topic['id']}")
            continue

        # Allocate budget per remaining topic
        topics_remaining = len(TOPICS) - len(results)
        per_topic_budget = remaining_budget / topics_remaining

        try:
            result = run_topic(
                topic=topic,
                budget=per_topic_budget,
                orchestrator=orchestrator
            )
            results.append(result)
            remaining_budget -= result['cost']
            print(f"\nRemaining budget: ${remaining_budget:.2f}")
        except RuntimeError as e:
            if "BUDGET" in str(e):
                print(f"\nBudget exceeded for {topic['id']}: {e}")
                # Try to get partial result info
                results.append({
                    'topic': topic['id'],
                    'verdict': 'BUDGET_EXCEEDED',
                    'winning_hypothesis': 'N/A',
                    'winning_posterior': 0,
                    'cost': per_topic_budget,
                    'calibration': []
                })
                remaining_budget = 0
            else:
                raise
        except Exception as e:
            print(f"\nERROR in {topic['id']}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    total_cost = sum(r['cost'] for r in results)
    print(f"\nCompleted: {len(results)}/{len(TOPICS)} topics")
    print(f"Total cost: ${total_cost:.2f} / ${TOTAL_BUDGET:.2f}")

    print(f"\n{'Topic':<25} {'Verdict':<20} {'Posterior':<10} {'LR'}")
    print("-" * 70)
    for r in results:
        lr = r['calibration'][0]['lr_range'] if r['calibration'] else 'N/A'
        post = f"{r['winning_posterior']:.4f}" if r['winning_posterior'] else 'N/A'
        print(f"{r['topic']:<25} {r['verdict']:<20} {post:<10} {lr}")

    # Update summary file
    summary_path = os.path.join(OUTPUT_DIR, "calibration_summary.json")
    existing = {}
    if os.path.exists(summary_path):
        with open(summary_path) as f:
            existing = json.load(f)

    # Merge with existing results
    all_results = existing.get('results', [])
    for r in results:
        # Remove any existing entry for this topic
        all_results = [x for x in all_results if x['topic'] != r['topic']]
        all_results.append(r)

    with open(summary_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_cost': sum(r['cost'] for r in all_results),
            'results': all_results
        }, f, indent=2)
    print(f"\nSummary updated: {summary_path}")


if __name__ == "__main__":
    main()
