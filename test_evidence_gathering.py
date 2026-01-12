#!/usr/bin/env python3
"""
Focused test for multi-search evidence gathering.

Tests the _run_phase_2_evidence method directly without running the full analysis.
"""
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import after env loaded
from bfih_orchestrator_fixed import BFIHOrchestrator, BFIHAnalysisRequest


def test_multi_search_evidence():
    """Test the multi-search evidence gathering."""
    print("\n" + "="*60)
    print("Testing Multi-Search Evidence Gathering")
    print("="*60 + "\n")

    # Initialize orchestrator
    orchestrator = BFIHOrchestrator()

    # Create a minimal request for testing
    request = BFIHAnalysisRequest(
        scenario_id="test_hotels",
        proposition="Lifestyle luxury hotels in Chicago",
        scenario_config={
            "hypotheses": [
                {"id": "H1", "title": "The Peninsula Chicago", "name": "The Peninsula Chicago"},
                {"id": "H2", "title": "Park Hyatt Chicago", "name": "Park Hyatt Chicago"},
                {"id": "H3", "title": "Waldorf Astoria Chicago", "name": "Waldorf Astoria Chicago"},
                {"id": "H4", "title": "The Langham Chicago", "name": "The Langham Chicago"},
                {"id": "H0", "title": "Other luxury hotels", "name": "Other luxury hotels"},
            ]
        }
    )

    # Mock methodology (we're testing evidence gathering, not methodology retrieval)
    methodology = "Use web search to find evidence supporting or refuting each hypothesis."

    # Run the evidence gathering phase
    print("Starting evidence gathering phase...\n")
    markdown_summary, evidence_items = orchestrator._run_phase_2_evidence(request, methodology)

    # Analyze results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)

    print(f"\nTotal evidence items: {len(evidence_items)}")

    # Count items with valid URLs
    valid_urls = [item for item in evidence_items if item.get('source_url', '').startswith('http')]
    print(f"Items with valid URLs: {len(valid_urls)}")

    # Count unique URLs
    unique_urls = set(item.get('source_url', '') for item in evidence_items if item.get('source_url', '').startswith('http'))
    print(f"Unique URLs: {len(unique_urls)}")

    # Show hypothesis distribution
    hyp_counts = {}
    for item in evidence_items:
        for hyp in item.get('supports_hypotheses', []):
            hyp_counts[hyp] = hyp_counts.get(hyp, 0) + 1
    print(f"\nEvidence distribution by hypothesis:")
    for hyp, count in sorted(hyp_counts.items()):
        print(f"  {hyp}: {count} items")

    # Show sample evidence
    print("\n" + "-"*40)
    print("Sample evidence items (first 5):")
    print("-"*40)
    for item in evidence_items[:5]:
        print(f"\n{item.get('evidence_id', '?')}: {item.get('description', 'N/A')[:100]}...")
        print(f"  Source: {item.get('source_name', 'Unknown')}")
        url = item.get('source_url', '')
        if url:
            print(f"  URL: {url[:80]}...")

    # Save results
    output = {
        "total_evidence": len(evidence_items),
        "valid_urls": len(valid_urls),
        "unique_urls": len(unique_urls),
        "hypothesis_distribution": hyp_counts,
        "evidence_items": evidence_items
    }

    with open("test_evidence_result.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nFull results saved to: test_evidence_result.json")

    return len(evidence_items), len(unique_urls)


if __name__ == "__main__":
    total, unique = test_multi_search_evidence()
    print(f"\n{'='*60}")
    print(f"FINAL: {total} evidence items with {unique} unique URLs")
    print("="*60)
