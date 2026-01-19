#!/usr/bin/env python3
"""
BFIH Narrative Synthesis

Generates unified narrative from component analyses and meta-analysis,
weaving them into a coherent philosophical work with hermeneutic reflection.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

from openai import OpenAI

from bfih_cross_analysis import UnifiedFindings
from hermeneutic_config_schema import HermeneuticProjectConfig, SynthesisConfig

logger = logging.getLogger(__name__)


@dataclass
class SynthesisDocument:
    """Represents the synthesized document."""
    title: str
    author: str
    sections: List[Dict[str, Any]]
    bibliography: List[Dict[str, str]]
    metadata: Dict[str, Any]

    def to_markdown(self) -> str:
        """Convert document to markdown format."""
        lines = [
            f"# {self.title}",
            "",
            f"*{self.author}*",
            "",
            f"*Generated: {self.metadata.get('generated_at', 'Unknown')}*",
            "",
            "---",
            ""
        ]

        for section in self.sections:
            section_type = section.get("type", "section")
            title = section.get("title", "")
            content = section.get("content", "")

            if section_type == "chapter":
                lines.append(f"# {title}")
            elif section_type == "section":
                lines.append(f"## {title}")
            elif section_type == "subsection":
                lines.append(f"### {title}")

            lines.append("")
            lines.append(content)
            lines.append("")

            # Add appendix if present
            if section.get("appendix"):
                lines.append("<details>")
                lines.append("<summary>Technical Appendix</summary>")
                lines.append("")
                lines.append(section["appendix"])
                lines.append("")
                lines.append("</details>")
                lines.append("")

        # Add bibliography
        if self.bibliography:
            lines.append("---")
            lines.append("")
            lines.append("## Bibliography")
            lines.append("")
            for i, ref in enumerate(self.bibliography, 1):
                lines.append(f"{i}. {ref.get('citation', 'Unknown reference')}")
            lines.append("")

        return "\n".join(lines)

    def save_markdown(self, path: str) -> None:
        """Save document as markdown file."""
        with open(path, 'w') as f:
            f.write(self.to_markdown())


class NarrativeSynthesizer:
    """
    Generates unified narrative from component analyses and meta-analysis.

    The synthesizer weaves together:
    - Component analysis synopses as chapters
    - Hermeneutic reflection on part-whole relations
    - Meta-analysis conclusions
    - Final synthesis and open questions
    """

    def __init__(
        self,
        component_results: Dict[str, Any],
        meta_result: Dict[str, Any],
        unified_findings: UnifiedFindings,
        config: HermeneuticProjectConfig,
        client: Optional[OpenAI] = None
    ):
        """
        Initialize the synthesizer.

        Args:
            component_results: Dictionary mapping topic_id to analysis results
            meta_result: Meta-analysis result
            unified_findings: Integrated findings from cross-analysis
            config: Project configuration
            client: Optional OpenAI client
        """
        self.components = component_results
        self.meta = meta_result
        self.findings = unified_findings
        self.config = config

        if client is None:
            self.client = OpenAI()
        else:
            self.client = client

    def generate_synthesis(self) -> SynthesisDocument:
        """
        Generate the unified philosophical work.

        Returns:
            SynthesisDocument containing the complete synthesis
        """
        logger.info("Starting narrative synthesis")

        document = SynthesisDocument(
            title=self.config.project.title,
            author=self.config.project.author,
            sections=[],
            bibliography=[],
            metadata={
                "generated_at": datetime.utcnow().isoformat(),
                "component_analyses": len(self.components),
                "total_evidence_items": self.findings.total_evidence_items
            }
        )

        # 1. Introduction
        logger.info("Generating introduction...")
        intro = self._generate_introduction()
        document.sections.append({
            "type": "section",
            "title": "Introduction",
            "content": intro
        })

        # 2. Component chapters (using synopses)
        logger.info("Adding component chapters...")
        narrative_order = self._get_narrative_order()
        for topic_id in narrative_order:
            result = self.components.get(topic_id)
            if result:
                chapter_title = self._topic_to_chapter_title(topic_id, result)
                chapter_content = self._get_synopsis_or_summary(result)
                document.sections.append({
                    "type": "chapter",
                    "title": chapter_title,
                    "content": chapter_content,
                    "appendix": self._get_technical_appendix(result) if self.config.synthesis.include_technical_appendices else None
                })

        # 3. Hermeneutic reflection
        if self.config.synthesis.include_hermeneutic_reflection:
            logger.info("Generating hermeneutic reflection...")
            reflection = self._generate_hermeneutic_reflection()
            document.sections.append({
                "type": "section",
                "title": "Hermeneutic Interlude: Parts and Whole",
                "content": reflection
            })

        # 4. Meta-analysis chapter
        logger.info("Adding meta-analysis chapter...")
        meta_content = self._format_meta_analysis()
        document.sections.append({
            "type": "chapter",
            "title": "Toward a Unified Account",
            "content": meta_content
        })

        # 5. Conclusion
        logger.info("Generating conclusion...")
        conclusion = self._generate_conclusion()
        document.sections.append({
            "type": "section",
            "title": "Conclusion",
            "content": conclusion
        })

        # 6. Consolidated bibliography
        logger.info("Consolidating bibliography...")
        document.bibliography = self._consolidate_bibliographies()

        logger.info("Narrative synthesis complete")
        return document

    def _get_narrative_order(self) -> List[str]:
        """Get topic IDs in optimal narrative order."""
        # Use execution order from config (respects dependencies)
        return self.config.get_execution_order()

    def _topic_to_chapter_title(self, topic_id: str, result: Any) -> str:
        """Convert topic ID to readable chapter title."""
        # Get proposition if available
        if hasattr(result, 'proposition'):
            proposition = result.proposition
        elif isinstance(result, dict):
            proposition = result.get('proposition', '')
        else:
            proposition = ''

        if proposition:
            # Clean up proposition for title
            title = proposition.strip('?').strip()
            if len(title) > 80:
                title = title[:77] + "..."
            return title

        # Fallback to cleaned topic ID
        return topic_id.replace("_", " ").title()

    def _get_synopsis_or_summary(self, result: Any) -> str:
        """Get synopsis content or generate summary from result."""
        # Try to get synopsis from file
        synopsis_path = None
        if hasattr(result, 'synopsis_path'):
            synopsis_path = result.synopsis_path
        elif isinstance(result, dict):
            synopsis_path = result.get('synopsis_path')

        if synopsis_path and os.path.exists(synopsis_path):
            with open(synopsis_path, 'r') as f:
                return f.read()

        # Fallback to summary
        if hasattr(result, 'summary'):
            return result.summary
        elif isinstance(result, dict):
            return result.get('summary', 'No synopsis available.')

        return "Synopsis not available for this analysis."

    def _get_technical_appendix(self, result: Any) -> Optional[str]:
        """Get technical report excerpt for appendix."""
        report_path = None
        if hasattr(result, 'report_path'):
            report_path = result.report_path
        elif isinstance(result, dict):
            report_path = result.get('report_path')

        if report_path and os.path.exists(report_path):
            with open(report_path, 'r') as f:
                report = f.read()
            # Extract key technical sections
            sections_to_include = ["## 2. Hypothesis Set", "## 6. Paradigm Comparison"]
            appendix_parts = []
            for section in sections_to_include:
                if section in report:
                    start = report.index(section)
                    end = report.find("\n## ", start + len(section))
                    if end == -1:
                        end = len(report)
                    appendix_parts.append(report[start:end].strip())

            if appendix_parts:
                return "\n\n---\n\n".join(appendix_parts)

        return None

    def _generate_introduction(self) -> str:
        """Generate introduction section using LLM."""
        topics_summary = []
        for topic_id in self._get_narrative_order():
            result = self.components.get(topic_id)
            if result:
                prop = ""
                if hasattr(result, 'proposition'):
                    prop = result.proposition
                elif isinstance(result, dict):
                    prop = result.get('proposition', topic_id)
                topics_summary.append(f"- {prop}")

        prompt = f"""Write an introduction (600-800 words) for a philosophical work titled "{self.config.project.title}".

