#!/usr/bin/env python3
"""
Test script to verify web search behavior with OpenAI's Responses API.

This tests whether the model performs multiple web searches when prompted.
"""
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

client = OpenAI()
MODEL = "gpt-4o"


def count_web_searches(response) -> tuple[int, list]:
    """Count web searches in response and extract sources."""
    search_count = 0
    all_sources = []

    for output_item in response.output:
        if hasattr(output_item, 'type') and output_item.type == 'web_search_call':
            search_count += 1
            query = None
            if hasattr(output_item, 'action'):
                query = getattr(output_item.action, 'query', None)
                sources = getattr(output_item.action, 'sources', [])
                print(f"  Search #{search_count}: {query[:80] if query else 'N/A'}...")
                print(f"    -> {len(sources)} sources")
                all_sources.extend([
                    {'url': getattr(s, 'url', ''), 'title': getattr(s, 'title', '')}
                    for s in sources if hasattr(s, 'url')
                ])

    return search_count, all_sources


def test_single_call_multiple_search():
    """Test if model does multiple searches in single API call."""
    print("\n" + "="*60)
    print("TEST 1: Single API call - can model do multiple searches?")
    print("="*60)

    prompt = """You are a research agent. Search for diverse information about lifestyle luxury hotels in Chicago.

CRITICAL: Execute MULTIPLE separate web searches:
1. Search for "best luxury hotels Chicago 2025"
2. Search for "Chicago hotel reviews complaints"
3. Search for "Peninsula Chicago reviews"
4. Search for "Park Hyatt Chicago reviews"

You MUST call web_search multiple times with different queries.
After searching, summarize what you found in 2-3 sentences."""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
        tools=[{"type": "web_search", "search_context_size": "high"}],
        include=["web_search_call.action.sources"],
        max_output_tokens=4000
    )

    search_count, sources = count_web_searches(response)
    print(f"\nResult: {search_count} web search(es) executed")
    print(f"Total sources: {len(sources)}")
    return search_count


def test_multi_call_approach():
    """Test making multiple API calls, each with focused search."""
    print("\n" + "="*60)
    print("TEST 2: Multiple API calls - guaranteed diverse searches")
    print("="*60)

    search_queries = [
        ("Rankings", "best lifestyle luxury hotels Chicago 2025 rankings"),
        ("Reviews", "Chicago luxury hotel reviews ratings TripAdvisor"),
        ("Critical", "worst luxury hotels Chicago complaints problems avoid"),
        ("Peninsula", "Peninsula Chicago hotel review ratings"),
        ("Park Hyatt", "Park Hyatt Chicago hotel review experience"),
    ]

    total_searches = 0
    total_sources = []

    for name, query in search_queries:
        print(f"\n[{name}] Searching: {query[:60]}...")

        prompt = f"""Search for: {query}

Return a brief 1-2 sentence summary of what you found."""

        response = client.responses.create(
            model=MODEL,
            input=prompt,
            tools=[{"type": "web_search", "search_context_size": "medium"}],
            include=["web_search_call.action.sources"],
            max_output_tokens=1000
        )

        search_count, sources = count_web_searches(response)
        total_searches += search_count
        total_sources.extend(sources)
        print(f"  Result: {search_count} search(es), {len(sources)} sources")

    # Deduplicate sources
    unique_urls = set(s['url'] for s in total_sources if s.get('url'))

    print(f"\n{'='*60}")
    print(f"Multi-call result: {total_searches} total searches across {len(search_queries)} API calls")
    print(f"Unique source URLs: {len(unique_urls)}")
    return total_searches, len(unique_urls)


def main():
    print("Testing OpenAI web_search behavior")
    print(f"Model: {MODEL}")

    # Test 1: Single call with prompting for multiple searches
    single_count = test_single_call_multiple_search()

    # Test 2: Multiple calls guaranteed
    multi_count, unique_urls = test_multi_call_approach()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Single API call (prompting): {single_count} search(es)")
    print(f"Multi API call (guaranteed): {multi_count} search(es), {unique_urls} unique URLs")

    if single_count >= 3:
        print("\nConclusion: Single call CAN do multiple searches with good prompting!")
    else:
        print("\nConclusion: Single call only did 1 search despite prompting.")
        print("Multi-call approach is needed for guaranteed diverse evidence.")


if __name__ == "__main__":
    main()
