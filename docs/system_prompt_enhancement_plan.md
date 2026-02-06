# System Prompt Enhancement Plan

## Status: Planning (Not Yet Implemented)

This document records options for enhancing the BFIH system prompt based on analysis of the treatise (`Intellectual-Honesty_rev-4.pdf`) and comparison with the current implementation.

## Current State

The current system prompt in `get_bfih_system_context()` (~25 lines, ~500 tokens) provides:
- Basic BFIH identity and purpose
- Bayesian workflow overview
- Output format requirements
- Epistemic humility guidance

## Gap Analysis

The current prompt is **operationally adequate but philosophically thin**. Key gaps:

| Treatise Concept | Current Implementation | Gap |
|------------------|----------------------|-----|
| Hermeneutic foundation | Not mentioned | K0 treated as "objective" when treatise rejects pure objectivity |
| Four Forcing Functions | Referenced in phase prompts | Not in system identity |
| Discomfort Heuristic | Absent | No check for analyses that feel "too comfortable" |
| Evidence types (Smoking Gun, Hoop Test, etc.) | Not used | Could structure evidence evaluation |
| Cognitive bias warnings | Minimal | Confirmation bias, anchoring, base rate neglect not addressed |
| Incommensurable disagreements | Not mentioned | No guidance on when consensus is impossible |

## Enhancement Options

### Phase 1: Add Discomfort Heuristic (Low Risk, High Value)
**Estimated addition:** ~50 tokens

```
DISCOMFORT CHECK: If your analysis feels comfortable or confirms
what you expected to find, something is wrong. Genuine intellectual
honesty should produce conclusions that challenge at least some
of your priors.
```

**Rationale:** Single most impactful addition. Catches confirmation bias without restructuring prompts.

### Phase 2: Add Evidence Type Vocabulary (Low Risk, Medium Value)
**Estimated addition:** ~100 tokens

Add classification framework:
- **Smoking Gun**: High P(E|H), low P(E|~H) - strongly confirms
- **Hoop Test**: Low P(E|H), high P(E|~H) - failure eliminates
- **Straw-in-the-Wind**: Weakly affects probability either way
- **Doubly-Definitive**: Both confirms if present and eliminates if absent

**Rationale:** Enables more rigorous evidence evaluation in Phase 3.

### Phase 3: Revise K0 Framing (Medium Risk, High Value)
**Estimated change:** ~50 tokens (replacement, not addition)

Change from:
> "K0 represents an objective, evidence-based baseline"

To:
> "K0 represents a minimally-committed empirical stance, not pure objectivity. All paradigms including K0 embody background assumptions."

**Rationale:** Philosophical correctness per treatise. Risk: may change how model treats K0 posteriors.

### Phase 4: Add Cognitive Bias Warnings (Medium Risk, Medium Value)
**Estimated addition:** ~150 tokens

Explicit warnings about:
- Confirmation bias (seeking evidence that supports priors)
- Anchoring (over-weighting initial evidence)
- Base rate neglect (ignoring prior probabilities)
- Hedging bias (compressing toward 0.5)

**Rationale:** Only implement if calibration tests show systematic bias issues.

## Cost Analysis

| Configuration | System Prompt Tokens | Per-Analysis Overhead (13 calls) | Additional Cost |
|---------------|---------------------|----------------------------------|-----------------|
| Current | ~500 | 6,500 | Baseline |
| +Phase 1 | ~550 | 7,150 | +$0.02 |
| +Phase 1-2 | ~650 | 8,450 | +$0.06 |
| +Phase 1-3 | ~700 | 9,100 | +$0.08 |
| Full optimal | ~1,500 | 19,500 | +$0.40 |

## Risks

1. **Regression**: Current system produces valid analyses; changes could break JSON extraction or phase coordination
2. **Prompt interference**: Longer system prompts may compete with task-specific instructions
3. **Testing burden**: Each full analysis costs $5-15; no automated epistemological validation
4. **Over-correction**: Model may become overly cautious or apply discomfort heuristic inappropriately

## Recommendation

Implement phases incrementally with validation between each:
1. Phase 1 first (lowest risk, highest impact)
2. Run 2-3 full analyses to validate
3. Proceed to Phase 2 only if Phase 1 successful
4. Phase 3-4 only if specific issues identified

## Related Changes Completed

- Refactored all API calls to use OpenAI `instructions` parameter (separates system context from task prompts)
- All 13 phase callers now pass `instructions=get_bfih_system_context(...)` instead of embedding in prompt

---
*Generated: 2026-02-05*
*Based on analysis of Intellectual-Honesty_rev-4.pdf and bfih_orchestrator_fixed.py*
