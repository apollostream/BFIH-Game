---
title: "Intellectual Honesty Analysis: {{TOPIC_OR_PROPOSITION_SHORT_TITLE}}"
author: "{{ANALYST_NAME}}, analysis conducted using {{LLM_SYSTEM_NAME}} with Bayesian Framework for Intellectual Honesty (BFIH)"
date: "{{DATE}}"
output:
  pdf_document:
    latex_engine: lualatex
    toc: yes
    toc_depth: 2
  html_document:
    toc: yes
    toc_depth: 2
urlcolor: blue
linkcolor: red
---

\newpage

# Intellectual Honesty Analysis: {{TOPIC_OR_PROPOSITION_SHORT_TITLE}}
## {{OPTIONAL_SUBTITLE_OR_TAGLINE}}

**Analysis conducted using {{LLM_SYSTEM_NAME}} with Bayesian Framework for Intellectual Honesty (BFIH, current revision).**

---

> GLOBAL INSTRUCTION TO MODEL (MUST BE OBEYED AND THEN REMOVED FROM FINAL OUTPUT):
> - Replace all {{PLACEHOLDER_TEXT}} with concrete content for the specific topic.
> - Delete all instructional text in ALL CAPS or inside `<<LIKE THIS>>` before producing the final answer.
> - Follow the structure, headings, and sequence exactly. Do not omit or reorder sections.
> - Use formal, analytic language appropriate for expert readers.
> - Ensure all hypotheses are mutually exclusive and collectively exhaustive (MECE).
> - Use explicit decimal priors and posteriors (e.g., 0.125, not 12.5%).
> - Implement and show a Python script that computes posteriors from priors and likelihoods, and base all reported posterior values on that script’s output.
> - Perform full sensitivity testing of key conclusions with at least ±20% prior variation for selected hypotheses.
> - Include both narrative evidence descriptions and Bayesian likelihood tables for each evidence item.
> - Include a dedicated **Limitations** section as specified below.

---

## Proposition Under Investigation

**Proposition:** **"{{STATE_THE_CENTRAL_PROPOSITION_TO_BE_EVALUATED_AS_A_CLEAR_TESTABLE_CLAIM}}"**

<<INSTRUCTION TO MODEL:  
- Write a single, clear, testable proposition in quotes.  
- This proposition should be precise enough that evidence and hypotheses can clearly bear for or against it.  
- Avoid vague or compound claims; if necessary, focus on one primary proposition.>>

---

## Executive Summary

<<INSTRUCTION TO MODEL:  
Produce a concise 3–7 paragraph executive summary that:  
1. States the primary finding with an explicit verdict on the proposition (e.g., VALIDATED, PARTIALLY VALIDATED, PARTIALLY REJECTED, REJECTED, or INDETERMINATE).  
2. Summarizes the dominant paradigm’s conclusions and at least one alternative paradigm’s contrasting interpretation.  
3. Reports key posterior probabilities (decimal form) for the most decision-relevant hypotheses (e.g., H1, H2, Hk) under the dominant paradigm.  
4. Highlights 5–10 of the most important evidence points and their qualitative directional impact (supporting which hypotheses and how strongly).  
5. Explains, at a high level, whether conclusions are robust under sensitivity analysis.  
6. Explicitly distinguishes between (a) what can be said with high confidence and (b) what remains uncertain or contingent.>>

Example elements (adapt content to actual topic):

- **Primary Finding:** The proposition is **{{VERDICT_WORD}}**. Under the dominant paradigm, hypotheses {{LIST_KEY_HYPOTHESES}} have posterior probabilities approximately {{LIST_DECIMAL_VALUES}}.
- **Key Evidence:** Brief bullet sentences summarizing the most important empirical findings and their implications.

---

## DELIVERABLE 1: Dominant Paradigm Statement (K₀)

### My Interpretive Paradigm (K₀)

<<INSTRUCTION TO MODEL:  
- Clearly state the dominant interpretive paradigm K₀ from which the analysis is primarily conducted (e.g., "Legal-Institutionalist", "Evidentialist-Bayesian", "Market-Efficiency", "Public-Health Precautionary", etc.).  
- This paradigm should specify your background assumptions, what you count as legitimate evidence, and how you interpret causal mechanisms.  
- Describe this paradigm in 4–8 numbered points that specify:  
  1. Core assumptions about the domain.  
  2. How evidence is prioritized and weighed.  
  3. How rights/interests/costs/benefits are conceptualized.  
  4. How temporal dynamics (e.g., trends, lags, structural breaks) are interpreted.>>

