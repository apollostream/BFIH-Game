# Plan: Hermeneutic Synthesis System for BFIH

## Overview

An auxiliary system that orchestrates multiple connected BFIH analyses, synthesizes their findings through meta-analysis, and produces a unified philosophical work where individual analyses form chapters of a coherent whole.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HERMENEUTIC SYNTHESIS SYSTEM                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Topic 1    │    │   Topic 2    │    │   Topic N    │          │
│  │   Analysis   │───▶│   Analysis   │───▶│   Analysis   │          │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │
│         │                   │                   │                   │
│         ▼                   ▼                   ▼                   │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │              CROSS-ANALYSIS INTEGRATION                  │       │
│  │  • Extract posteriors, key findings, tensions            │       │
│  │  • Build unified evidence corpus                         │       │
│  │  • Map conceptual dependencies                           │       │
│  └─────────────────────────┬───────────────────────────────┘       │
│                            │                                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │                   META-ANALYSIS                          │       │
│  │  • Proposition: "What unified theory accounts for..."    │       │
│  │  • Evidence: Conclusions from component analyses         │       │
│  │  • Hypotheses: Grand synthetic frameworks                │       │
│  └─────────────────────────┬───────────────────────────────┘       │
│                            │                                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │               NARRATIVE SYNTHESIS                        │       │
│  │  • Weave synopses into unified philosophical work        │       │
│  │  • Hermeneutic reflection on part-whole relations        │       │
│  │  • Technical appendices from full reports                │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Project Configuration (`hermeneutic_project.yaml`)

Defines the topic network, dependencies, and synthesis parameters.

```yaml
project:
  title: "The Nature of Mind: A Multi-Analysis Investigation"
  author: "BFIH Hermeneutic Synthesis System"
  output_dir: "./synthesis_output"

topics:
  - id: "consciousness_llm"
    proposition: "Can artificial systems like LLMs have genuine subjective experience?"
    model: "o3"
    difficulty: "hard"
    depends_on: []  # Root analysis

  - id: "illusionism"
    proposition: "Is phenomenal consciousness an introspective illusion rather than an irreducible feature of reality?"
    model: "o3"
    difficulty: "hard"
    depends_on: ["consciousness_llm"]
    context_from_prior: true  # Incorporate prior findings in framing

  - id: "understanding_vs_mimicry"
    proposition: "Does sophisticated language use require genuine understanding, or can it emerge from pattern matching alone?"
    model: "o3"
    difficulty: "hard"
    depends_on: ["consciousness_llm", "illusionism"]

  - id: "personal_identity"
    proposition: "Does personal identity require psychological continuity, or can identity persist through discontinuous episodes?"
    model: "o3"
    difficulty: "hard"
    depends_on: ["consciousness_llm"]

  - id: "moral_status"
    proposition: "What properties are necessary and sufficient for an entity to have moral status deserving of ethical consideration?"
    model: "o3"
    difficulty: "hard"
    depends_on: ["consciousness_llm", "personal_identity"]

meta_analysis:
  proposition: "What unified theory of mind best accounts for the findings across consciousness, understanding, identity, and moral status?"
  hypotheses:
    - "Functionalist Coherentism: Mental properties are functional roles; all findings cohere under computational functionalism"
    - "Biological Exceptionalism: Genuine mentality requires biological substrate; AI systems are sophisticated zombies"
    - "Graded Mentality: Mental properties exist on a continuum; different systems instantiate different degrees"
    - "Eliminative Pluralism: Folk mental concepts are incoherent; we need new vocabulary for different system types"
    - "Panpsychist Integration: Consciousness is fundamental; both biological and artificial systems partake differently"
    - "Pragmatic Deflationism: Metaphysical questions are underdetermined; focus on functional and ethical implications"

synthesis:
  style: "philosophical_treatise"
  target_length: "book_chapter"  # or "essay", "book"
  include_hermeneutic_reflection: true
  include_technical_appendices: true
```

### 2. Analysis Runner (`bfih_hermeneutic_runner.py`)

Orchestrates the execution of multiple analyses respecting dependencies.

