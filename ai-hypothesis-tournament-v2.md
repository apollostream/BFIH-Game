# AI-Assisted Hypothesis Tournament: Game Design Specification

## 1. Overview

### 1.1 Purpose
This document specifies an AI-assisted educational game that instantiates **Game Family 1: The Hypothesis Tournament** as an interactive, LLM-driven application. The game is designed to teach:

- Intellectual honesty as a **procedure**, not a sentiment
- Bayesian confirmation theory (likelihoods, likelihood ratios, weight of evidence, posteriors)
- Paradigm-awareness and paradigm-dependence of conclusions
- The value of disciplined reasoning under uncertainty with **real economic stakes** (bets/payoffs)

### 1.2 Core Idea
An LLM-based AI system acts as:

- Paradigm definer
- Hypothesis generator
- Forcing-function executor (Ontological Scan, Ancestral Check, Paradigm Inversion, Split-Brain Workflow)
- Hypothesis set updater
- Prior assigner under each paradigm
- Evidence generator/gatherer
- Evidence pooler and clusterer (to enforce conditional independence assumptions)
- Likelihood assessor under each paradigm
- Bayesian calculator of confirmation metrics
- Narrator/explainer providing rationale at each step

Human player(s) are:

- **Epistemic bettors** who allocate monetary budgets across hypotheses over time
- Evaluated on calibration, accuracy, epistemic humility, and ability to anticipate the AI's Bayesian updates

Visualizations include:

1. **Evidence Matrix Heatmaps**
2. **Belief Space Radar/Spider Plots** under each paradigm
3. Optional time-series plots of posteriors and cumulative weight of evidence

---

## 2. Game Components

### 2.1 Roles

- **AI System (LLM + Bayesian Engine)**
  - Defines paradigms and hypotheses
  - Executes forcing functions
  - Generates and clusters evidence
  - Assesses likelihoods and computes Bayesian metrics
  - Narrates reasoning steps

- **Human Player(s)** (1–N)
  - Receive initial monetary budget (tokens/credits)
  - Place initial and updated bets on hypotheses
  - Observe evidence, AI explanations, and visualizations
  - Learn from discrepancies between their beliefs and the AI's Bayesian process

### 2.2 Key Artifacts

1. **Paradigm Set** \(\mathcal{K} = \{K_1, K_2, \dots, K_m\}\)
   - Example paradigms:
     - Secular-Individualist
     - Religious-Communitarian
     - Traditionalist-Ancestral
     - Economistic-Rationalist
     - Psychological-Constructivist
     - Systemic-Institutional

2. **Hypothesis Set** \(\mathcal{H} = \{H_0, H_1, \dots, H_n\}\)
   - Mutually exclusive, collectively exhaustive w.r.t. the scenario
   - Each hypothesis is associated with one or more paradigms

3. **Evidence Set** \(\mathcal{E} = \{E_1, E_2, \dots, E_T\}\)
   - Evidence items grouped into **conditionally independent clusters** given any hypothesis

4. **Bayesian Metrics** for each \((H_j, E_i, K_k)\):
   - \( P(E_i \mid H_j, K_k) \)
   - \( P(E_i \mid \neg H_j, K_k) \)
   - Likelihood Ratio: \( \text{LR}(H_j; E_i, K_k) = \frac{P(E_i \mid H_j, K_k)}{P(E_i \mid \neg H_j, K_k)} \)
   - Weight of Evidence: \( \text{WoE}(H_j; E_i, K_k) = \log_{10} \text{LR}(H_j; E_i, K_k) \) (or in decibans)
   - Posterior: \( P(H_j \mid E_{1:i}, K_k) \)

5. **Player Budget and Bets**
   - Each player \(p\) has a budget \(B_p\)
   - Bets are allocations \(b_{p,j}^{(t)}\) onto hypotheses \(H_j\) at betting stage \(t\)

---

## 3. Game Flow

### 3.1 High-Level Phases

1. Scenario and Paradigm Initialization
2. Hypothesis Generation and Forcing Functions
3. Prior Assignment (by AI) under each Paradigm
4. Initial Player Betting
5. Evidence Rounds (repeated):
   - Evidence generation and clustering
   - Player "raise" opportunity (bets before AI likelihood assignment)
   - AI likelihood assessment, Bayesian updating, visualization
6. Final Resolution and Payoffs
7. BFIH Analysis Report Generation
8. Post-Game Analysis and Debrief

---

## 4. Detailed Phase Design

### Phase 1: Scenario & Paradigm Initialization

**Inputs**:
- Domain selection (e.g., medical case, policy outcome, startup success/failure, historical event, etc.)
- Difficulty level (controls number of hypotheses and evidence items)

**AI Responsibilities**:
1. **Scenario Narrative**
   - Present a concise but rich description of the case
   - Make clear: time horizon, decision stakes, basic background facts

2. **Paradigm Definition**
   - Select 2–4 paradigms for this session
   - For each paradigm \(K_k\), provide:
     - Name (e.g., "Secular-Individualist (K1)") 
     - Short epistemic/ontological stance
     - Typical priors on classes of explanation (e.g., preference for material vs. spiritual causes)

**UI/UX**:
- Scenario shown in a main text panel
- Paradigm cards with short descriptions, color-coded
- Option for players to pick a "home paradigm" (for self-awareness and post-game comparison)

---

### Phase 2: Hypothesis Generation & Forcing Functions

**AI Responsibilities**:

1. **Ontological Scan (Forcing Function 1)**
   - Ensure hypotheses cover all seven domains: Biological, Economic, Cultural, Theological, Historical, Institutional, Psychological
   - If a domain yields no viable hypothesis, explicitly log the justification (presented to players)

2. **Ancestral Check (Forcing Function 2)**
   - Identify historical mechanisms for similar problems
   - Ensure at least one hypothesis reflects a historically robust mechanism or provide explicit justification for exclusion

3. **Paradigm Inversion (Forcing Function 3)**
   - For each selected paradigm \(K_k\), generate at least one strong hypothesis from its **inverse** paradigm
   - Log the inversion mapping, e.g.:
     - Secular-Individualist ↔ Religious-Communitarian
     - Modernist-Progressive ↔ Traditionalist-Ancestral