**Background Knowledge & Expertise**

<<INSTRUCTION TO MODEL:  
- Briefly describe the “idealized analyst” performing this BFIH analysis: domain knowledge, methodological expertise, and access to data sources.  
- Also list at least 3–5 acknowledged limitations and biases (e.g., status-quo bias, myopia on long-tail risks, tendency to overweight quantitative vs. qualitative evidence).>>

**Expected Outcomes (Pre-Commitment)**

<<INSTRUCTION TO MODEL:  
- Before introducing any new evidence in this report, explicitly state 3–6 “pre-committed” expectations given K₀.  
- These should be framed as provisional expectations about which hypotheses are likely to be supported and which patterns might appear in the data.  
- The purpose is to make background expectations explicit for intellectual honesty.>>

---

## DELIVERABLE 2: Hypothesis Set (H₀)

### Mutually Exclusive, Collectively Exhaustive Hypotheses

<<INSTRUCTION TO MODEL:  
- Define a set of hypotheses H1, H2, ..., Hn, and H0 (catch-all) that are **mutually exclusive** (no two can be simultaneously true in the exact same sense) and **collectively exhaustive** (one of them must be true, possibly H0 if others are incomplete).  
- Each hypothesis must:  
  - Be stated in a short bold heading (e.g., **H1: Brief Descriptive Name**).  
  - Have a short paragraph that clearly defines the state of the world it describes, in relation to the central proposition.  
  - Include 3–6 concrete, operationalized testable predictions that specify what empirical patterns would be expected if this hypothesis were true.  
- Design hypotheses to allow meaningful differential likelihoods P(E|Hᵢ) for observed evidence.  
- Ensure that, taken together, the hypotheses provide a full explanatory partition of plausible scenarios regarding the proposition.>>

**Example format for each hypothesis (fill with topic-specific content):**

**H1: {{SHORT_NAME}}**

{{NARRATIVE_DEFINITION_OF_H1}}

**Testable Predictions (H1):**

- {{Prediction 1}}
- {{Prediction 2}}
- {{Prediction 3}}
- {{Prediction 4}}

---

(repeat analogous structure for H2 ... Hn; ensure conceptual disjointness)

---

### H0: Catch-All / Unmodeled Combination

**H0: Residual / Uncaptured Factors**

{{DEFINITION_OF_H0_AS_ANY_COMBINATION_OR_STATE_NOT_CAPTURED_BY_H1_..._Hn}}

---

### Prior Allocation Over Hypotheses

<<INSTRUCTION TO MODEL:  
- Assign explicit decimal prior probabilities P(Hᵢ) to each hypothesis H1 ... Hn and H0.  
- Priors must sum exactly to 1.0 (within rounding error).  
- Provide a table with hypothesis labels, prior values, and brief rationales.  
- Justify priors using K₀’s assumptions and any widely accepted background knowledge, but do not pre-use topic-specific evidence that will appear later in the Evidence Matrix.>>

| Hypothesis | Prior P(H) | Rationale |
|-----------|:----------:|-----------|
| H1 | {{0.XXX}} | {{Brief rationale grounded in K₀ background, not using specific Eₖ}} |
| H2 | {{0.XXX}} | {{...}} |
| H3 | {{0.XXX}} | {{...}} |
| ... | ... | ... |
| Hn | {{0.XXX}} | {{...}} |
| H0 | {{0.XXX}} | {{Reason for reserving catch-all mass}} |

<<INSTRUCTION TO MODEL:  
- After filling the table, explicitly verify in prose that the priors sum to 1.0, and mention the sum.>>

---

## DELIVERABLE 3: Paradigm Inversion (At Least One Alternative Paradigm)

### Inverse Paradigm 1 (Θ₁): {{NAME_OF_ALTERNATIVE_PARADIGM_1}}

<<INSTRUCTION TO MODEL:  
- Construct at least one explicit alternative interpretive paradigm Θ₁ that is meaningfully different from K₀ (ideally “inverted” along key dimensions).  
- Optionally, include a second alternative paradigm Θ₂ if particularly relevant, but at least one is mandatory.  
- For each alternative paradigm, specify:  
  - How it differs from K₀ on core assumptions, how evidence is interpreted, and what counts as a “success” or “failure” of the proposition.  
  - A brief table contrasting K₀ and Θ₁ across 5–8 dimensions (e.g., view of uncertainty, role of institutions, emphasis on distributional vs. aggregate outcomes, etc.).  