```python
class HermeneuticRunner:
    """
    Orchestrates multiple BFIH analyses with dependency management.
    """

    def __init__(self, project_config: str):
        self.config = load_yaml(project_config)
        self.results = {}  # topic_id -> AnalysisResult
        self.orchestrator = BFIHOrchestrator()

    def run_all(self) -> Dict[str, AnalysisResult]:
        """Execute all analyses in dependency order."""
        execution_order = self._topological_sort()

        for topic_id in execution_order:
            topic = self._get_topic(topic_id)

            # Build context from prior analyses if configured
            prior_context = None
            if topic.get("context_from_prior"):
                prior_context = self._build_prior_context(topic["depends_on"])

            # Run analysis
            result = self._run_single_analysis(topic, prior_context)
            self.results[topic_id] = result

            # Save intermediate result
            self._save_result(topic_id, result)

        return self.results

    def _build_prior_context(self, dependencies: List[str]) -> str:
        """
        Build contextual framing from prior analysis conclusions.
        Injected into the analysis prompt to condition the investigation.
        """
        context_parts = []
        for dep_id in dependencies:
            if dep_id in self.results:
                result = self.results[dep_id]
                context_parts.append(
                    f"Prior finding ({dep_id}): {result.verdict} - "
                    f"Leading hypothesis: {result.winning_hypothesis} "
                    f"(posterior: {result.winning_posterior:.1%})"
                )
        return "\n".join(context_parts)

    def _topological_sort(self) -> List[str]:
        """Return topics in dependency-respecting order."""
        # Standard topological sort implementation
        ...
```

### 3. Cross-Analysis Integrator (`bfih_cross_analysis.py`)

Extracts and structures findings across all component analyses.

```python
class CrossAnalysisIntegrator:
    """
    Integrates findings across multiple BFIH analyses.
    """

    def __init__(self, results: Dict[str, AnalysisResult]):
        self.results = results

    def extract_unified_findings(self) -> UnifiedFindings:
        """
        Extract structured findings suitable for meta-analysis.
        """
        return UnifiedFindings(
            verdicts=self._extract_verdicts(),
            winning_hypotheses=self._extract_winners(),
            posterior_distributions=self._extract_posteriors(),
            key_evidence=self._extract_key_evidence(),
            paradigm_sensitivities=self._extract_sensitivities(),
            tensions=self._identify_tensions(),
            reinforcements=self._identify_reinforcements()
        )

    def _identify_tensions(self) -> List[Tension]:
        """
        Identify places where analyses produce conflicting implications.
        E.g., if illusionism is validated but consciousness analysis
        favored IIT-based accounts.
        """
        tensions = []
        # Compare hypotheses across analyses for logical conflicts
        ...
        return tensions

    def _identify_reinforcements(self) -> List[Reinforcement]:
        """
        Identify places where analyses mutually support conclusions.
        E.g., if personal identity analysis supports bundle theory,
        which coheres with certain consciousness findings.
        """
        reinforcements = []
        # Compare hypotheses across analyses for logical support
        ...
        return reinforcements

    def generate_meta_evidence(self) -> List[Dict]:
        """
        Convert analysis conclusions into evidence items for meta-analysis.
        Each component analysis becomes an evidence item.
        """
        evidence_items = []
        for topic_id, result in self.results.items():
            evidence_items.append({
                "evidence_id": f"META_{topic_id}",
                "description": f"BFIH analysis of '{result.proposition}' concluded {result.verdict}. "
                              f"Winning hypothesis: {result.winning_hypothesis} "
                              f"(posterior {result.winning_posterior:.1%}). "
                              f"Key finding: {result.summary}",
                "source_name": "BFIH Analysis",
                "source_url": f"file://{result.report_path}",
                "evidence_type": "systematic_analysis",
                "supports_hypotheses": self._map_to_meta_hypotheses(result, "support"),
                "refutes_hypotheses": self._map_to_meta_hypotheses(result, "refute")
            })
        return evidence_items
```

### 4. Meta-Analysis Engine (`bfih_meta_analysis.py`)

Runs a BFIH analysis where evidence consists of prior analysis conclusions.

