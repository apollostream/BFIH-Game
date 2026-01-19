# BFIH Hermeneutic Synthesis System

A system for orchestrating multiple connected BFIH analyses and synthesizing them into a unified philosophical work where individual analyses form chapters of a coherent whole as a hermeneutic circle.

## Overview

The hermeneutic synthesis system enables deep philosophical investigations that span multiple interconnected questions. Each analysis informs and is informed by the others, building toward integrated understanding through four phases:

1. **Component Analyses** - Run BFIH analyses on each topic in dependency order
2. **Cross-Analysis Integration** - Extract findings, identify tensions and reinforcements
3. **Meta-Analysis** - BFIH analysis treating component conclusions as evidence
4. **Narrative Synthesis** - Generate unified philosophical work

## Quick Start

```bash
# Run a full synthesis project
python bfih_hermeneutic.py --project projects/nature_of_mind.yaml

# Resume an interrupted project
python bfih_hermeneutic.py --project projects/nature_of_mind.yaml --resume

# Validate configuration without running
python bfih_hermeneutic.py --project projects/nature_of_mind.yaml --validate
```

## Project Configuration

Projects are defined in YAML format with four sections:

### 1. Project Metadata

```yaml
project:
  title: "The Nature of Mind"
  author: "BFIH Hermeneutic Synthesis System"
  output_dir: "./synthesis_output/nature_of_mind"
  description: "A multi-analysis investigation..."
```

### 2. Topic Network

Topics form a directed acyclic graph (DAG) where each topic can depend on prior topics:

```yaml
topics:
  - id: consciousness_llm
    proposition: "Can LLMs have subjective experience?"
    model: o3
    difficulty: hard
    depends_on: []  # Root topic

  - id: illusionism
    proposition: "Is phenomenal consciousness illusory?"
    model: o3
    difficulty: hard
    depends_on: [consciousness_llm]
    context_from_prior: true  # Inject findings from dependencies
```

**Topic Options:**
- `id`: Unique identifier for the topic
- `proposition`: The question to analyze
- `model`: Reasoning model (`o3-mini`, `o3`, `gpt-5`, etc.)
- `difficulty`: `easy`, `medium`, or `hard` (affects search depth)
- `depends_on`: List of topic IDs this analysis depends on
- `context_from_prior`: If true, inject dependency findings as context

### 3. Meta-Analysis Configuration

```yaml
meta_analysis:
  proposition: "What unified theory of mind accounts for these findings?"
  model: o3
  hypotheses:
    - id: H1
      name: "Functionalist Coherentism"
      description: "Mental properties are functional roles..."
    - id: H2
      name: "Biological Exceptionalism"
      description: "Genuine mentality requires biology..."
```

### 4. Synthesis Configuration

```yaml
synthesis:
  style: philosophical_treatise  # or academic_paper, essay
  target_length: book_chapter    # or essay, book
  include_hermeneutic_reflection: true
  include_technical_appendices: true
  include_visualizations: true
```

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
│  │  • Extract verdicts, posteriors, key findings            │       │
│  │  • Identify tensions and reinforcements                  │       │
│  │  • Map conceptual dependencies                           │       │
│  └─────────────────────────┬───────────────────────────────┘       │
│                            │                                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │                   META-ANALYSIS                          │       │
│  │  • Evidence = Component analysis conclusions             │       │
│  │  • Hypotheses = Grand synthesis frameworks               │       │
│  │  • Full BFIH Bayesian analysis                          │       │
│  └─────────────────────────┬───────────────────────────────┘       │
│                            │                                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │               NARRATIVE SYNTHESIS                        │       │
│  │  • Introduction and framing                             │       │
│  │  • Component synopses as chapters                       │       │
│  │  • Hermeneutic reflection on part-whole relations       │       │
│  │  • Meta-analysis synthesis                              │       │
│  │  • Conclusion with open questions                       │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## File Structure