- State, for each paradigm, which hypotheses are a priori expected to be strongest under that paradigm.>>

**Foundational Assumptions (Θ₁):**

- {{Assumption 1}}
- {{Assumption 2}}
- {{Assumption 3}}
- {{Assumption 4}}

**Key Differences from K₀:**

| Dimension | K₀ (Dominant Paradigm) | Θ₁ (Alternative Paradigm 1) |
|----------|-------------------------|-----------------------------|
| {{Dim 1}} | {{K₀ stance}} | {{Θ₁ stance}} |
| {{Dim 2}} | {{K₀ stance}} | {{Θ₁ stance}} |
| ... | ... | ... |

**Paradigm-Conditional Expectations (Θ₁):**

- Under Θ₁, hypotheses {{LIST_HYPOTHESES}} are expected to be most plausible.
- Evidence patterns such as {{EXAMPLE_PATTERNS}} would be seen as especially diagnostic.

<<OPTIONAL: Repeat analogous subsection for Θ₂ if useful.>>

---

## DELIVERABLE 4: Evidence Matrix

### Evidence Clustering Strategy

<<INSTRUCTION TO MODEL:  
- Organize evidence into 4–10 thematic clusters (A, B, C, ...) relevant for the topic (e.g., "Clinical Outcomes", "Epidemiological Trends", "Economic Impacts", "Institutional Behavior", "Historical Comparisons").  
- For each cluster, briefly explain what type of claim/evidence it addresses and why it matters for distinguishing among hypotheses.>>

#### Cluster A: {{CLUSTER_A_NAME}}

{{One short paragraph explaining what this cluster captures and why it is relevant.}}

---

### Evidence Items Within Each Cluster

<<INSTRUCTION TO MODEL:  
For **each** evidence item E-Xy (e.g., E-A1, E-A2, ...):  
1. Provide a 1–3 paragraph narrative description of the evidence, including:  
   - What the data or source shows (quantitatively if possible).  
   - Time frame, population, and key conditions or limitations.  
2. Then provide a Bayesian likelihood table specifying P(E-Xy | Hᵢ) for all hypotheses that are materially affected, plus an “Interpretation” column.  
3. Likelihood values should be decimal numbers in [0, 1], reflecting how expected this evidence is under each hypothesis.  
4. Emphasize where the evidence is strongly discriminative (e.g., very high under some hypotheses, low under others).  
5. If a hypothesis is essentially neutral with respect to the evidence, you may either omit it from the table or note that P(E|Hᵢ) ≈ baseline.>>

**E-A1: {{EVIDENCE_LABEL_OR_SHORT_DESCRIPTION}}**

{{Narrative description of E-A1: what the evidence says, numerical magnitude if available, context, and methodological caveats.}}

| Hypothesis | P(E-A1 \| H) | Interpretation |
|-----------|:------------:|----------------|
| H1 | {{0.XXX}} | {{How consistent this evidence is with H1, and why}} |
| H2 | {{0.XXX}} | {{...}} |
| H3 | {{0.XXX}} | {{...}} |
| ... | ... | ... |
| Hn | {{0.XXX}} | {{...}} |

---

(repeat similar structure for E-A2, E-A3, ..., then for Cluster B, Cluster C, etc.)

---

### Evidence Matrix Bayesian Integration

<<INSTRUCTION TO MODEL:  
- After specifying all likelihood tables for evidence items, explain in prose how the combined likelihood for each hypothesis is conceptually obtained (product or sum of log-likelihoods, independence assumptions, etc.).  
- Then provide a **single coherent Bayesian updating procedure** implemented as a Python script (below) that:  
  1. Stores priors P(Hᵢ).  
  2. Stores likelihoods P(Eₖ | Hᵢ) for each evidence item.  
  3. Computes likelihoods under negation and Bayesian confirmation metrics: likelihood ratios and weights of evidence.
  4. Computes the joint likelihood of all evidence under each hypothesis (assuming conditional independence given Hᵢ, or using a clearly stated alternative).  
  5. Multiplies priors by joint likelihoods and normalizes to get posteriors P(Hᵢ | E₁,...,Eₖ).  
  6. Computes total evidence Bayesian confirmation metrics: likelihood ratios and weights of evidence. 
  7. Prints the intermediate individual evidence Bayesian confirmation metrics.    
  8. Prints the normalized posteriors as a dictionary or table with decimal values.     
  9. Prints the total evidence Bayesian confirmation metrics.   
  