The work examines the following questions through rigorous Bayesian multi-paradigm analysis:
{chr(10).join(topics_summary)}

The introduction should:
1. Establish why these questions matter and how they connect
2. Briefly explain the BFIH methodology (Bayesian Framework for Intellectual Honesty)
3. Preview the structure of the work
4. Set appropriate epistemic expectations (uncertainty is a feature, not a bug)

Write in a measured, scholarly tone that is accessible to educated non-specialists.
Do NOT use bullet points or numbered lists. Write in flowing prose.
Do NOT include any headers or section markers."""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500
        )

        return response.choices[0].message.content.strip()

    def _generate_hermeneutic_reflection(self) -> str:
        """Generate hermeneutic reflection section using LLM."""
        analyses_summary = self._summarize_analyses_for_prompt()

        prompt = f"""Write a hermeneutic reflection (1200-1500 words) for a philosophical work that has examined {len(self.components)} interconnected questions through Bayesian analysis.

The analyses were:
{analyses_summary}

Tensions identified:
{self._format_tensions_for_prompt()}

Reinforcements identified:
{self._format_reinforcements_for_prompt()}

Write a reflective section examining:
1. How understanding each part required provisional understanding of the whole
2. How the whole only became visible through careful examination of parts
3. Where the hermeneutic circle tightened (convergence) vs remained loose (persistent uncertainty)
4. What this recursive structure reveals about the nature of philosophical inquiry itself

