#!/usr/bin/env python3
"""
BFIH Hermeneutic Synthesis System

Orchestrates multiple connected BFIH analyses and synthesizes them
into a unified philosophical work where individual analyses form
chapters of a coherent whole as a hermeneutic circle.

Usage:
    python bfih_hermeneutic.py --project project.yaml
    python bfih_hermeneutic.py --project project.yaml --resume
    python bfih_hermeneutic.py --project project.yaml --meta-only
    python bfih_hermeneutic.py --project project.yaml --synthesis-only

Phases:
    1. Component Analyses - Run BFIH analyses on each topic in dependency order
    2. Cross-Analysis Integration - Extract findings, identify tensions/reinforcements
    3. Meta-Analysis - BFIH analysis treating component conclusions as evidence
    4. Narrative Synthesis - Generate unified philosophical work
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import hermeneutic modules
from hermeneutic_config_schema import (
    HermeneuticProjectConfig,
    load_project_config
)
from bfih_hermeneutic_runner import HermeneuticRunner, AnalysisResult
from bfih_cross_analysis import CrossAnalysisIntegrator, UnifiedFindings
from bfih_meta_analysis import MetaAnalysisEngine
from bfih_narrative_synthesis import NarrativeSynthesizer, SynthesisDocument


def print_banner():
    """Print startup banner."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║         BFIH HERMENEUTIC SYNTHESIS SYSTEM                         ║
║                                                                   ║
║   Multi-Analysis Philosophical Investigation with Bayesian Rigor  ║
╚═══════════════════════════════════════════════════════════════════╝
""")


def run_component_analyses(
    config: HermeneuticProjectConfig,
    output_dir: Path,
    resume: bool = False
) -> Dict[str, AnalysisResult]:
    """
    Phase 1: Run component analyses.

    Args:
        config: Project configuration
        output_dir: Output directory
        resume: Resume from checkpoint if available

    Returns:
        Dictionary of analysis results
    """
    print("\n" + "=" * 60)
    print("PHASE 1: Component Analyses")
    print("=" * 60)

    runner = HermeneuticRunner(config, str(output_dir))

    if resume:
        if runner.load_checkpoint():
            print(f"  Resuming from checkpoint ({len(runner.results)} completed)")
        else:
            print("  No checkpoint found, starting fresh")

    results = runner.run_all(resume=resume)

    print(f"\n  Completed: {len(results)} analyses")
    for topic_id, result in results.items():
        print(f"    {topic_id}: {result.verdict} ({result.winning_posterior:.1%})")

    return results


def run_cross_analysis_integration(
    results: Dict[str, AnalysisResult],
    output_dir: Path
) -> UnifiedFindings:
    """
    Phase 2: Cross-analysis integration.

    Args:
        results: Component analysis results
        output_dir: Output directory

    Returns:
        UnifiedFindings object
    """
    print("\n" + "=" * 60)
    print("PHASE 2: Cross-Analysis Integration")
    print("=" * 60)

    integrator = CrossAnalysisIntegrator(results)
    findings = integrator.extract_unified_findings()

    print(f"  Total analyses: {findings.total_analyses}")
    print(f"  Total evidence items: {findings.total_evidence_items}")
    print(f"  Tensions identified: {len(findings.tensions)}")
    print(f"  Reinforcements identified: {len(findings.reinforcements)}")

    # Save findings
    findings_path = output_dir / "unified_findings.json"
    findings.save(str(findings_path))
    print(f"  Saved: {findings_path}")

    return findings


def run_meta_analysis(
    findings: UnifiedFindings,
    config: HermeneuticProjectConfig,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Phase 3: Meta-analysis.

    Args:
        findings: Unified findings from integration
        config: Project configuration
        output_dir: Output directory

    Returns:
        Meta-analysis result dictionary
    """
    print("\n" + "=" * 60)
    print("PHASE 3: Meta-Analysis")
    print("=" * 60)

    print(f"  Proposition: {config.meta_analysis.proposition}")
    print(f"  Hypotheses: {len(config.meta_analysis.hypotheses)}")
    print(f"  Model: {config.meta_analysis.model}")

    engine = MetaAnalysisEngine(findings, config.meta_analysis)
    result = engine.run_meta_analysis(str(output_dir))

    # Extract verdict
    posteriors = result.get('posteriors', {}).get('K0', {})
    if posteriors:
        winner = max(posteriors.items(), key=lambda x: x[1])
        print(f"\n  Meta-verdict: {winner[0]} ({winner[1]:.1%})")
    else:
        print(f"\n  Meta-analysis complete")

    return result


def run_narrative_synthesis(
    component_results: Dict[str, Any],
    meta_result: Dict[str, Any],
    findings: UnifiedFindings,
    config: HermeneuticProjectConfig,
    output_dir: Path
) -> SynthesisDocument:
    """
    Phase 4: Narrative synthesis.

    Args:
        component_results: Component analysis results
        meta_result: Meta-analysis result
        findings: Unified findings
        config: Project configuration
        output_dir: Output directory

    Returns:
        SynthesisDocument
    """
    print("\n" + "=" * 60)
    print("PHASE 4: Narrative Synthesis")
    print("=" * 60)

    synthesizer = NarrativeSynthesizer(
        component_results,
        meta_result,
        findings,
        config
    )

    document = synthesizer.generate_synthesis()

    # Save outputs
    synthesis_path = output_dir / "synthesis.md"
    document.save_markdown(str(synthesis_path))
    print(f"  Saved: {synthesis_path}")

    # Save metadata
    metadata_path = output_dir / "synthesis_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(document.metadata, f, indent=2)

    return document