- Use this script’s output as the authoritative source for all confirmation metrics and posterior values used later in the report.  
- Ensure consistency: the confirmation metrics and posterior numbers presented in later tables must exactly match the Python output (up to rounding).>>

```


# BFIH posterior computation for {{TOPIC_OR_PROPOSITION_SHORT_TITLE}}

import numpy as np
from collections import OrderedDict

# 1. Define hypotheses and priors

hypotheses = ["H1", "H2", "H3", {{...}}, "Hn", "H0"]
priors = {
"H1": {{0.XXX}},
"H2": {{0.XXX}},
"H3": {{0.XXX}},
\# ...
"Hn": {{0.XXX}},
"H0": {{0.XXX}}
}

# 2. Define likelihoods P(E_k | H_i) for each evidence item

# Each evidence item E_k is represented as a dict mapping hypothesis -> likelihood.

evidence_items = {
"E-A1": {
"H1": {{0.XXX}},
"H2": {{0.XXX}},
"H3": {{0.XXX}},
\# ...
},
"E-A2": {
"H1": {{0.XXX}},
"H2": {{0.XXX}},
\# ...
},
\# Add all evidence items used in this analysis:
\# "E-A3": {...},
\# "E-B1": {...},
\# ...
}

# 3. Computes likelihoods under negation and Bayesian confirmation metrics
# 4. Compute unnormalized posteriors and evidence metrics
unnormalized_posteriors = {}
metrics = {h: [] for h in hypotheses} # To store LR and WoE per hypothesis per evidence

for h_i in hypotheses:
    prior_hi = priors[h_i]
    joint_likelihood = 1.0
    
    for Ek, lh_dict in evidence_items.items():
        # P(Ek | Hi)
        pk_hi = lh_dict.get(h_i, 1.0)
        
        # P(Ek | ~Hi) = SUM( P(Ek | Hj) * [P(Hj) / (1 - P(Hi))] ) for j != i
        complement_prior_hi = 1 - prior_hi
        if complement_prior_hi > 0:
            # Likelihood under negation.
            pk_not_hi = sum(
                lh_dict.get(h_j, 1.0) * (priors[h_j] / complement_prior_hi)
                for h_j in hypotheses if h_j != h_i
            )
        else:
            pk_not_hi = 0.0

        # Bayesian confirmation metrics:
        # Calculate Likelihood Ratio (LR) and Weight of Evidence (WoE)
        lr = pk_hi / pk_not_hi if pk_not_hi > 0 else float('inf')
        woe = 10 * np.log10(lr) if lr > 0 else float('-inf')
        
        metrics[h_i].append({'evidence': Ek, 'LR': lr, 'WoE': woe})
        joint_likelihood *= pk_hi

    unnormalized_posteriors[h_i] = prior_hi * joint_likelihood

# 5. Normalize to get final posteriors
normalization_constant = sum(unnormalized_posteriors.values())
posteriors = {h: unnormalized_posteriors[h] / normalization_constant for h in hypotheses}

# 6. Compute total evidence Bayesian confirmation metrics
total_likelihood_ratios = {h: (post / (1 - post)) / (priors[h] / (1 - priors[h])) for h, post in posteriors.items()}
total_weights_of_evidence = {h: 10 * np.log10(lr) for h, lr in total_likelihood_ratios.items()}

# 7. Print Bayesian Confirmation Metrics (individual evidence)
print("=" * 60)
print("BFIH BAYESIAN CONFIRMATION METRICS (individual evidence)")
print("=" * 60)
print("\nLikelihood Ratio and Weight of Evidence:\n")
for h in hypotheses:
    print(f"\n--- Hypothesis: {h} (Posterior: {posteriors[h]:.4f}) ---")
    for m in metrics[h]:
        print(f" Evidence: {m['evidence']:10} | LR: {m['LR']:8.4f} | WoE: {m['WoE']:8.4f} dB")

# 8. Print Posteriors
print("=" * 60)
print("BFIH POSTERIOR COMPUTATION")
print("=" * 60)
print("\nFinal Posterior Probabilities P(H | E₁...E₁₂):\n")

for h in sorted(posteriors.keys(), key=lambda x: posteriors[x], reverse=True):
    print(f"{h:4s}: {posteriors[h]:.6f}")

print(f"\nNormalization Check: {sum(posteriors.values()):.6f}")

# 9. Print Bayesian Confirmation Metrics (total evidence)
print("=" * 60)
print("BFIH BAYESIAN CONFIRMATION METRICS (total evidence)")
print("=" * 60)
print("\nLikelihood Ratio and Weight of Evidence:\n")

for h in sorted(posteriors.keys(), key=lambda x: posteriors[x], reverse=True):
    print(f"{h:4s}: LR = {total_likelihood_ratios[h]:.3f}, WoE = {total_weights_of_evidence[h]:.1f}")

```