4. **Hypothesis Set Finalization**
   - Ensure \(\mathcal{H}\) is MECE
   - Tag each hypothesis with:
     - Associated paradigms
     - Domain(s) covered
     - Whether it is an ancestral/historical solution

**Player View**:
- Hypothesis list with tags (domain, paradigm, ancestral/non-ancestral)
- Short narrative for each hypothesis
- Sidebar showing forcing-functions log:
  - Which domains covered
  - What historical solution(s) were considered
  - Which hypotheses result from paradigm inversion

---

### Phase 3: AI Prior Assignment under Each Paradigm

For each paradigm \(K_k\):

1. AI assigns priors \(P(H_j \mid K_k)\) over \(\mathcal{H}\)
2. Priors must sum to 1 per paradigm
3. AI generates a **natural language justification** for each non-trivial prior

**UI/UX**:
- **Belief Space Radar Plot**:
  - Axes: Hypotheses \(H_j\)
  - For each paradigm \(K_k\), plot priors as a polygon over the axes
  - Visual comparison of how paradigms weight hypotheses differently

- **Tabular View**:
  - Rows: Hypotheses
  - Columns: Paradigm priors, narrative justification snippets

Players can inspect:
- How "their" home paradigm's priors compare to other paradigms
- Where paradigms strongly disagree or converge

---

### Phase 4: Initial Player Betting

Each human player \(p\):

1. Receives an initial budget \(B_p\) (e.g., 100 credits)
2. Allocates bets \(b_{p,j}^{(0)}\) across hypotheses, subject to:
   - \(\sum_j b_{p,j}^{(0)} \leq B_p\)
   - Minimum bet per hypothesis (optional)
3. Can optionally indicate their **subjective prior probabilities** \(\hat{P}_p(H_j)\)

**Scoring Hooks**:
- These initial priors will later be evaluated for **calibration** vs. the Bayesian posteriors and ground truth

**UI/UX**:
- Slider or numeric input per hypothesis
- Visual budget bar showing used vs. remaining credits
- Optional overlay showing AI priors under each paradigm for comparison

---

### Phase 5: Evidence Rounds (Repeated)

Each evidence round consists of:

1. **Evidence Generation & Clustering**
2. **Player Raise Phase (Pre-Likelihood)**
3. **AI Likelihood Assessment & Bayesian Update**
4. **Visualization & Explanation**

#### 5.1 Evidence Generation & Clustering

**AI Responsibilities**:

1. Generate or retrieve a set of candidate evidence items \(E_{i}\) relevant to the scenario.
2. Cluster evidence into groups \(C_1, C_2, \dots, C_r\) such that, **for design purposes**, items in different clusters are assumed conditionally independent given any \(H_j\).
3. For the current round, select one cluster \(C_t\) to reveal.
4. For each evidence item in \(C_t\), provide:
   - Short textual description
   - Type (e.g., quantitative statistic, expert testimony, historical analogy, qualitative observation)

**Player View**:
- Evidence items for current cluster displayed in a panel
- Optional indicators of type and source

#### 5.2 Player Raise Phase (Before AI Likelihoods)

Players see the raw evidence but **do not yet see AI likelihoods or posteriors**.

Each player \(p\):
- May adjust bets \(b_{p,j}^{(t)}\) across hypotheses (raise, lower, or reallocate)
- Is constrained by remaining budget and any locked bets

This phase tests:
- How well players can anticipate the direction and strength of Bayesian updates

#### 5.3 AI Likelihood Assessment & Bayesian Update

After the raise phase closes:

For each paradigm \(K_k\) and hypothesis \(H_j\):

1. AI assigns:
   - \( P(E_{i} \mid H_j, K_k) \)
   
2. Compute:
   - \( P(E_i \mid \neg H_j, K_k) = \sum_{m \neq j} P(E_i \mid H_m, K_k) \times P(H_m \mid \neg H_j, K_k) \)
   
     where the conditional probability is normalized: \( P(H_m \mid \neg H_j, K_k) = \frac{P(H_m \mid K_k)}{1 - P(H_j \mid K_k)} \) for all \(m \neq j\), distributing the remaining probability mass across all non-\(j\) hypotheses
   
   - \( \text{LR}(H_j; E_i, K_k) = \frac{P(E_i \mid H_j, K_k)}{P(E_i \mid \neg H_j, K_k)} \)
   - \( \text{WoE}(H_j; E_i, K_k) = \log_{10} \text{LR}(H_j; E_i, K_k) \) (or in decibans)

3. Aggregate across all evidence items in the cluster \(C_t\) assuming conditional independence within cluster or using an appropriate model
4. Update posteriors:
   - \( P(H_j \mid E_{1:t}, K_k) \)

**Narration**:
- AI explains, for each paradigm, how the evidence affects each hypothesis:
  - "Under \(K_1\), this evidence strongly favors \(H_3\) over \(H_1\) because …"
  - "Under \(K_2\), the same evidence is nearly neutral, because …"

#### 5.4 Visualization & Explanation

**Evidence Matrix Heatmap**:

- Axes:
  - Rows: Hypotheses \(H_j\)
  - Columns: Evidence items \(E_i\) (or clusters)
- Cell value: e.g., \(\text{WoE}(H_j; E_i, K_k)\) under a selected paradigm \(K_k\)
- Color scale:
  - Positive WoE (favoring \(H_j\)) in warm colors
  - Negative WoE (disfavoring \(H_j\)) in cool colors
  - Near-zero as neutral

**Belief Space Radar Plot**:

- Axes: Hypotheses \(H_j\)
- Polygons:
  - Prior beliefs under each paradigm
  - Updated posteriors after current evidence
- Players can toggle paradigms to see how belief shapes differ across paradigms

**Optional Time-Series Plots**:

- Posterior over rounds for each \(H_j\)
- Cumulative WoE for each \(H_j\)

**Player Learning Prompts**:

- "Which hypotheses gained the most posterior probability this round?"
- "Did the evidence move beliefs in the direction you predicted when you raised?"

---

### Phase 6: Final Resolution & Payoffs

At the end of T evidence rounds:

1. AI reveals the **ground-truth hypothesis** (pre-defined or sampled from the prior if simulated).
2. Final posteriors \(P(H_j \mid E_{1:T}, K_k)\) under each paradigm are displayed.

