#!/usr/bin/env python3
"""
BFIH Hermeneutic Runner

Orchestrates the execution of multiple BFIH analyses with dependency management,
checkpointing, and context injection from prior analyses.
"""

import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

from hermeneutic_config_schema import (
    HermeneuticProjectConfig,
    TopicConfig,
    load_project_config
)

# Import the BFIH orchestrator
from bfih_orchestrator_fixed import BFIHOrchestrator, BFIHAnalysisRequest

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Stores the result of a single BFIH analysis."""
    topic_id: str
    analysis_id: str
    scenario_id: str
    proposition: str
    verdict: str
    winning_hypothesis: str
    winning_hypothesis_id: str
    winning_posterior: float
    posteriors: Dict[str, Dict[str, float]]
    evidence_count: int
    cluster_count: int
    report_path: str
    synopsis_path: Optional[str]
    json_path: str
    visualization_path: Optional[str]
    duration_seconds: float
    timestamp: str
    summary: str = ""
    key_findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ProjectCheckpoint:
    """Checkpoint state for resuming interrupted projects."""
    project_path: str
    completed_topics: List[str]
    results: Dict[str, Dict[str, Any]]  # topic_id -> result dict
    started_at: str
    last_updated: str

    def save(self, path: str) -> None:
        """Save checkpoint to file."""
        data = {
            'project_path': self.project_path,
            'completed_topics': self.completed_topics,
            'results': self.results,
            'started_at': self.started_at,
            'last_updated': datetime.utcnow().isoformat()
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'ProjectCheckpoint':
        """Load checkpoint from file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(
            project_path=data['project_path'],
            completed_topics=data['completed_topics'],
            results=data['results'],
            started_at=data['started_at'],
            last_updated=data['last_updated']
        )