<<INSTRUCTION TO MODEL:  
- Replace all {{0.XXX}} with actual numeric values consistent with the previously defined priors and likelihood tables.  
- Conceptually “run” this script and record the resulting Bayesian confirmation metrics and posterior values to at least 3 decimal places for each hypothesis.  
- Use those confirmation metrics and posteriors consistently in all subsequent tables and narrative.>>

---

## DELIVERABLE 5: Perspective-by-Perspective Analysis

<<INSTRUCTION TO MODEL:  
- Identify 3–6 distinct analytic perspectives relevant to the topic (e.g., "Clinical Efficacy", "Causal Inference", "Economic Policy", "Ethical/Normative", "Institutional/Legal", "Historical").  
- For each perspective, follow this structure:  
  - State the guiding question.  
  - Define the evidence standard and what counts as “good” or “sufficient” evidence from that perspective.  
  - Summarize the key evidence identified earlier that matters most to this perspective.  
  - Provide a clear conclusion in bold (e.g., **Conclusion:** {{short statement}}) with an explicit qualitative confidence level.  
  - Explain how the perspective maps onto the hypothesis posteriors (which hypotheses this perspective especially supports or undermines).>>

### {{PERSPECTIVE_1_NAME}} Perspective

**Question:** {{Perspective-specific question}}

**Evidence Standard:** {{Describe what counts as relevant/strong evidence here}}

**Conclusion:** **{{CLEAR_STATEMENT_OF_FINDING_FROM_THIS_PERSPECTIVE}}**

**Confidence:** {{e.g., Moderate (60–70%), High (75–85%), Very High (90%+)}}

**Key Evidence:**

- {{Evidence item and its implication}}
- {{Evidence item and its implication}}
- {{...}}

**Assessment:**

{{1–3 paragraphs analyzing how this perspective interprets the evidence, and how it aligns with or challenges particular hypotheses.}}

---

(repeat for additional perspectives)

---

## DELIVERABLE 6: Paradigm Integration & Sensitivity Analysis

### Posterior Probabilities Under Dominant Paradigm K₀

<<INSTRUCTION TO MODEL:  
- Present a table summarizing priors and posteriors for all hypotheses under K₀, using the Python-computed posteriors.  
- Provide a brief interpretation column.>>

| Hypothesis | Prior P(H) | Posterior P(H \| E) | Interpretation under K₀ |
|------|:------:|:-------:|----------------------------|
| H1 | {{0.XXX}} | {{0.XXX}} | {{Short interpretation}} |
| H2 | {{0.XXX}} | {{0.XXX}} | {{...}} |
| ... | ... | ... | ... |
| H0 | {{0.XXX}} | {{0.XXX}} | {{...}} |

### Posterior Probabilities Under Alternative Paradigm(s)

<<INSTRUCTION TO MODEL:  
- If priors (and potentially some likelihood judgments) change meaningfully under Θ₁ (and Θ₂ if used), recompute posteriors conceptually and summarize them in similar tables.  
- If the likelihood structure is the same but priors differ, explain that assumption.  
- Highlight where paradigm choice materially changes posterior rankings or magnitudes.>>

### Sensitivity Analysis: ±20% Prior Variation

<<INSTRUCTION TO MODEL:  
- Select at least 2–4 key hypotheses (especially those central to the main decision or proposition, e.g., H1, H2, Hk).  
- For each selected hypothesis under K₀ and (if relevant) under Θ₁, vary its prior by ±20% (relative), adjusting other priors proportionally or explicitly noting the re-normalization approach.  
- Recompute (conceptually) the posteriors for these scenarios (you may do this analytically or via repeating the Python process conceptually).  
- Present a table showing how the posterior for each key hypothesis changes under low/central/high prior scenarios.  
- Explicitly state whether key conclusions are robust to this prior variation.>>

Example format (adapt):

| Scenario | Hypothesis | Prior P(H) | Posterior P(H \| E) | Robustness Comment |
|-------------|:---:|:---:|:----------:|:-------:|
| K₀ central | H2 | 0.250 | 0.180 | Baseline |
| K₀ low (-20%) | H2 | 0.200 | 0.172 | Minimal change; robust |
| K₀ high (+20%) | H2 | 0.300 | 0.189 | Minimal change; robust |
| Θ₁ central | H2 | 0.400 | 0.320 | Baseline under Θ₁ |
| Θ₁ low (-20%) | H2 | 0.320 | 0.305 | Robust |
| Θ₁ high (+20%) | H2 | 0.480 | 0.335 | Robust |