**Payoff Mechanism** (for each player \(p\)):

- For each hypothesis \(H_j\), let total bet be \(B_{p,j}^{\text{total}}\).
- If \(H_j\) is the true hypothesis:
  - Payout could be proportional to AI's final posterior under a designated "reference paradigm" or under a **paradigm-averaged posterior**:
    - \(\text{Payout}_{p,j} = B_{p,j}^{\text{total}} \times f\big(P(H_j \mid E_{1:T})\big)\), where f is a scoring function
- If \(H_j\) is false:
  - Bets are lost (or partially penalized depending on design)

**Alternative payoff schemes**:

- **Log scoring**: Reward ~ log of probability assigned to truth
- **Quadratic scoring**: Penalize squared error between bets as implicit probabilities and reality

**Calibration and Honesty Metrics**:

- Compute:
  - Brier score or log score for each player's subjective probability distributions
  - Overconfidence/underconfidence metrics
  - Divergence between player priors/posteriors and AI's Bayesian posteriors

---

### Phase 7: BFIH Analysis Report Generation

After each game concludes, the system automatically generates a **Bayesian Framework for Intellectual Honesty (BFIH) Analysis Report** that documents the full reasoning process according to the Treatise on Intellectual Honesty.

**Report Structure** (see Section 10 below for detailed template):

1. **Executive Summary**: Key findings and paradigm-dependence summary
2. **Scenario & Objectives**: Framing and decision stakes
3. **Background Knowledge Analysis**: Explicit statement of \(K_0\) (dominant paradigm) and alternative paradigms
4. **Forcing Functions Log**: 
   - Ontological Scan results (7 domains covered/justified)
   - Ancestral Check results (historical solutions identified/justified)
   - Paradigm Inversion mappings and results
5. **Hypothesis Set Documentation**: MECE structure with domain/paradigm tags
6. **Evidence & Likelihood Analysis**: Evidence matrix with all likelihoods and LRs per paradigm
7. **Bayesian Update Trace**: Round-by-round posteriors and WoE accumulation
8. **Paradigm-Dependence Analysis**: 
   - Robust conclusions (hold across paradigms)
   - Paradigm-dependent conclusions (vary by paradigm)
   - Incommensurable disagreements
9. **Player Performance Analytics**: Calibration scores, overconfidence, updating behavior
10. **Intellectual Honesty Assessment**: Did analysis apply forcing functions? Were blind spots surfaced?

This report serves dual purposes:
- **Pedagogical**: Players see the full epistemic chain and reasoning
- **Archival**: Report is saved in scenario library (Section 10) for reproducibility and institutional memory

---

### Phase 8: Post-Game Analysis & Debrief

The AI generates a **narrative debrief**:

1. **Paradigm Dependence**:
   - Which hypotheses remained plausible under some paradigms but not others?
   - Which conclusions were robust across paradigms?

2. **Player vs. AI Comparison**:
   - Where did players over/underweight certain hypotheses relative to AI priors/posteriors?
   - Were players more "secular" or "religious" in implicit reasoning?

3. **Intellectual Honesty Assessment**:
   - Did players adjust bets when evidence clearly contradicted prior beliefs?
   - Did they appear to cherry-pick or refuse to update?

4. **What-If Replays**:
   - Option to rerun belief updates under different paradigms
   - Option to see counterfactual: "If you had bet according to the AI's priors/posteriors, your payoff would have been X."

---

## 5. AI Architecture & Modules (Conceptual)

### 5.1 LLM Layer

- Natural language generation for:
  - Scenario, hypotheses, paradigms
  - Explanations of priors and likelihoods
  - Narration and debrief
- Orchestration of forcing functions via prompt patterns and tools

### 5.2 Bayesian Engine

- Data structures for:
  - Hypothesis sets \(\mathcal{H}\)
  - Evidence sets and clusters \(\mathcal{E}\)
  - Priors/posteriors per paradigm
- Numerical routines for:
  - Likelihood computation
  - Likelihood ratios
  - WoE
  - Posterior updating

### 5.3 Evidence Management & Clustering

- Evidence generators (domain-specific or generic)
- Clustering logic to approximate conditional independence
- Metadata tagging for each evidence item (type, source, relevance)

### 5.4 Visualization Layer

- APIs to render:
  - Heatmaps for evidence matrix
  - Radar/spider plots for belief state per paradigm
  - Time-series plots for posterior trajectories

### 5.5 Game Logic & Scoring

- State machine for phases (init → priors → bets → evidence rounds → resolution → BFIH report → debrief)
- Bet tracking and budget updates
- Payout computation and calibration scoring

---

## 6. Intellectual Honesty Features Mapped to Treatise

- **Ontological Scan**: Enforced in hypothesis generation; all 7 domains must be covered or explicitly justified as irrelevant.
- **Ancestral Check**: At least one hypothesis must reflect the primary historical solution for analogous problems.
- **Paradigm Inversion**: For each chosen paradigm, an inverse-paradigm hypothesis is generated and tracked.
- **Split-Brain Workflow**: Multiple paradigms act as "agents"; the player can see disagreements between them via visualizations.
- **Hermeneutic Spiral**: Evidence rounds iteratively refine \(K\) and \(H\); players see how understanding evolves.
- **Likelihood Ratio as Gold Standard**: All evidence impact is computed and displayed via LR and WoE, not via vague intuition.

---

## 7. Example Minimal Session (Concrete Sketch)

1. Scenario: "Why did Startup X succeed while three similar competitors failed?"
2. Paradigms: Secular-Individualist (K1), Religious-Communitarian (K2), Economistic-Rationalist (K3)
3. Hypotheses: H1 (founder grit), H2 (religious community backing), H3 (capital efficiency), H4 (regulatory arbitrage), H0 (unknown mix).
4. AI assigns priors under each K.
5. Player receives 100 credits, places initial bets, e.g., strongly on H1 and H3.
6. Round 1 evidence: founder background, early user growth, advisors.
7. Player raises bets on H1 before likelihoods.
8. AI computes LRs, updates posteriors; radar plots show K2 boosts H2 significantly.
9. After several rounds, true hypothesis (e.g., H2) revealed.
10. Player sees they consistently underweighted religious-communitarian explanations and overconfidently bet on secular grit.
11. BFIH report generated, showing full evidence matrix, forcing functions log, and paradigm-dependence analysis.
12. Report and game config saved to scenario library for reproducibility.