```python
class MetaAnalysisEngine:
    """
    Performs BFIH analysis at the meta-level, treating component
    analysis conclusions as evidence.
    """

    def __init__(self, unified_findings: UnifiedFindings, meta_config: Dict):
        self.findings = unified_findings
        self.config = meta_config
        self.orchestrator = BFIHOrchestrator()

    def run_meta_analysis(self) -> AnalysisResult:
        """
        Run BFIH analysis with component findings as evidence.
        """
        # Generate meta-evidence from component analyses
        meta_evidence = self._prepare_meta_evidence()

        # Generate meta-paradigms (philosophies of mind)
        meta_paradigms = self._generate_meta_paradigms()

        # Generate meta-hypotheses from config
        meta_hypotheses = self.config["hypotheses"]

        # Build scenario config
        scenario_config = {
            "proposition": self.config["proposition"],
            "paradigms": meta_paradigms,
            "hypotheses": meta_hypotheses,
            "injected_evidence": meta_evidence,  # Skip web search, use these
            "tensions": self.findings.tensions,
            "reinforcements": self.findings.reinforcements
        }

        # Run analysis with injected evidence (no web search)
        result = self.orchestrator.analyze_with_injected_evidence(
            scenario_config,
            model=self.config.get("model", "o3"),
            synopsis=True
        )

        return result

    def _generate_meta_paradigms(self) -> List[Dict]:
        """
        Generate paradigms for meta-analysis: different philosophies
        of mind that would interpret the component findings differently.
        """
        return [
            {
                "id": "K0",
                "name": "Integrative Naturalist",
                "description": "Seeks coherent naturalistic account across all findings"
            },
            {
                "id": "K1",
                "name": "Reductive Physicalist",
                "description": "All mental phenomena reduce to physical processes"
            },
            {
                "id": "K2",
                "name": "Property Dualist",
                "description": "Mental properties are non-reducible but depend on physical"
            },
            {
                "id": "K3",
                "name": "Pragmatic Functionalist",
                "description": "Focus on functional roles, bracket metaphysics"
            },
            {
                "id": "K4",
                "name": "Phenomenological Traditionalist",
                "description": "Privileges first-person experience as primary datum"
            }
        ]
```

### 5. Narrative Synthesizer (`bfih_narrative_synthesis.py`)

Weaves all analyses into a unified philosophical work.