<<INSTRUCTION TO MODEL:  
- Provide concrete numeric values and a clear narrative summary of robustness vs. sensitivity.>>

---

## DELIVERABLE 7: Ancestral / Historical Check

<<INSTRUCTION TO MODEL:  
- Identify relevant historical or “ancestral” baselines that provide context for interpreting current evidence (e.g., previous regimes, earlier policy eras, historical analogues in other countries, earlier technological generations).  
- Compare current patterns to these baselines to see whether the present situation represents continuity, gradual drift, or a structural break / inflection point.  
- Explicitly connect this comparison back to specific hypotheses (which ones predict continuity vs. discontinuity).>>

### Historical Baseline(s) and Comparison

**Question:** {{Formulate the historical/ancestral comparison question}}

**Historical Baselines:**

- {{Baseline 1 description and relevance}}
- {{Baseline 2 description and relevance}}
- {{...}}

**Comparison and Implications:**

{{2–5 paragraphs explaining how current evidence compares to these baselines and what that implies for each key hypothesis.}}

---

## DELIVERABLE 8: Comprehensive Integration

### Integrated Answers to the Core Questions

<<INSTRUCTION TO MODEL:  
- Synthesize all prior sections into direct answers to the main proposition and 2–5 key sub-questions.  
- For each question, state:  
  - A clear answer (with qualifiers if necessary).  
  - The main hypotheses driving that answer and their posteriors.  
  - The key evidence clusters that matter most.  
  - An explicit confidence judgment.  
- Distinguish carefully between what is strongly supported vs. what remains uncertain or conditional on future developments.>>

**Core Question 1:** {{Restate the central proposition as a question}}

**Answer:** {{Clear answer, e.g., VALIDATED / PARTIALLY VALIDATED / PARTIALLY REJECTED / REJECTED / INDETERMINATE, with nuance}}

**Supporting Hypotheses and Posteriors:**

- {{H_i}}: Posterior {{0.XXX}} – {{Short interpretation}}
- {{H_j}}: Posterior {{0.XXX}} – {{Short interpretation}}

**Key Evidence Clusters:**

- {{Cluster name}} – {{Why it matters}}
- {{Cluster name}} – {{Why it matters}}

**Confidence:** {{Confidence range with justification}}

---

(repeat for other core questions as needed)

---

## DELIVERABLE 9: Limitations, Unknowns, and Future Tests

<<INSTRUCTION TO MODEL:  
- Provide a dedicated section that frankly assesses:  
  1. **Data Limitations**: Missing data, measurement error, selection bias, and any reliance on extrapolation or models.  
  2. **Modeling Limitations**: Ways in which the hypotheses may not be fully exhaustive or where independence assumptions may be violated.  
  3. **Paradigm Dependence**: How much conclusions rely on K₀ vs. alternative paradigms Θ₁ (and Θ₂ if used).  
  4. **Temporal Uncertainty**: Future events or data that could substantially update the posteriors (what would be most diagnostic to observe next).  
  5. **Normative/Interpretive Disagreements**: Where reasonable experts might disagree, even if they accepted the same evidence.  
- For each category, give concrete examples and explain how they could alter conclusions if addressed.  
- End with a short list of “critical future observations or experiments” that would most efficiently reduce key uncertainties.>>

### Data and Measurement Limitations

{{Discuss concrete limitations and their likely direction/magnitude of impact.}}

### Modeling and Structural Limitations

{{Discuss hypothesis design limits, independence assumptions, and possible omitted mechanisms.}}

### Paradigm Dependence

{{Explain where K₀ vs. Θ₁ lead to materially different interpretations, even with the same posteriors.}}

### Temporal and Scenario Uncertainty

{{Identify what future signals or events would strengthen or weaken key hypotheses, and over what time horizon.}}

### Critical Future Tests

- {{Future test or observation 1 and what it would tell us}}
- {{Future test or observation 2}}
- {{Future test or observation 3}}

---

**End of BFIH Report Template**

<<INSTRUCTION TO MODEL:  
- When generating an actual report, remove all instructional text (including this line), fill all placeholders with concrete content, and ensure consistency across all tables, narrative, priors, likelihoods, and posteriors.>>