class HermeneuticRunner:
    """
    Orchestrates multiple BFIH analyses with dependency management.

    Features:
    - Executes analyses in topological order (respecting dependencies)
    - Injects context from prior analyses when configured
    - Supports checkpointing for long-running projects
    - Saves all results and intermediate artifacts
    """

    def __init__(self, config: HermeneuticProjectConfig, output_dir: Optional[str] = None):
        """
        Initialize the runner.

        Args:
            config: Project configuration
            output_dir: Override output directory (uses config default if None)
        """
        self.config = config
        self.output_dir = Path(output_dir or config.project.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results: Dict[str, AnalysisResult] = {}
        self.checkpoint: Optional[ProjectCheckpoint] = None
        self.orchestrator = BFIHOrchestrator()

        # Set up logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for the runner."""
        log_path = self.output_dir / "hermeneutic_runner.log"
        handler = logging.FileHandler(log_path)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def _get_checkpoint_path(self) -> Path:
        """Get the checkpoint file path."""
        return self.output_dir / "checkpoint.json"

    def load_checkpoint(self) -> bool:
        """
        Load checkpoint if it exists.

        Returns:
            True if checkpoint was loaded, False otherwise
        """
        checkpoint_path = self._get_checkpoint_path()
        if checkpoint_path.exists():
            self.checkpoint = ProjectCheckpoint.load(str(checkpoint_path))

            # Restore results from checkpoint
            for topic_id, result_dict in self.checkpoint.results.items():
                self.results[topic_id] = AnalysisResult.from_dict(result_dict)

            logger.info(f"Loaded checkpoint with {len(self.checkpoint.completed_topics)} completed topics")
            return True
        return False

    def save_checkpoint(self) -> None:
        """Save current progress to checkpoint."""
        checkpoint = ProjectCheckpoint(
            project_path=str(self.config.project.output_dir),
            completed_topics=list(self.results.keys()),
            results={tid: r.to_dict() for tid, r in self.results.items()},
            started_at=self.checkpoint.started_at if self.checkpoint else datetime.utcnow().isoformat(),
            last_updated=datetime.utcnow().isoformat()
        )
        checkpoint.save(str(self._get_checkpoint_path()))
        logger.info(f"Saved checkpoint with {len(checkpoint.completed_topics)} completed topics")

    def run_all(self, resume: bool = False) -> Dict[str, AnalysisResult]:
        """
        Execute all analyses in dependency order.

        Args:
            resume: If True, load checkpoint and skip completed topics

        Returns:
            Dictionary mapping topic IDs to analysis results
        """
        if resume:
            self.load_checkpoint()

        execution_order = self.config.get_execution_order()
        total = len(execution_order)

        logger.info(f"Starting hermeneutic analysis project: {self.config.project.title}")
        logger.info(f"Execution order: {execution_order}")

        for i, topic_id in enumerate(execution_order, 1):
            # Skip if already completed (resume mode)
            if topic_id in self.results:
                logger.info(f"[{i}/{total}] Skipping '{topic_id}' (already completed)")
                continue

            topic = self.config.get_topic_by_id(topic_id)
            if not topic:
                logger.error(f"Topic not found: {topic_id}")
                continue

            logger.info(f"[{i}/{total}] Running analysis: '{topic_id}'")
            print(f"\n{'='*60}")
            print(f"[{i}/{total}] Analyzing: {topic.proposition[:50]}...")
            print(f"{'='*60}")

            try:
                result = self._run_single_analysis(topic)
                self.results[topic_id] = result

                # Save checkpoint after each successful analysis
                self.save_checkpoint()

                logger.info(f"[{i}/{total}] Completed '{topic_id}': {result.verdict}")
                print(f"  Verdict: {result.verdict}")
                print(f"  Winner: {result.winning_hypothesis} ({result.winning_posterior:.1%})")

            except Exception as e:
                logger.error(f"[{i}/{total}] Failed '{topic_id}': {e}", exc_info=True)
                print(f"  ERROR: {e}")
                # Continue with next topic rather than failing entire project
                continue

        return self.results

    def _run_single_analysis(self, topic: TopicConfig) -> AnalysisResult:
        """
        Run a single BFIH analysis for a topic.

        Args:
            topic: Topic configuration

        Returns:
            Analysis result
        """
        start_time = time.time()

        # Build context from prior analyses if configured
        prior_context = None
        if topic.context_from_prior and topic.depends_on:
            prior_context = self._build_prior_context(topic.depends_on)
            logger.info(f"Injecting context from {len(topic.depends_on)} prior analyses")

        # Prepare proposition (with optional context)
        proposition = topic.proposition
        if prior_context:
            proposition = f"{topic.proposition}\n\n[PRIOR ANALYSIS CONTEXT]\n{prior_context}"

        # Map difficulty to model behavior
        # The orchestrator will handle difficulty internally

        # Run the analysis using the orchestrator's analyze_topic method
        # Include prior context in the proposition if available
        result_obj = self.orchestrator.analyze_topic(
            proposition=proposition,  # Includes prior context if configured
            domain="philosophy",
            difficulty=topic.difficulty,
            reasoning_model=topic.model
        )

        duration = time.time() - start_time

        # Extract result information from BFIHAnalysisResult object
        analysis_id = result_obj.analysis_id
        scenario_id = result_obj.scenario_id

        # Get posteriors and find winner
        posteriors = result_obj.posteriors
        k0_posteriors = posteriors.get('K0', {})

        winning_hyp_id = max(k0_posteriors, key=k0_posteriors.get) if k0_posteriors else 'H0'
        winning_posterior = k0_posteriors.get(winning_hyp_id, 0.0)

        # Get hypothesis name from scenario config
        scenario_config = result_obj.scenario_config or {}
        hypotheses = scenario_config.get('hypotheses', [])
        winning_hyp_name = winning_hyp_id
        for h in hypotheses:
            if h.get('id') == winning_hyp_id:
                winning_hyp_name = h.get('name', h.get('short_name', winning_hyp_id))
                break

        # Determine verdict
        if winning_posterior > 0.6:
            verdict = "VALIDATED" if "TRUE" in winning_hyp_name.upper() else "REFUTED"
        elif winning_posterior > 0.4:
            verdict = "PARTIALLY_SUPPORTED"
        else:
            verdict = "INDETERMINATE"

        # Override with actual verdict if present
        report = result_obj.report or ''
        if '**Verdict:**' in report:
            for line in report.split('\n'):
                if '**Verdict:**' in line:
                    verdict = line.split('**Verdict:**')[1].strip().split()[0].upper()
                    break

        # Get evidence counts
        evidence = scenario_config.get('evidence', {})
        evidence_count = evidence.get('total_items', len(evidence.get('items', [])))
        cluster_count = evidence.get('total_clusters', len(evidence.get('clusters', [])))

        # Build file paths
        topic_dir = self.output_dir / "analyses" / topic.id
        topic_dir.mkdir(parents=True, exist_ok=True)

        # Save result files to topic directory
        base_name = f"bfih_report_{scenario_id}"
        import shutil

        report_path = topic_dir / f"{base_name}.md"
        json_path = topic_dir / f"{base_name}.json"
        synopsis_path = topic_dir / f"{base_name}_synopsis.md"
        viz_path = topic_dir / f"{base_name}_evidence_flow.png"

        # Save markdown report directly from result object
        if report:
            with open(report_path, 'w') as f:
                f.write(report)
            logger.info(f"Saved report: {report_path}")

        # Save JSON result
        result_dict = {
            'analysis_id': analysis_id,
            'scenario_id': scenario_id,
            'proposition': topic.proposition,
            'posteriors': posteriors,
            'scenario_config': scenario_config,
            'created_at': datetime.utcnow().isoformat()
        }
        with open(json_path, 'w') as f:
            json.dump(result_dict, f, indent=2)
        logger.info(f"Saved JSON: {json_path}")

        # Check for visualization in /tmp and copy it
        tmp_viz = Path(f"/tmp/{scenario_id}-evidence-flow.png")
        if tmp_viz.exists():
            shutil.copy(tmp_viz, viz_path)
            logger.info(f"Saved visualization: {viz_path}")

        # Extract summary from report
        summary = ""
        if "## Executive Summary" in report:
            summary_section = report.split("## Executive Summary")[1]
            summary_end = summary_section.find("\n## ")
            if summary_end > 0:
                summary = summary_section[:summary_end].strip()[:500]

        # Extract key findings
        key_findings = []
        if "**Primary Finding:**" in report:
            finding = report.split("**Primary Finding:**")[1].split("\n")[0].strip()
            key_findings.append(finding)

        return AnalysisResult(
            topic_id=topic.id,
            analysis_id=analysis_id,
            scenario_id=scenario_id,
            proposition=topic.proposition,
            verdict=verdict,
            winning_hypothesis=winning_hyp_name,
            winning_hypothesis_id=winning_hyp_id,
            winning_posterior=winning_posterior,
            posteriors=posteriors,
            evidence_count=evidence_count,
            cluster_count=cluster_count,
            report_path=str(report_path),
            synopsis_path=str(synopsis_path) if synopsis_path.exists() else None,
            json_path=str(json_path),
            visualization_path=str(viz_path) if viz_path.exists() else None,
            duration_seconds=duration,
            timestamp=datetime.utcnow().isoformat(),
            summary=summary,
            key_findings=key_findings
        )

    def _build_prior_context(self, dependencies: List[str]) -> str:
        """
        Build contextual framing from prior analysis conclusions.

        This context is injected into the analysis to condition the investigation
        based on findings from dependent analyses.

        Args:
            dependencies: List of topic IDs this analysis depends on

        Returns:
            Formatted context string
        """
        context_parts = []

        for dep_id in dependencies:
            if dep_id in self.results:
                result = self.results[dep_id]
                context_parts.append(f"""
Prior Analysis: {result.proposition}
  Verdict: {result.verdict}
  Leading Hypothesis: {result.winning_hypothesis} (posterior: {result.winning_posterior:.1%})
  Summary: {result.summary[:300]}...
""".strip())

        if context_parts:
            header = "The following prior BFIH analyses provide relevant context:\n"
            return header + "\n\n".join(context_parts)

        return ""

    def get_results_summary(self) -> str:
        """Generate a summary of all analysis results."""
        if not self.results:
            return "No analyses completed yet."

        lines = [
            f"# Hermeneutic Analysis Summary: {self.config.project.title}",
            "",
            f"**Topics Analyzed:** {len(self.results)}",
            ""
        ]

        for topic_id, result in self.results.items():
            lines.extend([
                f"## {topic_id}",
                f"**Proposition:** {result.proposition}",
                f"**Verdict:** {result.verdict}",
                f"**Winner:** {result.winning_hypothesis} ({result.winning_posterior:.1%})",
                f"**Evidence:** {result.evidence_count} items in {result.cluster_count} clusters",
                f"**Duration:** {result.duration_seconds:.1f}s",
                ""
            ])

        return "\n".join(lines)


def run_project(
    config_path: str,
    output_dir: Optional[str] = None,
    resume: bool = False
) -> Dict[str, AnalysisResult]:
    """
    Convenience function to run a complete hermeneutic analysis project.

    Args:
        config_path: Path to project configuration YAML
        output_dir: Override output directory
        resume: Resume from checkpoint if available

    Returns:
        Dictionary of analysis results
    """
    config = load_project_config(config_path)
    runner = HermeneuticRunner(config, output_dir)
    return runner.run_all(resume=resume)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run BFIH Hermeneutic Analysis Project")
    parser.add_argument("config", help="Path to project configuration YAML")
    parser.add_argument("--output", "-o", help="Output directory override")
    parser.add_argument("--resume", "-r", action="store_true", help="Resume from checkpoint")

    args = parser.parse_args()

    results = run_project(args.config, args.output, args.resume)

    print("\n" + "=" * 60)
    print("COMPONENT ANALYSES COMPLETE")
    print("=" * 60)
    for topic_id, result in results.items():
        print(f"  {topic_id}: {result.verdict} ({result.winning_posterior:.1%})")