Write in a measured, forward-moving style. Use specific findings from the analyses as examples.
Do NOT use bullet points or numbered lists. Write in flowing prose.
Do NOT include any headers or section markers."""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2500
        )

        return response.choices[0].message.content.strip()

    def _format_meta_analysis(self) -> str:
        """Format meta-analysis results as narrative section."""
        # Get meta-analysis report if available
        if isinstance(self.meta, dict) and 'report' in self.meta:
            # Extract key sections from meta-analysis report
            report = self.meta['report']
            # Return executive summary and conclusions
            if "## Executive Summary" in report:
                start = report.index("## Executive Summary")
                # Find conclusions
                if "## 8. Conclusions" in report:
                    end = report.index("## 8. Conclusions")
                    conclusion_section = report[end:]
                    return report[start:end] + "\n\n---\n\n" + conclusion_section
                return report[start:]
            return report

        # Fallback: generate from structured data
        posteriors = self.meta.get('posteriors', {})
        k0_posteriors = posteriors.get('K0', {})

        if k0_posteriors:
            winner = max(k0_posteriors.items(), key=lambda x: x[1])
            summary = f"""The meta-analysis evaluated which synthesis framework best accounts for the pattern of findings across all component analyses.

Under the integrative naturalist paradigm (K0), the leading hypothesis is **{winner[0]}** with posterior probability {winner[1]:.1%}.

Full posterior distribution:
"""
            for h, p in sorted(k0_posteriors.items(), key=lambda x: -x[1]):
                summary += f"- {h}: {p:.1%}\n"

            return summary

        return "Meta-analysis results not available."

    def _generate_conclusion(self) -> str:
        """Generate concluding section using LLM."""
        prompt = f"""Write the conclusion (1000-1200 words) to a philosophical work titled "{self.config.project.title}".

The work examined these questions through rigorous Bayesian analysis:
{self._list_propositions()}

Key findings across analyses:
{self._summarize_findings_for_conclusion()}

Meta-analysis conclusion:
{self._summarize_meta_for_conclusion()}

Write a concluding section that:
1. States what we now know with greater confidence than before
2. States what remains genuinely uncertain and why
3. Identifies the most important open questions for future inquiry
4. Reflects on what this mode of inquiry (multi-paradigm Bayesian analysis) contributes to philosophy

Do NOT summarize each chapter. Synthesize. The reader has read the whole work.
End with a thought that opens outward rather than closing down.