```python
class NarrativeSynthesizer:
    """
    Generates unified narrative from component analyses and meta-analysis.
    """

    def __init__(self,
                 component_results: Dict[str, AnalysisResult],
                 meta_result: AnalysisResult,
                 unified_findings: UnifiedFindings,
                 config: Dict):
        self.components = component_results
        self.meta = meta_result
        self.findings = unified_findings
        self.config = config

    def generate_synthesis(self) -> SynthesisDocument:
        """
        Generate the unified philosophical work.
        """
        document = SynthesisDocument(
            title=self.config["project"]["title"],
            author=self.config["project"]["author"]
        )

        # 1. Introduction: Frame the inquiry
        document.add_section(self._generate_introduction())

        # 2. Component chapters: One per analysis (using synopses)
        for topic_id in self._get_narrative_order():
            result = self.components[topic_id]
            document.add_chapter(
                title=self._topic_to_chapter_title(topic_id),
                content=result.synopsis,
                technical_appendix=result.report if self.config["synthesis"]["include_technical_appendices"] else None
            )

        # 3. Hermeneutic interlude: How parts inform whole
        if self.config["synthesis"]["include_hermeneutic_reflection"]:
            document.add_section(self._generate_hermeneutic_reflection())

        # 4. Meta-analysis chapter: The synthesis
        document.add_chapter(
            title="Toward a Unified Account",
            content=self.meta.synopsis,
            technical_appendix=self.meta.report
        )

        # 5. Conclusion: What we've learned, what remains open
        document.add_section(self._generate_conclusion())

        # 6. Consolidated bibliography
        document.add_bibliography(self._consolidate_bibliographies())

        return document

    def _generate_hermeneutic_reflection(self) -> str:
        """
        Generate section reflecting on part-whole relations.
        How did each analysis condition the others?
        What tensions emerged? What unexpected coherences?
        """
        prompt = f"""
        You are writing a hermeneutic reflection for a philosophical work that has
        examined {len(self.components)} interconnected questions through Bayesian analysis.

        The analyses were:
        {self._summarize_analyses()}

        Tensions identified:
        {self.findings.tensions}

        Reinforcements identified:
        {self.findings.reinforcements}

        Write a reflective section (1500-2000 words) examining:
        1. How understanding each part required provisional understanding of the whole
        2. How the whole only became visible through careful examination of parts
        3. Where the hermeneutic circle tightened (convergence) vs remained loose (persistent uncertainty)
        4. What this recursive structure reveals about the nature of philosophical inquiry itself

        Write in the measured, forward-moving style of the component synopses.
        """

        return self._generate_with_llm(prompt)

    def _generate_conclusion(self) -> str:
        """
        Generate concluding section synthesizing all findings.
        """
        prompt = f"""
        You are writing the conclusion to a philosophical work titled "{self.config['project']['title']}".

        The work examined these questions through rigorous Bayesian analysis:
        {self._list_propositions()}

        The meta-analysis concluded: {self.meta.verdict}
        Winning meta-hypothesis: {self.meta.winning_hypothesis} ({self.meta.winning_posterior:.1%})

        Key tensions that remained unresolved:
        {self.findings.tensions}

        Write a concluding section (1000-1500 words) that:
        1. States what we now know with greater confidence than before
        2. States what remains genuinely uncertain and why
        3. Identifies the most important open questions for future inquiry
        4. Reflects on what this mode of inquiry (multi-paradigm Bayesian analysis) contributes to philosophy

        Do not summarize each chapter. Synthesize. The reader has read the whole work.
        End with a thought that opens outward rather than closing down.
        """

        return self._generate_with_llm(prompt)
```

### 6. Main Entry Point (`bfih_hermeneutic.py`)

```python
#!/usr/bin/env python3
"""
BFIH Hermeneutic Synthesis System

Orchestrates multiple connected BFIH analyses and synthesizes them
into a unified philosophical work.

Usage:
    python bfih_hermeneutic.py --project project.yaml
    python bfih_hermeneutic.py --project project.yaml --resume  # Resume from checkpoint
    python bfih_hermeneutic.py --project project.yaml --meta-only  # Skip component analyses
"""

import argparse
from bfih_hermeneutic_runner import HermeneuticRunner
from bfih_cross_analysis import CrossAnalysisIntegrator
from bfih_meta_analysis import MetaAnalysisEngine
from bfih_narrative_synthesis import NarrativeSynthesizer

def main():
    parser = argparse.ArgumentParser(description="BFIH Hermeneutic Synthesis")
    parser.add_argument("--project", required=True, help="Project configuration YAML")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--meta-only", action="store_true", help="Run only meta-analysis")
    parser.add_argument("--output", help="Output directory override")
    args = parser.parse_args()

    config = load_yaml(args.project)
    output_dir = args.output or config["project"]["output_dir"]

    # Phase 1: Run component analyses
    if not args.meta_only:
        print("=" * 60)
        print("PHASE 1: Component Analyses")
        print("=" * 60)

        runner = HermeneuticRunner(args.project)
        if args.resume:
            runner.load_checkpoint()

        results = runner.run_all()
        runner.save_checkpoint()
    else:
        results = load_results_from_checkpoint(output_dir)

    # Phase 2: Cross-analysis integration
    print("=" * 60)
    print("PHASE 2: Cross-Analysis Integration")
    print("=" * 60)

    integrator = CrossAnalysisIntegrator(results)
    unified_findings = integrator.extract_unified_findings()

    print(f"  Tensions identified: {len(unified_findings.tensions)}")
    print(f"  Reinforcements identified: {len(unified_findings.reinforcements)}")

    # Phase 3: Meta-analysis
    print("=" * 60)
    print("PHASE 3: Meta-Analysis")
    print("=" * 60)

    meta_engine = MetaAnalysisEngine(unified_findings, config["meta_analysis"])
    meta_result = meta_engine.run_meta_analysis()

    print(f"  Meta-verdict: {meta_result.verdict}")
    print(f"  Winning meta-hypothesis: {meta_result.winning_hypothesis}")

    # Phase 4: Narrative synthesis
    print("=" * 60)
    print("PHASE 4: Narrative Synthesis")
    print("=" * 60)

    synthesizer = NarrativeSynthesizer(results, meta_result, unified_findings, config)
    document = synthesizer.generate_synthesis()

    # Save outputs
    document.save_markdown(f"{output_dir}/synthesis.md")
    document.save_pdf(f"{output_dir}/synthesis.pdf")  # Optional, requires pandoc

    print("=" * 60)
    print("SYNTHESIS COMPLETE")
    print("=" * 60)
    print(f"  Output: {output_dir}/synthesis.md")
    print(f"  Component analyses: {len(results)}")
    print(f"  Total evidence items: {sum(r.evidence_count for r in results.values())}")
    print(f"  Meta-analysis verdict: {meta_result.verdict}")

if __name__ == "__main__":
    main()
```

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Project configuration schema and loader
- [ ] Analysis runner with dependency management
- [ ] Checkpoint/resume system for long-running projects
- [ ] Result storage and retrieval