---

## 8. Extensibility & Variants

- **Solo vs. Multiplayer**: Cooperative or competitive modes (e.g., leaderboard of calibration scores).
- **Domain Packs**: Medical, policy, historical, startup/VC, social science, etc.
- **Difficulty Levels**: Vary number of paradigms, hypotheses, and evidence rounds.
- **Pedagogical Modes**:
  - Tutorial mode with guided explanation and slower pacing
  - Expert mode with minimal explanation and tighter time constraints

---

## 9. Perpetual Scenario Library & Topic Submission System

### 9.1 Overview

The system maintains a **perpetual library of scenario configurations** that users can:
- Select and play from
- Contribute new topics/propositions to
- Re-run with different players or player cohorts
- Track evolution and calibration over time

### 9.2 User Workflow for Topic Submission

**User submits a topic/proposition**:
- Natural language description: "Why did Company X fail despite having great products?"
- Domain category: Medical, Policy, Business, Historical, etc.
- Difficulty preference: Easy (3 hypotheses, 3 paradigms, 4 evidence clusters), Medium (5 hypotheses, 3–4 paradigms, 6–8 evidence clusters), Hard (6–7 hypotheses, 4+ paradigms, 10+ evidence clusters)

**AI-Assisted Workflow** (Automated):

1. **LLM generates initial MECE hypothesis set** under native paradigm
2. **Ontological Scan** (Forcing Function 1): Verifies 7 domains covered; iterates if gaps detected
3. **Ancestral Check** (Forcing Function 2): Identifies and includes primary historical solution
4. **Paradigm Inversion** (Forcing Function 3): Generates inverse-paradigm hypotheses
5. **Hypothesis Refinement**: AI solicits human feedback (optional) via UI prompts: "Does H2 capture the core of the religious-communitarian view? Should we revise?" → Optional human refinement loop
6. **Evidence Generation**: AI generates evidence clusters relevant to hypotheses
7. **Likelihood Assignment**: AI assigns likelihoods under each paradigm (with narrative justification)
8. **Config File Generation**: Full JSON scenario config saved (see Section 10)
9. **BFIH Analysis Report (Template)**: Generated as a markdown/PDF report documenting forcing functions, hypothesis construction, paradigm mappings

**Result**: Scenario becomes available in library for other users to play

### 9.3 Config File Specification (JSON Schema)

See Section 10 below for full JSON schema and example.

**Core Sections**:
- Metadata (scenario ID, domain, difficulty, creation date, contributors)
- Paradigms and their epistemic stances
- Hypotheses with domain/paradigm tags and narratives
- Evidence clusters with likelihoods per hypothesis/paradigm
- Priors per paradigm
- Payoff function and scoring rules
- Ground truth (if known)

### 9.4 Library Management

- **Searchable Index**: Filter by domain, difficulty, paradigm representation, date created
- **Version Control**: Scenario configs track edit history (if human feedback modifies hypothesis set)
- **Replayability**: Config + player bet history + evidence sequence is fully reproducible
- **Aggregation**: System can run meta-analysis across multiple plays of same scenario
  - E.g., "How do players' paradigm choices correlate with overconfidence on H1?"
  - Track paradigm representation trends: "Are newer scenarios better-balanced between paradigms?"

---

## 10. BFIH Analysis Report Template & JSON Config Schema

### 10.1 BFIH Analysis Report Template (Markdown)