Write in flowing prose without bullet points or numbered lists.
Do NOT include any headers or section markers."""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )

        return response.choices[0].message.content.strip()

    def _consolidate_bibliographies(self) -> List[Dict[str, str]]:
        """Consolidate bibliographies from all component analyses."""
        all_refs = []
        seen_urls = set()

        for topic_id, result in self.components.items():
            # Try to extract bibliography from report
            report_path = None
            if hasattr(result, 'report_path'):
                report_path = result.report_path
            elif isinstance(result, dict):
                report_path = result.get('report_path')

            if report_path and os.path.exists(report_path):
                with open(report_path, 'r') as f:
                    report = f.read()

                # Extract bibliography section
                if "## Bibliography" in report or "## 9. Bibliography" in report:
                    start_markers = ["## Bibliography", "## 9. Bibliography"]
                    for marker in start_markers:
                        if marker in report:
                            bib_section = report[report.index(marker):]
                            # Parse references
                            for line in bib_section.split('\n'):
                                if line.strip() and line[0].isdigit() and '.' in line:
                                    # Extract URL if present
                                    url = ""
                                    if "http" in line:
                                        url_start = line.index("http")
                                        url = line[url_start:].split()[0].rstrip(')')
                                        if url not in seen_urls:
                                            seen_urls.add(url)
                                            all_refs.append({
                                                "citation": line.split('.', 1)[1].strip() if '.' in line else line,
                                                "url": url,
                                                "source_topic": topic_id
                                            })
                                    elif url not in seen_urls or not url:
                                        all_refs.append({
                                            "citation": line.split('.', 1)[1].strip() if '.' in line else line,
                                            "url": "",
                                            "source_topic": topic_id
                                        })
                            break

        return all_refs[:100]  # Limit to 100 references

    def _summarize_analyses_for_prompt(self) -> str:
        """Summarize analyses for LLM prompt."""
        summaries = []
        for topic_id, result in self.components.items():
            prop = ""
            verdict = ""
            hyp = ""
            posterior = 0.0

            if hasattr(result, 'proposition'):
                prop = result.proposition
            elif isinstance(result, dict):
                prop = result.get('proposition', topic_id)

            if hasattr(result, 'verdict'):
                verdict = result.verdict
            elif isinstance(result, dict):
                verdict = result.get('verdict', 'UNKNOWN')

            if hasattr(result, 'winning_hypothesis'):
                hyp = result.winning_hypothesis
            elif isinstance(result, dict):
                hyp = result.get('winning_hypothesis', 'Unknown')

            if hasattr(result, 'winning_posterior'):
                posterior = result.winning_posterior
            elif isinstance(result, dict):
                posterior = result.get('winning_posterior', 0.0)

            summaries.append(f"- {prop}\n  Verdict: {verdict}, Winner: {hyp} ({posterior:.1%})")

        return "\n".join(summaries)

    def _format_tensions_for_prompt(self) -> str:
        """Format tensions for LLM prompt."""
        if not self.findings.tensions:
            return "No significant tensions identified."

        lines = []
        for t in self.findings.tensions:
            lines.append(f"- {t.description} (Severity: {t.severity})")
        return "\n".join(lines)

    def _format_reinforcements_for_prompt(self) -> str:
        """Format reinforcements for LLM prompt."""
        if not self.findings.reinforcements:
            return "No significant reinforcements identified."

        lines = []
        for r in self.findings.reinforcements:
            lines.append(f"- {r.description} (Strength: {r.strength})")
        return "\n".join(lines)

    def _list_propositions(self) -> str:
        """List all propositions for prompt."""
        props = []
        for topic_id, result in self.components.items():
            if hasattr(result, 'proposition'):
                props.append(f"- {result.proposition}")
            elif isinstance(result, dict):
                props.append(f"- {result.get('proposition', topic_id)}")
        return "\n".join(props)

    def _summarize_findings_for_conclusion(self) -> str:
        """Summarize key findings for conclusion prompt."""
        lines = []
        for topic_id, (hyp, posterior) in self.findings.winning_hypotheses.items():
            verdict = self.findings.verdicts.get(topic_id, "UNKNOWN")
            lines.append(f"- {topic_id}: {verdict} → {hyp} ({posterior:.1%})")
        return "\n".join(lines)

    def _summarize_meta_for_conclusion(self) -> str:
        """Summarize meta-analysis for conclusion prompt."""
        if isinstance(self.meta, dict):
            posteriors = self.meta.get('posteriors', {}).get('K0', {})
            if posteriors:
                winner = max(posteriors.items(), key=lambda x: x[1])
                return f"Leading synthesis: {winner[0]} ({winner[1]:.1%})"
        return "Meta-analysis pending"


def generate_synthesis(
    component_results: Dict[str, Any],
    meta_result: Dict[str, Any],
    unified_findings: UnifiedFindings,
    config: HermeneuticProjectConfig,
    output_path: str
) -> SynthesisDocument:
    """
    Convenience function to generate and save synthesis.

    Args:
        component_results: Results from component analyses
        meta_result: Meta-analysis result
        unified_findings: Integrated findings
        config: Project configuration
        output_path: Path to save synthesis markdown

    Returns:
        SynthesisDocument object
    """
    synthesizer = NarrativeSynthesizer(
        component_results, meta_result, unified_findings, config
    )

    document = synthesizer.generate_synthesis()
    document.save_markdown(output_path)

    return document


if __name__ == "__main__":
    print("Narrative synthesis module loaded.")
    print("Use generate_synthesis() or NarrativeSynthesizer class.")