def load_results_from_checkpoint(output_dir: Path) -> Dict[str, AnalysisResult]:
    """Load results from checkpoint file."""
    checkpoint_path = output_dir / "checkpoint.json"
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    with open(checkpoint_path, 'r') as f:
        data = json.load(f)

    results = {}
    for topic_id, result_dict in data.get('results', {}).items():
        results[topic_id] = AnalysisResult.from_dict(result_dict)

    return results


def load_unified_findings(output_dir: Path) -> UnifiedFindings:
    """Load unified findings from file."""
    findings_path = output_dir / "unified_findings.json"
    if not findings_path.exists():
        raise FileNotFoundError(f"Findings not found: {findings_path}")

    with open(findings_path, 'r') as f:
        data = json.load(f)

    # Reconstruct UnifiedFindings
    from bfih_cross_analysis import Tension, Reinforcement

    tensions = [Tension(**t) for t in data.get('tensions', [])]
    reinforcements = [Reinforcement(**r) for r in data.get('reinforcements', [])]

    # Reconstruct winning_hypotheses as tuples
    winning_hypotheses = {}
    for k, v in data.get('winning_hypotheses', {}).items():
        if isinstance(v, dict):
            winning_hypotheses[k] = (v.get('hypothesis', 'Unknown'), v.get('posterior', 0.0))
        else:
            winning_hypotheses[k] = v

    return UnifiedFindings(
        verdicts=data.get('verdicts', {}),
        winning_hypotheses=winning_hypotheses,
        posterior_distributions=data.get('posterior_distributions', {}),
        key_evidence=data.get('key_evidence', {}),
        paradigm_sensitivities=data.get('paradigm_sensitivities', {}),
        tensions=tensions,
        reinforcements=reinforcements,
        total_evidence_items=data.get('total_evidence_items', 0),
        total_analyses=data.get('total_analyses', 0)
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="BFIH Hermeneutic Synthesis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run full synthesis
    python bfih_hermeneutic.py --project nature_of_mind.yaml

    # Resume interrupted project
    python bfih_hermeneutic.py --project nature_of_mind.yaml --resume

    # Run only meta-analysis and synthesis (analyses already done)
    python bfih_hermeneutic.py --project nature_of_mind.yaml --meta-only

    # Run only narrative synthesis (meta-analysis already done)
    python bfih_hermeneutic.py --project nature_of_mind.yaml --synthesis-only
        """
    )

    parser.add_argument(
        "--project", "-p",
        required=True,
        help="Path to project configuration YAML"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory override"
    )
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        help="Resume from checkpoint if available"
    )
    parser.add_argument(
        "--meta-only",
        action="store_true",
        help="Skip component analyses, run meta-analysis and synthesis"
    )
    parser.add_argument(
        "--synthesis-only",
        action="store_true",
        help="Skip analyses and meta-analysis, run only synthesis"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration and exit"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Print banner
    print_banner()

    # Load and validate configuration
    print(f"Loading project: {args.project}")
    try:
        config = load_project_config(args.project)
    except ValueError as e:
        print(f"\nConfiguration error:\n{e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\nConfiguration file not found: {args.project}")
        sys.exit(1)

    print(f"  Title: {config.project.title}")
    print(f"  Topics: {len(config.topics)}")
    print(f"  Execution order: {config.get_execution_order()}")

    if args.validate:
        print("\nConfiguration is valid.")
        sys.exit(0)

    # Set up output directory
    output_dir = Path(args.output or config.project.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Output: {output_dir}")

    # Save configuration copy
    config_copy_path = output_dir / "project_config.yaml"
    config.save_yaml(str(config_copy_path))

    start_time = datetime.now()

    try:
        # Phase 1: Component Analyses
        if args.synthesis_only or args.meta_only:
            print("\n  Loading results from checkpoint...")
            component_results = load_results_from_checkpoint(output_dir)
        else:
            component_results = run_component_analyses(config, output_dir, args.resume)

        # Phase 2: Cross-Analysis Integration
        if args.synthesis_only:
            print("\n  Loading unified findings...")
            findings = load_unified_findings(output_dir)
        else:
            findings = run_cross_analysis_integration(component_results, output_dir)

        # Phase 3: Meta-Analysis
        if args.synthesis_only:
            # Load meta-analysis result
            meta_files = list(output_dir.glob("meta_analysis_*.json"))
            if meta_files:
                with open(meta_files[0], 'r') as f:
                    meta_result = json.load(f)
            else:
                print("  No meta-analysis found, running...")
                meta_result = run_meta_analysis(findings, config, output_dir)
        else:
            meta_result = run_meta_analysis(findings, config, output_dir)

        # Phase 4: Narrative Synthesis
        document = run_narrative_synthesis(
            component_results, meta_result, findings, config, output_dir
        )

        # Summary
        duration = datetime.now() - start_time

        print("\n" + "=" * 60)
        print("SYNTHESIS COMPLETE")
        print("=" * 60)
        print(f"  Title: {config.project.title}")
        print(f"  Output: {output_dir}")
        print(f"  Duration: {duration}")
        print(f"  Component analyses: {len(component_results)}")
        print(f"  Total evidence: {findings.total_evidence_items}")
        print(f"  Tensions: {len(findings.tensions)}")
        print(f"  Reinforcements: {len(findings.reinforcements)}")
        print(f"\n  Main output: {output_dir / 'synthesis.md'}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress saved to checkpoint.")
        sys.exit(130)
    except Exception as e:
        logger.exception("Fatal error in hermeneutic synthesis")
        print(f"\n\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