```markdown
# BFIH Analysis Report: [Scenario Title]

**Scenario ID**: [UUID]  
**Created**: [ISO date]  
**Analysis Date**: [ISO date]  
**Contributors**: [Names/Institutions]  
**Domain**: [Medical | Policy | Historical | Business | etc.]  

---

## Executive Summary

[1–2 paragraph overview of scenario, key findings, paradigm-dependence summary]

### Key Findings

- **Robust Conclusions**: [List conclusions that hold across all paradigms]
- **Paradigm-Dependent Conclusions**: [List conclusions that vary by paradigm]
- **Incommensurable Disagreements**: [List fundamental paradigm-level disagreements that evidence cannot resolve]

---

## 1. Scenario & Objectives

### Background
[Concise narrative of the case: time horizon, stakes, key actors, basic facts]

### Research Question / Decision Frame
[What are we trying to explain or decide?]

### Target Population / Scope
[Who are the stakeholders? What constraints apply?]

---

## 2. Background Knowledge (K₀) Analysis

### Dominant Paradigm(s)
**Primary Paradigm**: [Name]  
**Epistemic Stance**: [Short description of what this paradigm treats as valid evidence, causal mechanisms, etc.]  
**Typical Priors**: [E.g., "prefers material/measurable explanations; skeptical of transcendent/spiritual claims"]

### Alternative Paradigms
**Paradigm 2**: [Name]  
**Epistemic Stance**: [Description]  
**Inverse Mapping**: [How does it invert from primary paradigm?]

[Repeat for each paradigm]

### Implicit Assumptions in K₀
[What assumptions are "baked in" to the dominant paradigm that might blind analysis?]

---

## 3. Forcing Functions Application

### 3.1 Ontological Scan (Forcing Function 1)

Verification that hypothesis set covers all seven domains:

| Domain | Hypothesis(es) | Covered? | Justification |
|--------|---|---|---|
| Biological | [H_j] | ✓/✗ | [Why or why not] |
| Economic | [H_j] | ✓/✗ | [Why or why not] |
| Cultural/Social | [H_j] | ✓/✗ | [Why or why not] |
| Theological | [H_j] | ✓/✗ | [Why or why not] |
| Historical | [H_j] | ✓/✗ | [Why or why not] |
| Institutional | [H_j] | ✓/✗ | [Why or why not] |
| Psychological | [H_j] | ✓/✗ | [Why or why not] |

**Assessment**: [All domains covered, or justified absences?]

### 3.2 Ancestral Check (Forcing Function 2)

**Historical Analogues**: [Identify how similar problems were solved historically]  
**Primary Historical Mechanism**: [What was the time-tested solution?]  
**Inclusion in Hypothesis Set**: [Is it included as H_j? Or justified as excluded?]  
**Justification**: [Why is the historical solution included/excluded in this analysis?]

### 3.3 Paradigm Inversion (Forcing Function 3)

**Paradigm Pair 1**:
- Primary: [Paradigm A]
- Inverse: [Paradigm B]
- Inverse-generated Hypothesis: [H_j from Paradigm B perspective]
- Strength of Inverse Hypothesis: [Is it genuinely distinct/strong or strawmanned?]

[Repeat for each paradigm pair]

### 3.4 Split-Brain Workflow (Forcing Function 4)

**Agents Generated**:
- Agent A (Analyst): [Paradigm A's perspective]
- Agent B (Heretic): [Paradigm B's perspective]  
- Agent C (Judge): [Synthesis]

**Key Disagreements**: [Where do agents fundamentally diverge?]

---

## 4. Hypothesis Set Documentation

### MECE Verification

**Mutual Exclusivity**: [Do any hypotheses overlap? Explain exclusivity logic]  
**Collective Exhaustiveness**: [Do hypotheses cover all plausible explanatory mechanisms?]

### Hypothesis Inventory

| ID | Hypothesis | Domain(s) | Paradigm(s) | Ancestral? | Narrative |
|---|---|---|---|---|---|
| H₀ | [Unknown/Combination] | [List] | [List] | N/A | [Short description] |
| H₁ | [Description] | [List] | [List] | Yes/No | [Narrative] |
| H₂ | [Description] | [List] | [List] | Yes/No | [Narrative] |
| ... | ... | ... | ... | ... | ... |

---

## 5. Paradigm-Specific Priors

### Paradigm K₁: [Name]

| Hypothesis | Prior P(H \| K₁) | Justification |
|---|---|---|
| H₀ | 0.10 | [Rationale] |
| H₁ | 0.45 | [Rationale] |
| H₂ | 0.30 | [Rationale] |
| ... | ... | ... |

**Paradigm Characteristics**: [How does K₁'s worldview shape these priors?]

[Repeat for each paradigm]

---

## 6. Evidence Set & Likelihood Analysis

### Evidence Clustering & Conditional Independence

**Cluster 1**: [Thematic grouping]  
- E₁: [Evidence item, type, source]  
- E₂: [Evidence item, type, source]  

**Assumption**: [Why are items in Cluster 1 conditionally independent given hypotheses?]

[Repeat for each cluster]

### Evidence Matrix (by Paradigm)

**Under Paradigm K₁**:

| Hypothesis | E₁ LR | E₂ LR | E₃ LR | ... | Net WoE |
|---|---|---|---|---|---|
| H₀ | 0.8 | 1.2 | 0.5 | ... | -0.3 |
| H₁ | 5.0 | 2.1 | 0.9 | ... | +2.1 |
| H₂ | 1.5 | 0.7 | 2.0 | ... | +0.8 |

**Legend**: LR = Likelihood Ratio; WoE = Weight of Evidence (log₁₀ scale); Positive WoE favors hypothesis; Negative WoE disfavors.

[Repeat for each paradigm]

### Evidence Interpretation (Narrative)

**E₁**: [Description and interpretation across paradigms]  
- Under K₁: Strongly favors H₁ because …  
- Under K₂: Nearly neutral because …  

[Repeat for each evidence item]

---

## 7. Bayesian Update Trace

### Round-by-Round Posterior Evolution

**Initial State**:
- K₁ Prior: [Priors listed]
- K₂ Prior: [Priors listed]

**After E₁**:
- K₁ Posterior: [Updated posteriors]
- K₂ Posterior: [Updated posteriors]
- Interpretation: [How did evidence shift beliefs?]

[Repeat for each evidence cluster]

### Final Posteriors

**Under Paradigm K₁**:
- P(H₀ \| E₁:T, K₁) = [value]
- P(H₁ \| E₁:T, K₁) = [value]
- P(H₂ \| E₁:T, K₁) = [value]

[Repeat for each paradigm]

---

## 8. Paradigm-Dependence Analysis

### Robust Conclusions

[Hypotheses/findings that converge across paradigms despite different priors and likelihoods]

**Example**: 
- Under all paradigms, hypothesis H₃ (capital efficiency) receives material posterior support
- This is robust because multiple independent lines of evidence (quantitative and qualitative) support it across epistemic frames

### Paradigm-Dependent Conclusions

[Hypotheses/findings that diverge significantly across paradigms]

| Conclusion | K₁ Assessment | K₂ Assessment | K₃ Assessment | Why? |
|---|---|---|---|---|
| [Conclusion] | [Verdict] | [Verdict] | [Verdict] | [Explanation of divergence] |

### Incommensurable Disagreements

[Fundamental paradigm-level disagreements that additional evidence cannot resolve]

**Example**:
- **Question**: Does transcendent meaning causally contribute to roots?
- **K₁ (Secular) Answer**: Transcendence is an experience that correlates with roots but is not necessary; material/social factors are primary.
- **K₂ (Religious) Answer**: Transcendence is constitutive; roots without transcendent meaning-making are fragile and spiritually hollow.
- **Verdict**: This is not an empirical disagreement resolvable by more data; it is a paradigm-level disagreement.

---

## 9. Intellectual Honesty Assessment

### Were Forcing Functions Applied?

- Ontological Scan: ✓/✗ [Assessment]
- Ancestral Check: ✓/✗ [Assessment]
- Paradigm Inversion: ✓/✗ [Assessment]
- Split-Brain Workflow: ✓/✗ [Assessment]

### Were Blind Spots Surfaced?

[Did analysis reveal assumptions or biases in K₀ that initially went unnoticed?]

### Consistency Standards

[Were the same evidence-evaluation criteria applied to favored vs. disfavored hypotheses? Any ad-hoc exceptions?]

### Implications for Decision-Making

[For stakeholders with different paradigms, what do these findings mean? Who should prioritize which hypotheses?]

---

## 10. Player Performance Analytics (if Game Context)

### Calibration Assessment

[How did players' belief distributions compare to final posteriors?]

### Overconfidence/Underconfidence Metrics

[Did players express excessive confidence or excessive uncertainty?]

### Paradigm Bias

[Did players' native paradigm show through their likelihood assignments or bets?]

### Belief Updating Behavior

[Did players update appropriately when evidence contradicted priors?]

---

## 11. Conclusion & Synthesis

[Summary of key findings, paradigm-dependence conclusions, and intellectual honesty assessment]

---

## 12. References & Appendices

[Citations, detailed evidence source materials, etc.]
```