```
bfih-game-exported-assets/
├── bfih_hermeneutic.py              # Main entry point
├── bfih_hermeneutic_runner.py       # Analysis orchestration
├── bfih_cross_analysis.py           # Integration layer
├── bfih_meta_analysis.py            # Meta-analysis engine
├── bfih_narrative_synthesis.py      # Narrative generation
├── hermeneutic_config_schema.py     # Configuration validation
├── projects/                        # Project configurations
│   └── nature_of_mind.yaml          # Example project
└── HERMENEUTIC_SYNTHESIS.md         # This documentation
```

## Output Structure

```
synthesis_output/nature_of_mind/
├── project_config.yaml              # Copy of configuration
├── checkpoint.json                  # Checkpoint for resume
├── unified_findings.json            # Cross-analysis findings
├── analyses/                        # Component analyses
│   ├── consciousness_llm/
│   │   ├── bfih_report_*.md
│   │   ├── bfih_report_*.json
│   │   └── *_synopsis.md
│   ├── illusionism/
│   └── ...
├── meta_analysis_*.md               # Meta-analysis report
├── meta_analysis_*.json             # Meta-analysis data
├── synthesis.md                     # Final unified work
└── synthesis_metadata.json          # Synthesis metadata
```

## Command Line Options

```
usage: bfih_hermeneutic.py [-h] --project PROJECT [--output OUTPUT]
                           [--resume] [--meta-only] [--synthesis-only]
                           [--validate] [--verbose]

Options:
  --project, -p     Path to project configuration YAML (required)
  --output, -o      Output directory override
  --resume, -r      Resume from checkpoint if available
  --meta-only       Skip component analyses (load from checkpoint)
  --synthesis-only  Skip analyses and meta-analysis (load from files)
  --validate        Validate configuration and exit
  --verbose, -v     Enable verbose output
```

## Extending the System

### Custom Paradigms

Override default meta-paradigms in your project configuration:

```yaml
meta_analysis:
  custom_paradigms:
    - id: K0
      name: "My Custom Paradigm"
      description: "Custom epistemic stance..."
```

### Adding Topics

Topics can be added to existing projects. The system will detect new topics and run only the analyses not yet completed when using `--resume`.

### Programmatic Usage

```python
from hermeneutic_config_schema import load_project_config
from bfih_hermeneutic_runner import HermeneuticRunner
from bfih_cross_analysis import CrossAnalysisIntegrator
from bfih_meta_analysis import MetaAnalysisEngine
from bfih_narrative_synthesis import NarrativeSynthesizer

# Load configuration
config = load_project_config("projects/my_project.yaml")

# Run analyses
runner = HermeneuticRunner(config)
results = runner.run_all()

# Integrate findings
integrator = CrossAnalysisIntegrator(results)
findings = integrator.extract_unified_findings()

# Run meta-analysis
engine = MetaAnalysisEngine(findings, config.meta_analysis)
meta_result = engine.run_meta_analysis()

# Generate synthesis
synthesizer = NarrativeSynthesizer(results, meta_result, findings, config)
document = synthesizer.generate_synthesis()
document.save_markdown("synthesis.md")
```

## The Hermeneutic Circle

The system embodies the hermeneutic principle that understanding parts requires understanding the whole, and vice versa:

1. **Part → Whole**: Each component analysis contributes findings that inform the meta-analysis synthesis
2. **Whole → Part**: The dependency structure allows later analyses to incorporate context from earlier ones
3. **Iteration**: The checkpoint system enables re-running analyses with updated understanding
4. **Reflection**: The narrative synthesis includes explicit hermeneutic reflection on how parts and whole inform each other

## Costs and Performance

**Estimated costs per project** (varies by model and topic count):
- Component analyses: ~$5-15 per topic with o3
- Meta-analysis: ~$3-8 with o3
- Narrative synthesis: ~$1-3 with GPT-4o

**Performance tips:**
- Use `o3-mini` for initial exploration, `o3` for final runs
- Set difficulty to `medium` for faster iterations
- Use `--resume` to avoid re-running completed analyses

## Requirements

- Python 3.10+
- OpenAI API key with access to o3/GPT-4o models
- Dependencies: `openai`, `pyyaml`

## License

Part of the BFIH (Bayesian Framework for Intellectual Honesty) project.