### Phase 2: Integration Layer
- [ ] Cross-analysis integrator
- [ ] Tension/reinforcement detection algorithms
- [ ] Meta-evidence generation from component findings

### Phase 3: Meta-Analysis
- [ ] Extend BFIHOrchestrator to accept injected evidence (skip web search)
- [ ] Meta-paradigm generation
- [ ] Meta-hypothesis evaluation

### Phase 4: Narrative Synthesis
- [ ] Chapter structure generation
- [ ] Hermeneutic reflection generator
- [ ] Bibliography consolidation
- [ ] Markdown/PDF output

### Phase 5: Refinement
- [ ] Iterative re-analysis capability (true hermeneutic spiral)
- [ ] Visualization of topic network and findings
- [ ] Interactive mode for steering synthesis

## File Structure

```
bfih-game-exported-assets/
├── bfih_orchestrator_fixed.py      # Existing - extend with injected_evidence support
├── bfih_hermeneutic.py             # Main entry point
├── bfih_hermeneutic_runner.py      # Analysis orchestration
├── bfih_cross_analysis.py          # Integration layer
├── bfih_meta_analysis.py           # Meta-analysis engine
├── bfih_narrative_synthesis.py     # Narrative generation
├── hermeneutic_config_schema.py    # Configuration validation
└── projects/                       # Project configurations
    └── nature_of_mind.yaml         # Example project
```

## Example Execution

```bash
# Full run with 5 component analyses + meta-analysis + synthesis
python bfih_hermeneutic.py --project projects/nature_of_mind.yaml

# Resume after interruption
python bfih_hermeneutic.py --project projects/nature_of_mind.yaml --resume

# Re-run just meta-analysis and synthesis (components already done)
python bfih_hermeneutic.py --project projects/nature_of_mind.yaml --meta-only
```

## Estimated Effort

| Phase | Components | Estimate |
|-------|-----------|----------|
| Phase 1 | Core infrastructure | 4-6 hours |
| Phase 2 | Integration layer | 3-4 hours |
| Phase 3 | Meta-analysis | 3-4 hours |
| Phase 4 | Narrative synthesis | 4-6 hours |
| Phase 5 | Refinement | 2-4 hours |
| **Total** | | **16-24 hours** |

## Dependencies

- Existing: `bfih_orchestrator_fixed.py`, OpenAI API
- New: `pyyaml` (config), `networkx` (dependency graphs), `pandoc` (optional PDF)

## Open Questions

1. **Iteration depth**: How many hermeneutic cycles? One pass, or iterate until convergence?
2. **Human-in-the-loop**: Should synthesis allow human steering between phases?
3. **Parallel execution**: Run independent analyses concurrently to save time?
4. **Cost management**: Full o3 runs are expensive; allow model mixing per topic?