---

### 10.2 JSON Configuration Schema (Full Specification)

```json
{
  "schema_version": "1.0",
  "scenario_metadata": {
    "scenario_id": "uuid_string",
    "title": "string",
    "description": "string",
    "domain": "enum: [medical, policy, historical, business, scientific, social_science, etc.]",
    "difficulty_level": "enum: [easy, medium, hard]",
    "created_date": "ISO-8601",
    "last_modified_date": "ISO-8601",
    "contributors": ["string: name/institution"],
    "ground_truth_hypothesis_id": "string or null (if unknown)"
  },
  
  "scenario_narrative": {
    "title": "string",
    "background": "string: rich narrative setup",
    "stakes": "string: what is at stake?",
    "time_horizon": "string: temporal scope",
    "key_actors": "string: who are the key players?",
    "research_question": "string: what are we trying to explain?"
  },
  
  "paradigms": [
    {
      "paradigm_id": "K1",
      "name": "string",
      "description": "string: epistemic/ontological stance",
      "inverse_paradigm_id": "K2 or null",
      "characteristics": {
        "prefers_evidence_types": ["string"],
        "skeptical_of": ["string"],
        "causal_preference": "string",
        "materiality": "string: emphasis on material vs. spiritual, etc."
      }
    }
  ],
  
  "hypotheses": [
    {
      "hypothesis_id": "H0",
      "name": "string",
      "narrative": "string: full description",
      "domains": ["Biological", "Economic", "Cultural", "Theological", "Historical", "Institutional", "Psychological"],
      "associated_paradigms": ["K1", "K2"],
      "is_ancestral_solution": boolean,
      "is_catch_all": boolean
    }
  ],
  
  "forcing_functions_log": {
    "ontological_scan": {
      "domains_covered": {
        "Biological": { "hypothesis_id": "H_j", "justification": "string" },
        "Economic": { "hypothesis_id": "H_j", "justification": "string" },
        "Cultural": { "hypothesis_id": "H_j", "justification": "string" },
        "Theological": { "hypothesis_id": null, "justification": "string: why excluded" },
        "Historical": { "hypothesis_id": "H_j", "justification": "string" },
        "Institutional": { "hypothesis_id": "H_j", "justification": "string" },
        "Psychological": { "hypothesis_id": "H_j", "justification": "string" }
      }
    },
    "ancestral_check": {
      "historical_analogue": "string: what historical solution exists?",
      "primary_mechanism": "string: description",
      "included_in_hypotheses": boolean,
      "hypothesis_id": "H_j or null",
      "justification": "string: if excluded, why?"
    },
    "paradigm_inversion": [
      {
        "paradigm_pair_id": "K1_K2",
        "primary_paradigm": "K1",
        "inverse_paradigm": "K2",
        "generated_hypothesis_id": "H_j",
        "quality_assessment": "string: is it genuinely strong or strawmanned?"
      }
    ]
  },
  
  "priors_by_paradigm": [
    {
      "paradigm_id": "K1",
      "priors": [
        {
          "hypothesis_id": "H0",
          "prior_probability": 0.10,
          "justification": "string: why this prior under K1?"
        },
        {
          "hypothesis_id": "H1",
          "prior_probability": 0.45,
          "justification": "string"
        }
      ]
    }
  ],
  
  "evidence": [
    {
      "evidence_cluster_id": "C1",
      "cluster_name": "string",
      "conditional_independence_assumption": "string: why conditionally independent?",
      "evidence_items": [
        {
          "evidence_id": "E1",
          "description": "string",
          "type": "enum: [quantitative, qualitative, expert_testimony, historical_analogy, etc.]",
          "source": "string",
          "likelihoods_by_paradigm": [
            {
              "paradigm_id": "K1",
              "likelihoods": [
                {
                  "hypothesis_id": "H0",
                  "P_E_given_H": 0.15,
                  "P_E_given_not_H": 0.50,
                  "likelihood_ratio": 0.30,
                  "weight_of_evidence_decibans": -5.2,
                  "explanation": "string: why this likelihood under K1?"
                },
                {
                  "hypothesis_id": "H1",
                  "P_E_given_H": 0.80,
                  "P_E_given_not_H": 0.25,
                  "likelihood_ratio": 3.20,
                  "weight_of_evidence_decibans": 5.1,
                  "explanation": "string"
                }
              ]
            }
          ]
        }
      ]
    }
  ],
  
  "game_settings": {
    "initial_budget_per_player": 100,
    "minimum_bet": 1,
    "payoff_function": "enum: [log_score, quadratic_score, proportional_posterior]",
    "scoring_description": "string: how are payoffs calculated?"
  },
  
  "session_history": [
    {
      "session_id": "uuid",
      "played_date": "ISO-8601",
      "num_players": integer,
      "player_paradigm_choices": ["K1", "K2"],
      "player_calibration_scores": [0.75, 0.82],
      "ground_truth_revealed": "H2",
      "final_posteriors_under_each_paradigm": {
        "K1": [{ "hypothesis_id": "H0", "posterior": 0.12 }],
        "K2": [{ "hypothesis_id": "H0", "posterior": 0.25 }]
      },
      "player_payoffs": [45, 68]
    }
  ],
  
  "metadata_tags": {
    "keywords": ["string"],
    "paradigm_representation": "balanced | heavy_secular | heavy_religious | etc.",
    "evidence_diversity": "narrow | moderate | broad",
    "replayed_count": integer,
    "average_player_calibration": float
  }
}
```

---

### 10.3 Example Minimal Scenario Config (JSON)

```json
{
  "schema_version": "1.0",
  "scenario_metadata": {
    "scenario_id": "s_001_startup_success",
    "title": "Why Did Startup X Succeed While Competitors Failed?",
    "description": "Analysis of startup competitive advantage in a high-growth market",
    "domain": "business",
    "difficulty_level": "medium",
    "created_date": "2026-01-06",
    "contributors": ["System (generated)", "Michael L. Thompson (reviewed)"],
    "ground_truth_hypothesis_id": "H2"
  },
  
  "scenario_narrative": {
    "title": "Why Did Startup X Succeed While Competitors Failed?",
    "background": "In 2015, three startups (X, Y, Z) emerged in the educational SaaS space with similar product positioning. By 2025, Startup X achieved unicorn status (>$1B valuation), while Y and Z folded. All three had strong founders, venture capital backing, and market timing.",
    "stakes": "Understanding the mechanism of startup success vs. failure has implications for: investor allocation strategy, founder decision-making, and market predictions.",
    "time_horizon": "10-year retrospective (2015–2025)",
    "key_actors": "Founders (grit/vision), investors (capital + network), employees (culture/execution), market conditions (timing)",
    "research_question": "What is the primary causal mechanism differentiating X's success from Y/Z's failure?"
  },
  
  "paradigms": [
    {
      "paradigm_id": "K1",
      "name": "Secular-Individualist",
      "description": "Success driven by founder grit, deliberate strategy, and competitive efficiency. Measurable behaviors and incentives primary.",
      "inverse_paradigm_id": "K2",
      "characteristics": {
        "prefers_evidence_types": ["quantitative metrics", "behavioral data", "market efficiency"],
        "skeptical_of": ["spiritual/transcendent factors", "community-based networks"],
        "causal_preference": "individual agency and optimization"
      }
    },
    {
      "paradigm_id": "K2",
      "name": "Religious-Communitarian",
      "description": "Success driven by founder's faith/values alignment, trusted community networks, and institutional backing (e.g., faith-based investors/boards).",
      "inverse_paradigm_id": "K1",
      "characteristics": {
        "prefers_evidence_types": ["network analysis", "founder background/values", "institutional affiliations"],
        "skeptical_of": ["pure market efficiency", "individual-level optimization"],
        "causal_preference": "community, meaning-making, transcendent values"
      }
    },
    {
      "paradigm_id": "K3",
      "name": "Economistic-Rationalist",
      "description": "Success driven by capital efficiency (lower burn rate), unit economics (CAC/LTV), and regulatory arbitrage.",
      "inverse_paradigm_id": null,
      "characteristics": {
        "prefers_evidence_types": ["financial metrics", "growth rates", "cost analysis"],
        "skeptical_of": ["cultural/soft factors"],
        "causal_preference": "resource allocation and incentive alignment"
      }
    }
  ],
  
  "hypotheses": [
    {
      "hypothesis_id": "H0",
      "name": "Unknown/Combination",
      "narrative": "Multiple factors combined in ways not yet identified",
      "domains": [],
      "associated_paradigms": ["K1", "K2", "K3"],
      "is_ancestral_solution": false,
      "is_catch_all": true
    },
    {
      "hypothesis_id": "H1",
      "name": "Founder Grit & Strategic Vision",
      "narrative": "Founder of X possessed exceptional resilience, adaptability, and market foresight. Outexecuted competitors through sheer determination and tactical flexibility.",
      "domains": ["Psychological"],
      "associated_paradigms": ["K1"],
      "is_ancestral_solution": false,
      "is_catch_all": false
    },
    {
      "hypothesis_id": "H2",
      "name": "Faith-Based Community Network & Institutional Backing",
      "narrative": "Founder X's faith community (specific religious affiliation) provided: trusted advisors, early customers, institutional investors aligned on values. This dense, trust-based network accelerated growth and reduced execution risk.",
      "domains": ["Theological", "Cultural"],
      "associated_paradigms": ["K2"],
      "is_ancestral_solution": true,
      "is_catch_all": false
    },
    {
      "hypothesis_id": "H3",
      "name": "Capital Efficiency & Unit Economics",
      "narrative": "Startup X achieved superior CAC/LTV ratios through disciplined spending and retention focus. Lower burn rate meant longer runway and more strategic optionality than competitors.",
      "domains": ["Economic"],
      "associated_paradigms": ["K3"],
      "is_ancestral_solution": false,
      "is_catch_all": false
    },
    {
      "hypothesis_id": "H4",
      "name": "Regulatory Arbitrage & Market Timing",
      "narrative": "Policy shift in 2016 (education spending) created regulatory tail wind that Startup X capitalized on faster than competitors due to agility.",
      "domains": ["Institutional", "Economic"],
      "associated_paradigms": ["K1", "K3"],
      "is_ancestral_solution": false,
      "is_catch_all": false
    }
  ],
  
  "forcing_functions_log": {
    "ontological_scan": {
      "domains_covered": {
        "Biological": { "hypothesis_id": null, "justification": "No genetic or neurological factors relevant to business success in this context." },
        "Economic": { "hypothesis_id": "H3", "justification": "Capital efficiency directly affects startup survival." },
        "Cultural": { "hypothesis_id": "H2", "justification": "Community networks and trust are cultural mechanisms." },
        "Theological": { "hypothesis_id": "H2", "justification": "Faith-based backing is explicitly theological domain." },
        "Historical": { "hypothesis_id": "H2", "justification": "Religious networks have historically been primary scaling mechanism (ancestral)." },
        "Institutional": { "hypothesis_id": "H4", "justification": "Policy environment shapes startup incentives." },
        "Psychological": { "hypothesis_id": "H1", "justification": "Founder psychology and grit are core to H1." }
      }
    },
    "ancestral_check": {
      "historical_analogue": "Medieval guild systems and early modern merchant networks relied heavily on faith-based communities (religious orders, family networks rooted in faith) for trust and knowledge transfer.",
      "primary_mechanism": "Religious/faith-based institutional networks as primary trust and scaling mechanism.",
      "included_in_hypotheses": true,
      "hypothesis_id": "H2",
      "justification": "H2 directly represents this ancestral mechanism in modern context (faith-based investor networks and customer communities)."
    },
    "paradigm_inversion": [
      {
        "paradigm_pair_id": "K1_K2",
        "primary_paradigm": "K1",
        "inverse_paradigm": "K2",
        "generated_hypothesis_id": "H2",
        "quality_assessment": "Genuinely strong. Under K2, faith-based networks are not marginal but central—they provide trust, shared values, and intergenerational institutional support that secular mechanisms cannot replicate."
      }
    ]
  },
  
  "priors_by_paradigm": [
    {
      "paradigm_id": "K1",
      "priors": [
        { "hypothesis_id": "H0", "prior_probability": 0.10, "justification": "Catch-all for unknown factors; kept low." },
        { "hypothesis_id": "H1", "prior_probability": 0.50, "justification": "Under K1, founder grit and vision are primary success drivers. High prior." },
        { "hypothesis_id": "H2", "prior_probability": 0.10, "justification": "Faith networks dismissed as soft/secondary under secular paradigm." },
        { "hypothesis_id": "H3", "prior_probability": 0.20, "justification": "Capital efficiency matters but is secondary to execution (grit)." },
        { "hypothesis_id": "H4", "prior_probability": 0.10, "justification": "Market timing is luck, not primary driver." }
      ]
    },
    {
      "paradigm_id": "K2",
      "priors": [
        { "hypothesis_id": "H0", "prior_probability": 0.05, "justification": "Catch-all minimized; K2 emphasizes explicit causal mechanisms." },
        { "hypothesis_id": "H1", "prior_probability": 0.20, "justification": "Individual grit is secondary to community/institutional backing." },
        { "hypothesis_id": "H2", "prior_probability": 0.55, "justification": "Faith-based networks are primary scaling and trust mechanism; highest prior." },
        { "hypothesis_id": "H3", "prior_probability": 0.10, "justification": "Capital efficiency is material detail, not core driver." },
        { "hypothesis_id": "H4", "prior_probability": 0.10, "justification": "Regulatory shifts affect all players; not differentiating." }
      ]
    },
    {
      "paradigm_id": "K3",
      "priors": [
        { "hypothesis_id": "H0", "prior_probability": 0.15, "justification": "Catch-all for unmeasurable factors." },
        { "hypothesis_id": "H1", "prior_probability": 0.10, "justification": "Grit is not quantifiable; excluded." },
        { "hypothesis_id": "H2", "prior_probability": 0.05, "justification": "Faith networks are not directly measurable in financial terms." },
        { "hypothesis_id": "H3", "prior_probability": 0.60, "justification": "Unit economics are the primary predictor of startup survival; highest prior." },
        { "hypothesis_id": "H4", "prior_probability": 0.10, "justification": "Regulatory arbitrage is secondary to unit economics." }
      ]
    }
  ],
  
  "evidence": [
    {
      "evidence_cluster_id": "C1",
      "cluster_name": "Founder Background & Personal Factors",
      "conditional_independence_assumption": "Items in this cluster (founder background, family history, educational trajectory) are conditionally independent given any hypothesis about causal mechanisms.",
      "evidence_items": [
        {
          "evidence_id": "E1",
          "description": "Founder of X has stated publicly that faith (specific religious affiliation) was central to decision to start company and persevere through early setbacks.",
          "type": "qualitative",
          "source": "Founder interview, press coverage",
          "likelihoods_by_paradigm": [
            {
              "paradigm_id": "K1",
              "likelihoods": [
                { "hypothesis_id": "H1", "P_E_given_H": 0.50, "P_E_given_not_H": 0.30, "likelihood_ratio": 1.67, "weight_of_evidence_decibans": 2.2, "explanation": "Under K1, founder's stated faith could be post-hoc rationalization of grit-driven success; weak signal." },
                { "hypothesis_id": "H2", "P_E_given_H": 0.90, "P_E_given_not_H": 0.20, "likelihood_ratio": 4.50, "weight_of_evidence_decibans": 6.5, "explanation": "Strong signal for H2 under any paradigm; explicit evidence of faith influence." }
              ]
            },
            {
              "paradigm_id": "K2",
              "likelihoods": [
                { "hypothesis_id": "H1", "P_E_given_H": 0.40, "P_E_given_not_H": 0.50, "likelihood_ratio": 0.80, "weight_of_evidence_decibans": -0.97, "explanation": "Under K2, faith is not reducible to individual grit; modest disfavor for H1." },
                { "hypothesis_id": "H2", "P_E_given_H": 0.95, "P_E_given_not_H": 0.20, "likelihood_ratio": 4.75, "weight_of_evidence_decibans": 6.8, "explanation": "Very strong signal for H2 under K2; this is the central causal mechanism." }
              ]
            },
            {
              "paradigm_id": "K3",
              "likelihoods": [
                { "hypothesis_id": "H3", "P_E_given_H": 0.30, "P_E_given_not_H": 0.35, "likelihood_ratio": 0.86, "weight_of_evidence_decibans": -0.65, "explanation": "Under K3, founder's faith statement is not financially material; weak neutral signal." }
              ]
            }
          ]
        }
      ]
    }
  ],
  
  "game_settings": {
    "initial_budget_per_player": 100,
    "minimum_bet": 1,
    "payoff_function": "proportional_posterior",
    "scoring_description": "Players earn payout proportional to final posterior assigned to ground-truth hypothesis. E.g., if player bets 50 credits on H2 (truth) and final posterior P(H2|Evidence, K1)=0.70, payout = 50 * 0.70 = 35 credits."
  }
}
```

---

## 11. System Summary

This specification now includes:

1. **Corrected Bayesian calculation** (Section 5.3): P(E_i | ¬H_j, K_k) computed as the properly normalized sum over alternative hypotheses
2. **BFIH Analysis Report template** (Section 10.1): Full markdown structure with all forcing functions, paradigm analysis, and intellectual honesty assessment
3. **JSON Configuration Schema** (Section 10.2): Complete spec for scenario storage, reproducibility, and scenario library management
4. **Perpetual scenario library mechanism** (Section 9): Users can submit topics; system runs full BFIH analysis; configs saved for replayability and meta-analysis

This creates a self-reinforcing system:
- Each game generates a BFIH report (documentation)
- Each report is backed by a JSON config (reproducibility)
- Configs accumulate in a searchable library (institutional memory)
- Users can generate new scenarios via LLM-assisted BFIH analysis (perpetual growth)
- Repeated plays of scenarios enable calibration meta-analysis across cohorts

The system is now fully specified for implementation.

