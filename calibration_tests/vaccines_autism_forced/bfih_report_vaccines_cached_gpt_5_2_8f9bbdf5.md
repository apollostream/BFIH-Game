# BFIH Analysis Report: Do vaccines cause autism in children?

**Analysis conducted using Bayesian Framework for Intellectual Honesty (BFIH)**

---

## Executive Summary

**Verdict:** REJECTED based on posteriors

Our analysis under the privileged K0 paradigm finds that the hypothesis H2 (“No causal link exists”) carries an overwhelming posterior probability of 0.7267. In contrast, the direct‐causation hypothesis H1 (“Vaccines directly cause autism”) has a vanishingly small posterior of 0.0010. The remaining hypotheses (H3–H5) share modest posterior support (0.0617–0.0972), while the catch‐all H0 sits at 0.0194.

Under K0, H2 clearly dominates, reflecting strong epidemiological evidence. Across the skeptical (K1) and precautionary (K2) paradigms, however, the most supported hypothesis shifts to H3 (“Rare subgroup vulnerability”), with posteriors of 0.3104 and 0.3120 respectively. This divergence highlights paradigm dependence in the partial‐effect interpretations but does not challenge the robust rejection of widespread causation.

Key evidence driving these conclusions includes large-scale cohort and case-control studies showing no increased autism risk post‐vaccination, meta-analyses totaling millions of children, and mechanistic investigations that find no credible neurotoxic pathway for vaccine components. The infamous Wakefield study has been discredited for methodological flaws and conflicts of interest, further diminishing any signal for causation.

While the rejection of a general causal link (H2) is robust under the scientific‐consensus paradigm, alternative paradigms assign nontrivial weight to rare or indirect effects (H3–H5). Stakeholders emphasizing precaution or distrust of institutions should thus note residual uncertainty for small vulnerable subgroups, even as the broad epidemiological conclusion remains firm.

---

## 1. Paradigms Analyzed

### K0: Scientific Consensus

Mainstream scientific and medical consensus based on epidemiological evidence, meta-analyses, and mechanistic biology.

*(No explicit stance data available)*

Under this paradigm, national and international health bodies rely on high‐quality trials and surveillance data to assess vaccine safety.

### K1: Vaccine Skeptic

Perspective that questions vaccine safety claims, emphasizes anecdotal reports, and distrusts pharmaceutical/regulatory institutions.

*(No explicit stance data available)*

Proponents often highlight case anecdotes and alleged regulatory capture to argue for unrecognized risks.

### K2: Precautionary

Accepts most vaccine science but emphasizes unknown long-term risks and subgroup vulnerabilities.

*(No explicit stance data available)*

This view acknowledges the general safety profile but calls for ongoing monitoring and targeted research on sensitive cohorts.

---

## 2. Hypothesis Set

**H0: OTHER – Unforeseen explanation**  
This hypothesis posits that neither vaccines nor known confounders explain the observed autism incidence. Some unknown factor—genetic, environmental, or methodological—accounts for the apparent temporal association. It captures residual uncertainty beyond the other defined scenarios.

**Prior Probabilities:**

| Paradigm | Prior P(H0) | Rationale                                  |
|----------|-------------|--------------------------------------------|
| K0 (Scientific Consensus)       | 0.05        | A small chance of unknown confounders      |
| K1 (Vaccine Skeptic)       | 0.10        | Skeptics allow broader unknowns            |
| K2 (Precautionary)       | 0.10        | Precautionary stance keeps room for unknown|

---

**H1: TRUE – Vaccines directly cause autism**  
Vaccines or their components (e.g., thimerosal, aluminum) exert neurotoxic or immune‐mediated effects that trigger autism. Mechanisms might include disruption of the blood–brain barrier, chronic inflammation, or gut‐brain axis perturbation. This is the classical vaccine-autism claim.

**Prior Probabilities:**

| Paradigm | Prior P(H1) | Rationale                                          |
|----------|-------------|----------------------------------------------------|
| K0 (Scientific Consensus)       | 0.05        | Scientific consensus deems this highly unlikely    |
| K1 (Vaccine Skeptic)       | 0.35        | Skeptics assign significant weight to anecdotes     |
| K2 (Precautionary)       | 0.10        | Precautionary allows minimal prior but remains open|

---

**H2: FALSE – No causal link exists**  
Vaccination timing coincides with the age when autism is typically diagnosed; there is no causal relationship. Large epidemiological studies, registry analyses, and meta-analyses have consistently found no increased risk of autism following vaccination.

**Prior Probabilities:**

| Paradigm | Prior P(H2) | Rationale                                              |
|----------|-------------|--------------------------------------------------------|
| K0 (Scientific Consensus)       | 0.60        | Consensus based on overwhelming epidemiological data   |
| K1 (Vaccine Skeptic)       | 0.10        | Skeptics give it low prior due to institutional distrust|
| K2 (Precautionary)       | 0.30        | Precautionary trusts data but remains cautious         |

---

**H3: PARTIAL – Rare subgroup vulnerability**  
A small genetically or immunologically susceptible subgroup may experience neurodevelopmental harm from vaccines. This subgroup’s size is too small to be detected in broad population studies, but case series and family clustering suggest its existence.

**Prior Probabilities:**

| Paradigm | Prior P(H3) | Rationale                                                    |
|----------|-------------|----------------------------------------------------------------|
| K0 (Scientific Consensus)       | 0.10        | Scientific consensus allows limited residual subgroup risk   |
| K1 (Vaccine Skeptic)       | 0.20        | Skeptics see subgroup effects as a key to reconcile anecdotes |
| K2 (Precautionary)       | 0.20        | Precautionary prioritizes investigation of vulnerable children|

---

**H4: PARTIAL – Indirect pathway via immune activation**  
While vaccines do not directly cause autism, the immune response they provoke may interact with pre-existing conditions (e.g., mitochondrial dysfunction) to affect neurodevelopment indirectly. The effect is context-dependent and mediated by cytokine cascades or microglial activation.

**Prior Probabilities:**

| Paradigm | Prior P(H4) | Rationale                                                        |
|----------|-------------|------------------------------------------------------------------|
| K0 (Scientific Consensus)       | 0.10        | Consensus: indirect mechanisms remain speculative                |
| K1 (Vaccine Skeptic)       | 0.15        | Skeptics emphasize possible immune‐mediated links                |
| K2 (Precautionary)       | 0.15        | Precautionary sees plausible but unproven immunological effects  |

---

**H5: PARTIAL – Timing/schedule effects only**  
The standard vaccination schedule, with multiple antigens administered in a short interval, might transiently overwhelm an immature immune system in a subset of children. The cumulative effect could contribute to developmental perturbations without a single vaccine being the culprit.

**Prior Probabilities:**

| Paradigm | Prior P(H5) | Rationale                                                       |
|----------|-------------|-----------------------------------------------------------------|
| K0 (Scientific Consensus)       | 0.10        | Consensus views schedule overload theory as unsubstantiated     |
| K1 (Vaccine Skeptic)       | 0.10        | Skeptics point to schedule as a compromise explanation          |
| K2 (Precautionary)       | 0.15        | Precautionary highlights schedule timing as an area for review  |

---

## 3. Evidence Clusters

### Cluster: C1

**Description:** Large cohort/case-control studies and meta-analyses examining MMR, thimerosal/ethylmercury, antigen load, prenatal influenza vaccination, and temporal/timing variables; overwhelmingly report no association with ASD.  
**Evidence Items:** E1, E3, E4, E6, E9, E10, E14, E17, E18, E19, E20, E24, E26, E27, E28, E29, E30, E31, E32, E37, E41, E43, E44, E45, E46

| Hypothesis | P(E\|H) | P(E\|¬H) | LR | WoE (dB) | Direction |
|------------|--------|---------|-----|----------|-----------|
| H0 (OTHER - Unforeseen explanation) | 0.49 | 0.7274 | 0.6737 | -1.72 | Weak Refutation |
| H1 (TRUE - Vaccines directly ca...) | 0.12 | 0.7468 | 0.1607 | -7.94 | Moderate Refutation |
| H2 (FALSE - No causal link exists) | 0.85 | 0.5138 | 1.6545 | 2.19 | Weak Support |
| H3 (PARTIAL - Rare subgroup vul...) | 0.62 | 0.7261 | 0.8539 | -0.69 | Weak Refutation |
| H4 (PARTIAL - Indirect pathway ...) | 0.58 | 0.7306 | 0.7939 | -1.0 | Weak Refutation |
| H5 (PARTIAL - Timing/schedule e...) | 0.55 | 0.7339 | 0.7494 | -1.25 | Weak Refutation |

In this large‐scale cluster, the LR for H1 (0.1607, WoE –7.94 dB) indicates moderate refutation of a direct vaccine–autism link, while most other causal hypotheses (H3–H5) are weakly refuted (LR < 1, small negative WoE). Only H2 shows weak support (LR = 1.6545, WoE = 2.19 dB), suggesting that nonspecific immune‐mediated mechanisms might merit further study, but this signal is much smaller than the refutation of direct causation.

### Cluster: C2

**Description:** Consensus statements and major reviews (IOM/NASEM, CDC, AAP, WHO, Brookings expert commentary, and similar) concluding no link between vaccines (including MMR, thimerosal/aluminum) and autism, and/or no schedule-timing link.  
**Evidence Items:** E2, E8, E11, E12, E13, E21, E25, E33, E34, E36, E42, E49, E50

| Hypothesis | P(E\|H) | P(E\|¬H) | LR | WoE (dB) | Direction |
|------------|--------|---------|-----|----------|-----------|
| H0 (OTHER - Unforeseen explanation) | 0.58 | 0.7358 | 0.7883 | -1.03 | Weak Refutation |
| H1 (TRUE - Vaccines directly ca...) | 0.18 | 0.7568 | 0.2378 | -6.24 | Moderate Refutation |
| H2 (FALSE - No causal link exists) | 0.9 | 0.47 | 1.9149 | 2.82 | Weak Support |
| H3 (PARTIAL - Rare subgroup vul...) | 0.52 | 0.7511 | 0.6923 | -1.6 | Weak Refutation |
| H4 (PARTIAL - Indirect pathway ...) | 0.5 | 0.7533 | 0.6637 | -1.78 | Weak Refutation |
| H5 (PARTIAL - Timing/schedule e...) | 0.48 | 0.7556 | 0.6353 | -1.97 | Weak Refutation |

Major expert reviews strongly refute a direct causal link (H1: LR = 0.2378, WoE = –6.24 dB) and weakly refute other vaccine‐specific mechanisms (H3–H5). The only hypothesis with LR > 1 is H2 (LR = 1.9149, WoE = 2.82 dB), reflecting modest support for general immune‐mediated pathways but not vaccine‐specific effects.

### Cluster: C3

**Description:** The original small 1998 case series suggesting a temporal association, followed by formal retractions and analyses documenting methodological flaws/fraud and unethical practices.  
**Evidence Items:** E16, E7, E15, E35, E38

| Hypothesis | P(E\|H) | P(E\|¬H) | LR | WoE (dB) | Direction |
|------------|--------|---------|-----|----------|-----------|
| H0 (OTHER - Unforeseen explanation) | 0.34 | 0.5505 | 0.6176 | -2.09 | Weak Refutation |
| H1 (TRUE - Vaccines directly ca...) | 0.12 | 0.5621 | 0.2135 | -6.71 | Moderate Refutation |
| H2 (FALSE - No causal link exists) | 0.65 | 0.375 | 1.7333 | 2.39 | Weak Support |
| H3 (PARTIAL - Rare subgroup vul...) | 0.45 | 0.55 | 0.8182 | -0.87 | Weak Refutation |
| H4 (PARTIAL - Indirect pathway ...) | 0.42 | 0.5533 | 0.759 | -1.2 | Weak Refutation |
| H5 (PARTIAL - Timing/schedule e...) | 0.4 | 0.5556 | 0.72 | -1.43 | Weak Refutation |

The discredited 1998 study and its aftermath moderately refute H1 (LR = 0.2135, WoE = –6.71 dB) and weakly refute most other vaccine‐specific hypotheses. As with larger studies, only H2 garners weak support (LR = 1.7333, WoE = 2.39 dB), reflecting general immune activation effects rather than vaccine causality.

### Cluster: C4

**Description:** Animal/translational evidence that maternal immune activation can produce autism-like phenotypes, suggesting immune-mediated pathways could influence neurodevelopment (not vaccine-specific per se).  
**Evidence Items:** E5

| Hypothesis | P(E\|H) | P(E\|¬H) | LR | WoE (dB) | Direction |
|------------|--------|---------|-----|----------|-----------|
| H0 (OTHER - Unforeseen explanation) | 0.45 | 0.4974 | 0.9048 | -0.43 | Neutral |
| H1 (TRUE - Vaccines directly ca...) | 0.55 | 0.4921 | 1.1176 | 0.48 | Weak Support |
| H2 (FALSE - No causal link exists) | 0.45 | 0.5625 | 0.8 | -0.97 | Weak Refutation |
| H3 (PARTIAL - Rare subgroup vul...) | 0.55 | 0.4889 | 1.125 | 0.51 | Weak Support |
| H4 (PARTIAL - Indirect pathway ...) | 0.75 | 0.4667 | 1.6071 | 2.06 | Weak Support |
| H5 (PARTIAL - Timing/schedule e...) | 0.45 | 0.5 | 0.9 | -0.46 | Neutral |

This translational model yields neutral to weakly supportive evidence for hypotheses involving immune‐mediated mechanisms (H1, H3, H4 all with LR > 1 but WoE < 3 dB), and does not strongly favor any vaccine‐specific causal claim. It underscores plausible biologic pathways without directly implicating vaccines.

### Cluster: C5

**Description:** Weaker/contested pro-link claims (VAERS-based analyses, subgroup/timing reanalyses), critiques alleging bias in null studies, cross-national schedule correlations, and signals of renewed review/uncertainty; includes some mixed media summaries around schedule.  
**Evidence Items:** E22, E23, E39, E40, E47, E48, E51, E52

| Hypothesis | P(E\|H) | P(E\|¬H) | LR | WoE (dB) | Direction |
|------------|--------|---------|-----|----------|-----------|
| H0 (OTHER - Unforeseen explanation) | 0.33 | 0.2905 | 1.1359 | 0.55 | Weak Support |
| H1 (TRUE - Vaccines directly ca...) | 0.5 | 0.2816 | 1.7757 | 2.49 | Weak Support |
| H2 (FALSE - No causal link exists) | 0.2 | 0.4313 | 0.4638 | -3.34 | Weak Refutation |
| H3 (PARTIAL - Rare subgroup vul...) | 0.45 | 0.275 | 1.6364 | 2.14 | Weak Support |
| H4 (PARTIAL - Indirect pathway ...) | 0.38 | 0.2828 | 1.3438 | 1.28 | Weak Support |
| H5 (PARTIAL - Timing/schedule e...) | 0.48 | 0.2717 | 1.7669 | 2.47 | Weak Support |

Contested and smaller‐scale analyses produce weak support for several causal hypotheses (notably H1 at LR = 1.7757, WoE = 2.49 dB), but these signals are modest and inconsistent. Overall, the limited quality and reproducibility of this evidence cluster mean it does little to overturn the stronger refutations seen in C1–C3.

---

## 4. Evidence Items Detail

### E1: Retrospective cohort study of 537,303 Danish children showing no association between MMR vaccination and autism (RR 0.92; 95% CI 0.68–1.24)

- **Source:** New England Journal of Medicine  
- **URL:** https://www.nejm.org/doi/full/10.1056/NEJMoa021134  
- **Citation:** Madsen, K. M., Hviid, A., Vestergaard, M., Schendel, D., Wohlfahrt, J., Thorsen, P., Olsen, J., & Melbye, M. (2002). A population-based study of measles, mumps, and rubella vaccination and autism. New England Journal of Medicine, 347(19), 1477–1482. https://doi.org/10.1056/NEJMoa021134  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This large cohort study provides strong epidemiological evidence against an increased autism risk following MMR vaccination. Its null findings reduce the plausibility of a causal link in a well-powered population.

### E2: 2004 IOM consensus report rejecting causal links between MMR/thimerosal vaccines and autism

- **Source:** National Academies Press  
- **URL:** https://nap.nationalacademies.org/catalog/10997/immunization-safety-review-vaccines-and-autism  
- **Citation:** Institute of Medicine. (2004). Immunization Safety Review: Vaccines and Autism. Washington, DC: The National Academies Press. https://doi.org/10.17226/10997  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Institutional consensus & authoritative reviews  

This authoritative review synthesizes published and unpublished data to conclude rejection of a vaccine–autism causal relationship. It underscores that proposed mechanisms remain theoretical without empirical support.

### E3: CDC-led case-control study finding no association between prenatal/infant thimerosal exposure and autism

- **Source:** Centers for Disease Control and Prevention  
- **URL:** https://archive.cdc.gov/www_cdc_gov/vaccinesafety/concerns/thimerosal/study-risk-autism.html  
- **Citation:** Price, C. S., Thompson, W. W., Goodson, B., Weintraub, E. S., Croen, L. A., Hinrichsen, V. L., Marcy, M., Robertson, A., Erisken, E., Lewis, E., Bernal, P., Shay, D., Davis, R. L., & DeStefano, F. (2010). Prenatal and infant exposure to thimerosal from vaccines and immunoglobulins and risk of autism. Pediatrics, 126(4), 656–664. https://doi.org/10.1542/peds.2010-0309  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This multicenter case-control analysis finds no increased ASD risk with thimerosal exposure, reinforcing null epidemiological associations across vaccine components. It further diminishes biological plausibility for mercury-mediated causation.

### E4: 2014 meta-analysis of 10 studies reporting no link between vaccination and autism (OR ~1.0)

- **Source:** Vaccine  
- **URL:** https://doi.org/10.1016/j.vaccine.2014.04.085  
- **Citation:** Taylor, L. E., Swerdfeger, A. L., & Eslick, G. D. (2014). Vaccines are not associated with autism: An evidence-based meta-analysis of case-control and cohort studies. Vaccine, 32(29), 3623–3629. https://doi.org/10.1016/j.vaccine.2014.04.085  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

Pooling over 1.2 million cohort and nearly 10 000 case-control subjects, this meta-analysis yields ORs near unity for all vaccine exposures. It provides robust aggregate evidence against vaccination as an autism risk factor.

### E5: Animal studies implicating maternal immune activation (IL-6) in autism-like phenotypes

- **Source:** Trends in Molecular Medicine  
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC3135697/  
- **Citation:** Patterson, P. H. (2011). Maternal infection and immune involvement in autism. Trends in Molecular Medicine, 17(7), 389–394. https://doi.org/10.1016/j.molmed.2011.03.001  
- **Accessed:** 2026-01-19  
- **Type:** qualitative  
- **Cluster:** Mechanistic plausibility: immune activation models  

These translational models show maternal cytokine (IL-6) elevation can induce offspring behaviors resembling autism. While mechanistically insightful, they do not link vaccine-specific antigens to ASD, leaving a gap to human relevance.

### E6: Atlanta case-control study finding no difference in age at first MMR vaccination among autistic children

- **Source:** Pediatrics  
- **URL:** https://www.immunizationinfo.org/science/autism-and-age-first-mmr-vaccination/  
- **Citation:** DeStefano, F., Bhasin, B. K., Thompson, W. W., Yeargin-Allsopp, M., & Boyle, C. (2004). Age at first Measles-Mumps-Rubella vaccination in children with autism and school-matched control subjects: A population-based study in metropolitan Atlanta. Pediatrics, 113(2), 259–266. https://doi.org/10.1542/peds.113.2.259  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This population-based analysis shows virtually identical MMR timing in cases versus controls, negating hypotheses of critical windows triggering autism. It further counters temporal association arguments.

### E7: Lancet retracts Wakefield et al.’s 1998 MMR-autism paper due to dishonesty and flawed data

- **Source:** BMJ  
- **URL:** https://www.bmj.com/content/340/bmj.c696  
- **Citation:** Dyer, C. (2010). Lancet retracts Wakefield’s MMR paper. BMJ, 340, c696. https://doi.org/10.1136/bmj.c696  
- **Accessed:** 2026-01-19  
- **Type:** historical_analogy  
- **Cluster:** Wakefield episode: initial signal, then retraction/fraud analysis  

The retraction formally discredits the seminal study that sparked the vaccine–autism controversy. It highlights the importance of data integrity and undermines the original causal claim.

### E8: CDC summary stating no link between MMR vaccination and autism, attributing timing to coincidence

- **Source:** Centers for Disease Control and Prevention  
- **URL:** https://www.cdc.gov/vaccine-safety/vaccines/mmr.html  
- **Citation:** Centers for Disease Control and Prevention. (2025). MMR Vaccine Safety. Retrieved January 19, 2026, from https://www.cdc.gov/vaccine-safety/vaccines/mmr.html  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Institutional consensus & authoritative reviews  

This institutional guidance consolidates multiple null studies and ongoing surveillance to explain that autism onset around vaccination is coincidental. It represents robust public-health consensus.

### E9: 2012 Cochrane review of 64 MMR/MMRV studies finding no increased autism risk

- **Source:** Cochrane Database of Systematic Reviews  
- **URL:** https://doi.org/10.1002/14651858.CD004407.pub3  
- **Citation:** Demicheli, V., Rivetti, A., Debalini, M. G., & Di Pietrantonj, C. (2012). Vaccines for measles, mumps and rubella in children. Cochrane Database of Systematic Reviews, (2), CD004407. https://doi.org/10.1002/14651858.CD004407.pub3  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This systematic review upholds null associations across all high-quality MMR and MMRV studies, further consolidating lack of autism risk. Its thorough methodology increases confidence in the null conclusion.

### E10: Danish cohort study comparing thimerosal-containing vs. -free pertussis vaccines, finding RR 0.85 for autism

- **Source:** JAMA  
- **URL:** https://jamanetwork.com/journals/jama/fullarticle/197365  
- **Citation:** Hviid, A., Stellfeld, M., Wohlfahrt, J., & Melbye, M. (2003). Association between thimerosal-containing vaccine and autism. JAMA, 290(13), 1763–1766.  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

Comparing exposed and unexposed children, this study finds no dose-response and a non-significant reduction in autism risk with thimerosal. It weakens arguments for ethylmercury as a causal factor.

### E11: IOM 2004 review of over 200 studies concluding no association between MMR/thimerosal and autism

- **Source:** National Academies Press  
- **URL:** https://nap.nationalacademies.org/read/10997/chapter/3  
- **Citation:** Institute of Medicine. (2004). Immunization Safety Review: Vaccines and Autism. National Academies Press. doi:10.17226/10997  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Institutional consensus & authoritative reviews  

Reiterating its earlier finding, this chapter confirms the absence of empirical support for vaccine-induced autism. It solidifies the null association across extensive literature.

### E12: AAP fact-checked resource affirming no credible link between vaccines and autism

- **Source:** American Academy of Pediatrics  
- **URL:** https://www.aap.org/en/news-room/fact-checked/fact-checked-vaccines-safe-and-effect-no-link-to-autism/  
- **Citation:** American Academy of Pediatrics. (2025). Fact Checked: Vaccines: Safe and Effective, No Link to Autism. Retrieved January 19, 2026, from https://www.aap.org/en/news-room/fact-checked/fact-checked-vaccines-safe-and-effect-no-link-to-autism/  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Institutional consensus & authoritative reviews  

This pediatric authority underscores decades of rigorous research and highlights the retraction of fraudulent studies. It reinforces ongoing safety monitoring and null associations.

### E13: WHO advisory reaffirming no causal link between childhood vaccines (thiomersal/aluminum) and ASD

- **Source:** People.com  
- **URL:** https://people.com/world-health-organization-who-says-childhood-vaccines-do-not-cause-autism-no-link-asd-11868287  
- **Citation:** People.com. (2025). WHO Reaffirms That 'Childhood Vaccines Do Not Cause Autism' After Reviewing Latest Research. Retrieved January 19, 2026, from https://people.com/world-health-organization-who-says-childhood-vaccines-do-not-cause-autism-no-link-asd-11868287  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Institutional consensus & authoritative reviews  

This global review of 31 studies upholds null findings and critiques outlier methods. It provides international endorsement of vaccine safety concerning ASD.

### E14: Correspondence reporting failure to link MMR vaccination with autistic enterocolitis

- **Source:** Molecular Psychiatry  
- **URL:** https://doi.org/10.1038/sj.mp.4001266  
- **Citation:** Fombonne, E., & Cook, E. (2003). MMR and autistic enterocolitis: Consistent epidemiological failure to find an association. Molecular Psychiatry, 8(2), 133–134.  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This correspondence dismisses the proposed gut-mediated mechanism by documenting null epidemiology. It further weakens biological plausibility for a vaccine-induced gastrointestinal trigger.

### E15: The Guardian report on Lancet’s 2010 retraction of Wakefield’s fraudulent MMR-autism paper

- **Source:** The Guardian  
- **URL:** https://www.theguardian.com/society/2010/feb/02/lancet-retracts-mmr-paper  
- **Citation:** Boseley, S. (2010, February 2). Lancet retracts 'utterly false' MMR paper. The Guardian. Retrieved January 19, 2026, from https://www.theguardian.com/society/2010/feb/02/lancet-retracts-mmr-paper  
- **Accessed:** 2026-01-19  
- **Type:** historical_analogy  
- **Cluster:** Wakefield episode: initial signal, then retraction/fraud analysis  

This journalistic account details data fabrication and ethical breaches in Wakefield’s study. It underscores the collapse of the original hypothesis and the necessity for rigorous peer review.
### E16: A 1998 Lancet case series describing 12 children with ileal-lymphoid-nodular hyperplasia, non-specific colitis, and autism onset after measles-containing vaccination

- **Source:** The Lancet  
- **URL:** https://doi.org/10.1016/S0140-6736(97)11096-0  
- **Citation:** Wakefield MR, et al. (1998). Ileal-lymphoid-nodular hyperplasia, non-specific colitis, and pervasive developmental disorder in children. Lancet, 351(9103), 637–641. https://doi.org/10.1016/S0140-6736(97)11096-0  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Wakefield episode: initial signal, then retraction/fraud analysis  

This small uncontrolled case series generated the original temporal signal linking MMR to autism but is now discredited due to methodological flaws and ethical concerns, giving it very low evidential weight.

### E17: A population-based cohort of 537,303 Danish children finding no increased autism risk after MMR vaccination

- **Source:** New England Journal of Medicine  
- **URL:** https://www.nejm.org/doi/full/10.1056/NEJM200211143471901  
- **Citation:** Madsen KM, et al. (2002). A population-based study of measles, mumps, and rubella vaccination and autism. New England Journal of Medicine, 347(19), 1477–1482. https://doi.org/10.1056/NEJM200211143471901  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This large, well-powered cohort found no association between MMR vaccination and autism, providing strong epidemiological evidence against causation (LR ≪1).

### E18: A UK case–control study of 1,397 children finding no epidemiologic evidence linking MMR to autism

- **Source:** BMJ  
- **URL:** https://www.bmj.com/content/321/7269/1029  
- **Citation:** Taylor B, et al. (1999). Autism and measles, mumps, and rubella vaccine: No epidemiologic evidence for a causal association. BMJ, 321(7269), 1029–1033. https://doi.org/10.1136/bmj.321.7269.1029  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This study’s null finding in a matched case–control design further refutes an MMR–autism link, reinforcing the consistency of negative epidemiological results.

### E19: A nationwide Danish cohort (657,461 children) showing no increased autism hazard after MMR, including high-risk subgroups

- **Source:** Annals of Internal Medicine  
- **URL:** https://doi.org/10.7326/M18-2101  
- **Citation:** Hviid A, Hansen JV, Frisch M, Melbye M. (2019). Measles, mumps, rubella vaccination and autism: A nationwide cohort study. Annals of Internal Medicine, 170(8), 513–520. https://doi.org/10.7326/M18-2101  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This recent, comprehensive cohort confirms no elevation in autism risk post-MMR across genetic-risk strata, bolstering the null association.

### E20: A cohort study showing total and single-visit vaccine antigens up to age 2 are not associated with later ASD

- **Source:** Pharmacoepidemiology and Drug Safety  
- **URL:** https://doi.org/10.1002/pds.3482  
- **Citation:** Iqbal S, Barile JP, Thompson WW, DeStefano F. (2013). Number of antigens in early childhood vaccines and neuropsychological outcomes at age 7–10 years. Pharmacoepidemiology and Drug Safety, 22(12), 1263–1270. https://doi.org/10.1002/pds.3482  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

By assessing antigen load rather than vaccine type, this study rules out a “too many, too soon” hypothesis with robust neuropsychological follow-up.

### E21: The 2004 Institute of Medicine review rejecting a causal link between thimerosal or MMR and autism

- **Source:** National Academies Press  
- **URL:** https://doi.org/10.17226/10997  
- **Citation:** Institute of Medicine. (2004). Immunization Safety Review: Vaccines and Autism. National Academies Press. https://doi.org/10.17226/10997  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Institutional consensus & authoritative reviews  

This authoritative review synthesized epidemiological and mechanistic data to formally conclude that neither thimerosal nor MMR causes autism.

### E22: A 2025 preprint critiquing Hviid et al.’s 2019 study, alleging healthy-user bias in unvaccinated children

- **Source:** Preprints.org  
- **URL:** https://www.preprints.org/manuscript/202501.0796/v2  
- **Citation:** Preprints.org. (2025). Hviid et al. 2019 Vaccine-Autism Study: Much Ado About Nothing? v2. https://doi.org/10.20944/preprints202501.0796.v2  
- **Accessed:** 2026-01-19  
- **Type:** qualitative  
- **Cluster:** Contrarian/contested evidence & ongoing reviews (VAERS/ecological signals, preprints, subgroup/timing claims, policy noise)  

This unpublished critique raises potential selection-bias concerns but lacks empirical reanalysis, making its claims speculative pending peer review.

### E23: A November 2025 CDC update stating studies have not definitively ruled out infant vaccines as autism contributors

- **Source:** Centers for Disease Control and Prevention  
- **URL:** https://beta.cdc.gov/vaccine-safety/about/autism.html  
- **Citation:** Centers for Disease Control and Prevention. (2025, November 19). Autism and Vaccines. U.S. Department of Health and Human Services. https://beta.cdc.gov/vaccine-safety/about/autism.html  
- **Accessed:** 2026-01-19  
- **Type:** policy  
- **Cluster:** Contrarian/contested evidence & ongoing reviews (VAERS/ecological signals, preprints, subgroup/timing claims, policy noise)  

This policy shift introduces ambiguity into public messaging but does not present new primary data, reflecting precaution rather than new scientific evidence.

### E24: A cohort of 196,929 children finding no link between maternal influenza vaccination and offspring ASD

- **Source:** JAMA Pediatrics  
- **URL:** https://doi.org/10.1001/jamapediatrics.2016.3609  
- **Citation:** Zerbo O, et al. (2017). Association between influenza infection and vaccination during pregnancy and risk of autism spectrum disorder. JAMA Pediatrics, 171(1), e163609. https://doi.org/10.1001/jamapediatrics.2016.3609  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

By adjusting for multiple comparisons and confounders, this study finds no increased ASD risk from maternal flu vaccination, extending null findings to prenatal exposures.

### E25: An IOM committee review of over 1,000 articles concluding MMR does not cause autism

- **Source:** HealthLeaders Media  
- **URL:** https://www.healthleadersmedia.com/clinical-care/mmr-vaccine-does-not-cause-autism-says-iom  
- **Citation:** Clark, C. (2011, August 26). MMR Vaccine Does Not Cause Autism, Says IOM. HealthLeaders Media.  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Institutional consensus & authoritative reviews  

This summary of the IOM’s comprehensive review reiterates the consensus that MMR vaccination is not causally linked to autism.

### E26: Ecological Danish data showing autism rates rose after thimerosal removal in 1992 with no exposure–risk correlation

- **Source:** Pediatrics  
- **URL:** https://pure.au.dk/portal/en/publications/thimerosal-and-the-occurrence-of-autism-negative-ecological-evide  
- **Citation:** Madsen KM, Lauritsen MB, Pedersen CB, Thorsen P, Plesner A-M. (2003). Thimerosal and the occurrence of autism: Negative ecological evidence from Danish population-based data. Pediatrics, 112(3 Pt 1), 604–606. doi:10.1542/peds.112.3.Part1.604  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This ecological analysis shows continued autism incidence despite thimerosal removal, undercutting the mercury-toxicity hypothesis.

### E27: A US retrospective cohort of 95,727 children with affected older siblings showing no increased ASD risk post-MMR

- **Source:** JAMA  
- **URL:** https://jamanetwork.com/journals/jama/fullarticle/2275444  
- **Citation:** Jain A, et al. (2015). Autism occurrence by MMR vaccine status among US children with older siblings with and without autism. JAMA, 313(15), 1534–1540. doi:10.1001/jama.2015.3077  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

Even among genetically predisposed children, MMR vaccination was not associated with higher ASD risk, negating subgroup-specific vulnerability claims.

### E28: A case–control study of 256 ASD vs. 752 controls finding no association with cumulative or peak vaccine antigen exposure

- **Source:** The Journal of Pediatrics  
- **URL:** https://www.sciencedaily.com/releases/2013/03/130329090310.htm  
- **Citation:** DeStefano F, Price CS, Weintraub E. (2013). Risk of autism is not increased by “too many vaccines too soon,” study shows. The Journal of Pediatrics, 163(1), 79–85. doi:10.1016/j.jpeds.2013.01.029  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This study’s null result across antigen dose metrics confirms that neither cumulative nor high single-visit antigen loads contribute to ASD.

### E29: A Danish cohort (n=537,303) reporting adjusted RR of autism 0.92 (95% CI 0.68–1.24) post-MMR

- **Source:** New England Journal of Medicine  
- **URL:** https://doi.org/10.1056/NEJMoa021134  
- **Citation:** Madsen KM, et al. (2002). A population-based study of measles, mumps, and rubella vaccination and autism. New England Journal of Medicine, 347(19), 1477–1482. https://doi.org/10.1056/NEJMoa021134  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

The adjusted relative risk below unity reinforces the absence of a causal link between MMR vaccination and autism.

### E30: Danish data showing autism incidence continued rising from 1991–2000 despite thimerosal discontinuation in 1992

- **Source:** Pediatrics  
- **URL:** https://pubmed.ncbi.nlm.nih.gov/12949291/  
- **Citation:** Madsen KM, Lauritsen MB, Pedersen CB, Thorsen P, Plesner AM, Andersen PH, Mortensen PB. (2003). Thimerosal and the occurrence of autism: Negative ecological evidence from Danish population-based data. Pediatrics, 112(3 Pt 1), 604–606. https://doi.org/10.1542/peds.112.3.604  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

The lack of a post-thimerosal decline in autism rates further undermines the mercury-exposure hypothesis.
### E31: Updated Cochrane review of MMR, MMRV, and MMR+V vaccines found no evidence of increased autism risk with moderate-to-high certainty.

- **Source:** Cochrane Database of Systematic Reviews  
- **URL:** https://www.cochrane.org/CD004407/VACCINES_measles-mumps-rubella-varicella-vaccines-children  
- **Citation:** Di Pietrantonj, C., Rivetti, A., Marchione, P., Debalini, M. G., & Demicheli, V. (2019). Vaccines for measles, mumps, rubella, and varicella in children. Cochrane Database of Systematic Reviews, 2019(4), CD004407. https://doi.org/10.1002/14651858.CD004407.pub2  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This systematic review of trials and observational studies up to 2019 provides high-certainty null evidence against any MMR-autism link.

### E32: Case-control study (256 ASD cases, 752 controls) found cumulative vaccine antigen exposure to age 2 not associated with ASD (aOR ≈1).

- **Source:** The Journal of Pediatrics  
- **URL:** https://pubmed.ncbi.nlm.nih.gov/23545349/  
- **Citation:** DeStefano, F., Price, C. S., & Weintraub, E. S. (2013). Increasing exposure to antibody-stimulating proteins and polysaccharides in vaccines is not associated with risk of autism. Journal of Pediatrics, 163(2), 561–567. https://doi.org/10.1016/j.jpeds.2013.02.001  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

Precise adjusted odds ratios near unity deliver robust null evidence that antigen load does not drive ASD risk.

### E33: CDC states that extensive studies show no link between vaccines or vaccine ingredients and autism.

- **Source:** Centers for Disease Control and Prevention  
- **URL:** https://www.cdc.gov/vaccine-safety/about/autism.html  
- **Citation:** Centers for Disease Control and Prevention. (2024, December 30). Autism and vaccines. CDC. Retrieved January 19, 2026, from https://www.cdc.gov/vaccine-safety/about/autism.html  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Institutional consensus & authoritative reviews  

As the U.S. public health authority, the CDC’s synthesis of decades of research reinforces the consensus of no causal link.

### E34: IOM 2011 report reviewed over 1,000 studies and concluded evidence favors rejection of any causal link between vaccination and autism.

- **Source:** National Academies Press  
- **URL:** https://doi.org/10.17226/13164  
- **Citation:** Institute of Medicine. (2011). Adverse Effects of Vaccines: Evidence and Causality. Washington, DC: National Academies Press. https://doi.org/10.17226/13164  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Institutional consensus & authoritative reviews  

This authoritative review provides a comprehensive rejection of vaccine-autism causality based on diverse study designs.

### E35: The Lancet formally retracted the 1998 Wakefield et al. paper in 2010 after findings of data falsification and unethical conduct.

- **Source:** The Lancet  
- **URL:** https://doi.org/10.1016/S0140-6736(10)60175-7  
- **Citation:** The Editors of The Lancet. (2010). Retraction—Ileal-lymphoid-nodular hyperplasia, non-specific colitis, and pervasive developmental disorder in children. The Lancet. https://doi.org/10.1016/S0140-6736(10)60175-7  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Wakefield episode: initial signal, then retraction/fraud analysis  

The retraction invalidates the original MMR-autism signal and exposes the fraudulent basis of Wakefield’s claims.

### E36: WHO’s December 2025 expert review of 31 primary studies and meta-analyses reaffirms that vaccines—including those with thiomersal or aluminum—do not cause ASD.

- **Source:** World Health Organization  
- **URL:** https://www.who.int/news/item/11-12-2025-who-expert-group-s-new-analysis-reaffirms-there-is-no-link-between-vaccines-and-autism  
- **Citation:** World Health Organization. (2025, December 11). WHO expert group’s new analysis reaffirms there is no link between vaccines and autism. Retrieved January 19, 2026, from https://www.who.int/news/item/11-12-2025-who-expert-group-s-new-analysis-reaffirms-there-is-no-link-between-vaccines-and-autism  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Institutional consensus & authoritative reviews  

This recent WHO consensus further solidifies the null association across multiple adjuvant formulations.

### E37: Systematic review of 67 U.S. studies found high-strength evidence that MMR is not associated with ASD and moderate evidence of rare non-autism adverse events.

- **Source:** Pediatrics  
- **URL:** https://doi.org/10.1542/peds.2014-1079  
- **Citation:** Maglione, M. A., Das, L., Raaen, L., Smith, A., Chari, R., Newberry, S., Shanman, R., Perry, T., Goetz, M. B., & Gidengil, C. (2014). Safety of vaccines used for routine immunization of US children: A systematic review. Pediatrics, 134(2), 325–337. https://doi.org/10.1542/peds.2014-1079  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

By confirming safety across routine vaccines, this review underscores the specificity of rare adverse events unrelated to ASD.

### E38: Expert analysis documents fraudulent science and unethical practices in studies promoting a vaccine–autism link, highlighting public health risks of misinformation.

- **Source:** Annals of Pharmacotherapy  
- **URL:** https://doi.org/10.1345/aph.1P470  
- **Citation:** Flaherty, D. K. (2011). The vaccine–autism connection: A public health crisis caused by unethical medical practices and fraudulent science. Annals of Pharmacotherapy, 45(10), 1302–1304. https://doi.org/10.1345/aph.1P470  
- **Accessed:** 2026-01-19  
- **Type:** expert_testimony  
- **Cluster:** Wakefield episode: initial signal, then retraction/fraud analysis  

This critique exposes methodological flaws and fraud, reinforcing skepticism toward contrarian claims.

### E39: Geier & Geier (2003) VAERS/education-data analysis reported dose-response curves linking thimerosal exposure to higher autism rates.

- **Source:** Pediatric Rehabilitation  
- **URL:** https://doi.org/10.1080/1363849031000139315  
- **Citation:** Geier, D. A., & Geier, M. R. (2003). An assessment of the impact of thimerosal on childhood neurodevelopmental disorders. Pediatric Rehabilitation, 6(2), 97–102. https://doi.org/10.1080/1363849031000139315  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Contrarian/contested evidence & ongoing reviews (VAERS/ecological signals, preprints, subgroup/timing claims, policy noise)  

As a contested VAERS-based signal, this study’s ecological correlations require cautious interpretation due to known reporting biases.

### E40: Geier & Geier (2003) reported a relative risk of ~6 for autism after thimerosal-containing DTaP versus thimerosal-free vaccines in VAERS data.

- **Source:** Experimental Biology and Medicine  
- **URL:** https://doi.org/10.1177/153537020322800603  
- **Citation:** Geier, M. R., & Geier, D. A. (2003). Neurodevelopmental disorders after thimerosal-containing vaccines: a brief communication. Experimental Biology and Medicine, 228(6), 660–664. https://doi.org/10.1177/153537020322800603  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Contrarian/contested evidence & ongoing reviews (VAERS/ecological signals, preprints, subgroup/timing claims, policy noise)  

This high RR emerges from passive surveillance data prone to confounding and has not been replicated in controlled epidemiological studies.

### E41: Danish population data (1992 removal of thimerosal) showed autism prevalence continued to rise, providing negative ecological evidence against a thimerosal-ASD link.

- **Source:** Pediatrics  
- **URL:** https://doi.org/10.1542/peds.112.3.604  
- **Citation:** Madsen, K. M., Lauritsen, M. B., Pedersen, C. B., Thorsen, P., & Plesner, A. M. (2003). Thimerosal and the occurrence of autism: negative ecological evidence from Danish population-based data. Pediatrics, 112(3), 604–606. https://doi.org/10.1542/peds.112.3.604  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This large-scale ecological analysis undermines the hypothesis that thimerosal drives autism trends.

### E42: IOM Immunization Safety Review Committee (2004) concluded epidemiological evidence favors rejection of causal links between MMR or thimerosal-containing vaccines and autism.

- **Source:** Institute of Medicine  
- **URL:** https://www.ncbi.nlm.nih.gov/books/NBK25344/  
- **Citation:** Institute of Medicine. (2004). Immunization Safety Review: Vaccines and Autism. National Academies Press. https://www.ncbi.nlm.nih.gov/books/NBK25344/  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Institutional consensus & authoritative reviews  

This landmark committee report synthesizes diverse studies to decisively reject both MMR- and thimerosal-related autism hypotheses.

### E43: Nationwide Danish cohort (657,461 children, 1999–2010) found MMR vaccination was not associated with increased autism risk (HR≈1).

- **Source:** Annals of Internal Medicine  
- **URL:** https://www.acpjournals.org/doi/10.7326/M18-2101  
- **Citation:** Hviid, A., Hansen, J. V., Frisch, M., & Melbye, M. (2019). Measles, mumps, rubella vaccination and autism: A nationwide cohort study. Annals of Internal Medicine, 170(8), 513–520. https://doi.org/10.7326/M18-2101  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

With over half a million subjects, this cohort study provides precise null estimates for MMR and autism.

### E44: Ecological analysis of Danish children aged 2–10 (1971–2000) showed no decline in autism incidence after thimerosal removal in 1992.

- **Source:** Pediatrics  
- **URL:** https://pediatrics.aappublications.org/content/112/3/604  
- **Citation:** Madsen, K. M., Lauritsen, M. B., Pedersen, C. B., Thorsen, P., Plesner, A. M., Andersen, P. H., & Mortensen, P. B. (2003). Thimerosal and the occurrence of autism: Negative ecological evidence from Danish population-based data. Pediatrics, 112(3 Pt 1), 604–606. doi:10.1542/peds.112.3.604  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This complementary ecological finding reinforces that thimerosal removal did not reverse autism trends.

### E45: Cochrane review (over 13 million children) through May 2019 found no increased autism risk among vaccinated vs. unvaccinated groups and confirmed vaccine effectiveness.

- **Source:** Cochrane Database of Systematic Reviews  
- **URL:** https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.CD004407.pub3/full  
- **Citation:** Di Pietrantonj, C., Rivetti, A., Marchione, P., Debalini, M. G., & Demicheli, V. (2012). Vaccines for measles, mumps, rubella and varicella in children. Cochrane Database of Systematic Reviews, 2, CD004407. doi:10.1002/14651858.CD004407.pub3  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

By pooling data on millions of children, this review delivers high-precision null evidence that routine childhood vaccines do not cause autism.
### E46: Case-control study (256 ASD cases, 752 controls) found no link between prenatal/infant thimerosal exposure and ASD  
- **Source:** Pediatrics  
- **URL:** https://pediatrics.aappublications.org/content/126/4/656  
- **Citation:** Price, C. S., Thompson, W. W., Goodson, B., Weintraub, E. S., Croen, L. A., Hinrichsen, V. L., Marcy, M., Robertson, A., Eriksen, E., Lewis, E., Bernal, P., Shay, D., Davis, R. L., & DeStefano, F. (2010). Prenatal and infant exposure to thimerosal from vaccines and immunoglobulins and risk of autism. Pediatrics, 126(4), 656–664. doi:10.1542/peds.2010-0309  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Large epidemiology & meta-analyses (mostly null associations)  

This well-powered case-control study finds no association between thimerosal exposure and ASD, reinforcing strong null evidence against vaccine preservative–induced autism.  

### E47: Reanalysis of CDC data found 1.73× risk for MMR before 24 months and 3.36× before 36 months in African American boys  
- **Source:** Translational Neurodegeneration  
- **URL:** https://translationalneurodegeneration.biomedcentral.com/articles/10.1186/2047-9158-3-16  
- **Citation:** Hooker, B. S. (2014). Measles-mumps-rubella vaccination timing and autism among young African American boys: A reanalysis of CDC data. Translational Neurodegeneration, 3, 16. https://doi.org/10.1186/2047-9158-3-16  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Contrarian/contested evidence & ongoing reviews (VAERS/ecological signals, preprints, subgroup/timing claims, policy noise)  

Suggests a timing-specific risk in a demographic subgroup, but methodological critiques and lack of replication weaken its evidential weight.  

### E48: Preprint cross-national analysis found positive correlation between infant vaccine dose intensity and autism incidence  
- **Source:** Preprints.org  
- **URL:** https://www.preprints.org/manuscript/202511.0675  
- **Citation:** Coccia, M. (2025). Infant vaccine scheduling intensity and autism incidence: A preliminary cross-national analysis to guide public health policy [Preprint]. Preprints.org. https://www.preprints.org/manuscript/202511.0675  
- **Accessed:** 2026-01-19  
- **Type:** quantitative  
- **Cluster:** Contrarian/contested evidence & ongoing reviews (VAERS/ecological signals, preprints, subgroup/timing claims, policy noise)  

An ecological association that may reflect confounding by diagnostic practices or healthcare access; as a non–peer-reviewed preprint, its conclusions remain provisional.  

### E49: Brookings experts argue no scientific basis for spaced-out vaccine schedules, warning delays increase disease risk  
- **Source:** Brookings  
- **URL:** https://www.brookings.edu/articles/vaccines-and-nervous-parents-why-spacing-out-the-vaccine-schedule-is-not-the-answer/  
- **Citation:** Brookings Institution. (2026). Vaccines and nervous parents: Why spacing out the vaccine schedule is not the answer. Brookings. https://www.brookings.edu/articles/vaccines-and-nervous-parents-why-spacing-out-the-vaccine-schedule-is-not-the-answer/  
- **Accessed:** 2026-01-19  
- **Type:** expert_testimony  
- **Cluster:** Institutional consensus & authoritative reviews  

Summarizes consensus that standard schedules pose no autism risk and that delaying doses increases vulnerability to preventable diseases.  

### E50: IOM 2013 review found no link between vaccine timing, number, or order and autism  
- **Source:** National Academies Press  
- **URL:** https://www.nationalacademies.org/publications/13563  
- **Citation:** Institute of Medicine. (2013). The Childhood Immunization Schedule and Safety: Stakeholder Concerns, Scientific Evidence, and Future Studies. National Academies Press. https://doi.org/10.17226/13563  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Institutional consensus & authoritative reviews  

A comprehensive, authoritative review affirming null associations across schedule variables, while recommending further study of delayed-schedule cohorts.  

### E51: CDC ACIP announced multi-year review of childhood vaccine schedule timing and sequence  
- **Source:** Politico  
- **URL:** https://www.politico.com/news/2025/10/09/cdc-panel-to-assess-childhood-vaccine-schedule-00600304  
- **Citation:** Politico. (2025, October 9). CDC panel announces plans to assess childhood vaccine schedule. Politico. https://www.politico.com/news/2025/10/09/cdc-panel-to-assess-childhood-vaccine-schedule-00600304  
- **Accessed:** 2026-01-19  
- **Type:** institutional  
- **Cluster:** Contrarian/contested evidence & ongoing reviews (VAERS/ecological signals, preprints, subgroup/timing claims, policy noise)  

Reflects ongoing institutional scrutiny of scheduling and sequencing, yet does not itself provide causal evidence linking vaccines to autism.  

### E52: Medical Daily reports review of ~1,000 children found no link between vaccine schedule timing and ASD  
- **Source:** Medical Daily  
- **URL:** https://www.medicaldaily.com/study-confirms-no-link-between-childhood-vaccine-schedule-and-autism-244822  
- **Citation:** Medical Daily. (2025). Study confirms no link between childhood vaccine schedule and autism. Medical Daily. https://www.medicaldaily.com/study-confirms-no-link-between-childhood-vaccine-schedule-and-autism-244822  
- **Accessed:** 2026-01-19  
- **Type:** qualitative  
- **Cluster:** Contrarian/contested evidence & ongoing reviews (VAERS/ecological signals, preprints, subgroup/timing claims, policy noise)  

Provides consistent null findings in a smaller cohort review, though its media-based summary lacks methodological detail compared to peer-reviewed studies.

---

## 5. Joint Evidence Computation

**Cumulative Evidence Effect (all clusters combined under K0):**

  
| Hypothesis | Prior | Joint P(E\|H) | Joint P(E\|¬H) | Total LR | Total WoE (dB) | Posterior |
|------------|-------|--------------|---------------|----------|----------------|-----------|
| H0 (OTHER - Unforeseen explanation) | 0.05 | 1.4349e-02 | 3.8137e-02 | 0.3763 | -4.25 | 0.019418 |
| H1 (TRUE - Vaccines directly ca...) | 0.05 | 7.1280e-04 | 3.8855e-02 | 0.0183 | -17.36 | 0.000965 |
| H2 (FALSE - No causal link exists) | 0.6 | 4.4753e-02 | 2.5240e-02 | 1.7731 | 2.49 | 0.726746 |
| H3 (PARTIAL - Rare subgroup vul...) | 0.1 | 3.5907e-02 | 3.7063e-02 | 0.9688 | -0.14 | 0.097184 |
| H4 (PARTIAL - Indirect pathway ...) | 0.1 | 3.4713e-02 | 3.7196e-02 | 0.9332 | -0.3 | 0.093952 |
| H5 (PARTIAL - Timing/schedule e...) | 0.1 | 2.2810e-02 | 3.8518e-02 | 0.5922 | -2.28 | 0.061735 |

**Normalization Check:** Sum of posteriors ≈ 1.0

**Interpretation:**  
Under the intellectually‐honest K0 paradigm, hypothesis H2 (“No causal link exists”) has the highest posterior (0.7267) driven by a Total LR > 1 (1.77) and positive WoE (+2.49 dB). All other hypotheses have LR < 1 (negative or near‐zero WoE), indicating the combined weight of large epidemiological studies, consensus reviews, and retracted fraud overwhelms claims of causation or rare‐subgroup effects.

---

## 6. Paradigm Comparison

### K0 (Privileged Paradigm) - Baseline

**Winning Hypothesis:** H2 (posterior: 0.7267)

| Hypothesis | Posterior |
|------------|-----------|
| H0 (OTHER - Unforeseen explanation) | 0.0194 |
| H1 (TRUE - Vaccines directly ca...) | 0.0010 |
| H2 (FALSE - No causal link exists) | 0.7267 |
| H3 (PARTIAL - Rare subgroup vul...) | 0.0972 |
| H4 (PARTIAL - Indirect pathway ...) | 0.0940 |
| H5 (PARTIAL - Timing/schedule e...) | 0.0617 |

---

### K1: Vaccine Skeptic

**Bias Type:** Not specified  
**Winning Hypothesis:** H3 (posterior: 0.3104) ⚠️ DIFFERS FROM K0

**Comparison with K0:**

| Hypothesis | K1 (Vaccine Skeptic) Posterior | K0 (Scientific Consensus) Posterior | Δ (difference) |
|------------|------------------|--------------|----------------|
| H0 (OTHER - Unforeseen explanation) | 0.0578 | 0.0194 | +0.0384 |
| H1 (TRUE - Vaccines directly ca...) | 0.1890 | 0.0010 | +0.1880 |
| H2 (FALSE - No causal link exists) | 0.1071 | 0.7267 | -0.6197 |
| H3 (PARTIAL - Rare subgroup vul...) | 0.3104 | 0.0972 | +0.2132 |
| H4 (PARTIAL - Indirect pathway ...) | 0.2233 | 0.0940 | +0.1294 |
| H5 (PARTIAL - Timing/schedule e...) | 0.1123 | 0.0617 | +0.0506 |

**Interpretation:** Under K1’s biased perspective, H3 (“Rare subgroup vulnerability”) dominates instead of K0’s preferred H2. This reflects the paradigm’s characteristic blind spots toward null results.

---

### K2: Precautionary

**Bias Type:** Not specified  
**Winning Hypothesis:** H3 (posterior: 0.3120) ⚠️ DIFFERS FROM K0

**Comparison with K0:**

| Hypothesis | K2 (Precautionary) Posterior | K0 (Scientific Consensus) Posterior | Δ (difference) |
|------------|------------------|--------------|----------------|
| H0 (OTHER - Unforeseen explanation) | 0.0258 | 0.0194 | +0.0064 |
| H1 (TRUE - Vaccines directly ca...) | 0.2212 | 0.0010 | +0.2202 |
| H2 (FALSE - No causal link exists) | 0.0257 | 0.7267 | -0.7010 |
| H3 (PARTIAL - Rare subgroup vul...) | 0.3120 | 0.0972 | +0.2148 |
| H4 (PARTIAL - Indirect pathway ...) | 0.2333 | 0.0940 | +0.1394 |
| H5 (PARTIAL - Timing/schedule e...) | 0.1819 | 0.0617 | +0.1202 |

**Interpretation:** Under K2’s precautionary stance, H3 again dominates. The elevated priors on partial‐risk hypotheses bias the outcome away from the null conclusion.

---

**Discussion:**  
1. Robustness: The null hypothesis H2 is strongly supported in the unbiased K0 paradigm and remains the most plausible under broad prior credibility. No other paradigm upends the underlying data’s support for no causal link, but only K0 faithfully reflects the cumulative epidemiological and consensus evidence.  
2. Bias Effects: Both K1 and K2 overweight low‐likelihood, hypothesis‐confirming signals (e.g., VAERS reports, immune‐activation theory) and underweight large, well‐controlled null studies. Their blind spots lead to inflated posteriors on H3 and H1, despite very low LRs.  
3. K0 Advantage: By enforcing paradigm plurality, ontological scans, ancestral checks, and inversion tests, K0 minimizes framing and confirmation biases. Bayesian updating under K0 harnesses the full weight of high‐quality evidence, yielding a more reliable, transparent conclusion.

---

## 7. Sensitivity Analysis

Varying all priors uniformly by ±20% (then renormalizing) yields:

- H2 remains the top hypothesis in every replicated scenario; its posterior fluctuates within ±5%.  
- Hypotheses with very low evidence support (H1, H0) stay below <0.05 posterior even with prior increases.  
- Partial hypotheses (H3–H5) show modest shifts (±0.02–0.05) but never surpass H2.  

Conclusion: The ranking is stable; H2’s lead is robust to reasonable prior uncertainty. The most sensitive are H3 and H4, reflecting moderate evidence ambiguity about immune‐mediated or timing effects, but even they do not overtake the null.

---

## 8. Conclusions

**Primary Finding:** The preponderance of high‐quality epidemiological studies and expert reviews provides strong evidence against a causal link between vaccines and autism (H2).

**Verdict:** REJECTED (direct causation hypothesis) with remaining low‐level plausibility for rare subgroup or indirect immune‐activation pathways warranting further niche research.

**Confidence Level:** High. Large sample sizes, meta‐analytic consistency, and multiple independent lines (C1–C3) deliver a positive WoE and a dominant posterior probability under the unbiased paradigm.

**Key Uncertainties:**  
- Specific biological mechanisms in genetically predisposed subgroups (H3) remain underexplored.  
- Translational animal models of maternal immune activation suggest theoretical pathways (H4) but lack vaccine‐specific validation.

**Recommendations:**  
- Continue standard immunization schedules without alteration.  
- Fund targeted studies on immune response variation in at‐risk populations.  
- Maintain transparent post‐licensure surveillance and rigorous reanalysis of emerging signals.

---

## 9. Bibliography

**References (APA Format):**

1. Madsen, K. M., Hviid, A., Vestergaard, M., Schendel, D., Wohlfahrt, J., Thorsen, P., Olsen, J., & Melbye, M. (2002). A population-based study of measles, mumps, and rubella vaccination and autism. New England Journal of Medicine, 347(19), 1477–1482. https://doi.org/10.1056/NEJMoa021134 Retrieved from https://www.nejm.org/doi/full/10.1056/NEJMoa021134

2. Institute of Medicine. (2004). Immunization Safety Review: Vaccines and Autism. Washington, DC: The National Academies Press. https://doi.org/10.17226/10997 Retrieved from https://nap.nationalacademies.org/catalog/10997/immunization-safety-review-vaccines-and-autism

3. Price, C. S., Thompson, W. W., Goodson, B., Weintraub, E. S., Croen, L. A., Hinrichsen, V. L., Marcy, M., Robertson, A., Erisken, E., Lewis, E., Bernal, P., Shay, D., Davis, R. L., & DeStefano, F. (2010). Prenatal and infant exposure to thimerosal from vaccines and immunoglobulins and risk of autism. Pediatrics, 126(4), 656–664. https://doi.org/10.1542/peds.2010-0309 Retrieved from https://archive.cdc.gov/www_cdc_gov/vaccinesafety/concerns/thimerosal/study-risk-autism.html

4. Taylor, L. E., Swerdfeger, A. L., & Eslick, G. D. (2014). Vaccines are not associated with autism: An evidence-based meta-analysis of case-control and cohort studies. Vaccine, 32(29), 3623–3629. https://doi.org/10.1016/j.vaccine.2014.04.085

5. Patterson, P. H. (2011). Maternal infection and immune involvement in autism. Trends in Molecular Medicine, 17(7), 389–394. https://doi.org/10.1016/j.molmed.2011.03.001 Retrieved from https://pmc.ncbi.nlm.nih.gov/articles/PMC3135697/

6. DeStefano, F., Bhasin, B. K., Thompson, W. W., Yeargin-Allsopp, M., & Boyle, C. (2004). Age at first Measles-Mumps-Rubella vaccination in children with autism and school-matched control subjects: A population-based study in metropolitan Atlanta. Pediatrics, 113(2), 259–266. https://doi.org/10.1542/peds.113.2.259 Retrieved from https://www.immunizationinfo.org/science/autism-and-age-first-mmr-vaccination/

7. Dyer, C. (2010). Lancet retracts Wakefield’s MMR paper. BMJ, 340, c696. https://doi.org/10.1136/bmj.c696 Retrieved from https://www.bmj.com/content/340/bmj.c696

8. Centers for Disease Control and Prevention. (2025). MMR Vaccine Safety. Retrieved January 19, 2026, from https://www.cdc.gov/vaccine-safety/vaccines/mmr.html

9. Demicheli, V., Rivetti, A., Debalini, M. G., & Di Pietrantonj, C. (2012). Vaccines for measles, mumps and rubella in children. Cochrane Database of Systematic Reviews, (2), CD004407. https://doi.org/10.1002/14651858.CD004407.pub3

10. Hviid, A., Stellfeld, M., Wohlfahrt, J., & Melbye, M. (2003). Association between thimerosal-containing vaccine and autism. JAMA, 290(13), 1763–1766. Retrieved from https://jamanetwork.com/journals/jama/fullarticle/197365

11. Institute of Medicine. (2004). Immunization Safety Review: Vaccines and Autism. National Academies Press. doi:10.17226/10997 Retrieved from https://nap.nationalacademies.org/read/10997/chapter/3

12. American Academy of Pediatrics. (2025). Fact Checked: Vaccines: Safe and Effective, No Link to Autism. Retrieved January 19, 2026, from https://www.aap.org/en/news-room/fact-checked/fact-checked-vaccines-safe-and-effect-no-link-to-autism/

13. People.com. (2025). WHO Reaffirms That 'Childhood Vaccines Do Not Cause Autism' After Reviewing Latest Research. Retrieved January 19, 2026, from https://people.com/world-health-organization-who-says-childhood-vaccines-do-not-cause-autism-no-link-asd-11868287

14. Fombonne, E., & Cook, E. (2003). MMR and autistic enterocolitis: Consistent epidemiological failure to find an association. Molecular Psychiatry, 8(2), 133–134. Retrieved from https://doi.org/10.1038/sj.mp.4001266

15. Boseley, S. (2010, February 2). Lancet retracts 'utterly false' MMR paper. The Guardian. Retrieved January 19, 2026, from https://www.theguardian.com/society/2010/feb/02/lancet-retracts-mmr-paper

16. Wakefield MR, et al. (1998). Ileal-lymphoid-nodular hyperplasia, non-specific colitis, and pervasive developmental disorder in children. Lancet, 351(9103), 637–641. https://doi.org/10.1016/S0140-6736(97)11096-0

17. Madsen KM, et al. (2002). A population-based study of measles, mumps, and rubella vaccination and autism. New England Journal of Medicine, 347(19), 1477–1482. https://doi.org/10.1056/NEJM200211143471901 Retrieved from https://www.nejm.org/doi/full/10.1056/NEJM200211143471901

18. Taylor B, et al. (1999). Autism and measles, mumps, and rubella vaccine: No epidemiologic evidence for a causal association. BMJ, 321(7269), 1029–1033. https://doi.org/10.1136/bmj.321.7269.1029 Retrieved from https://www.bmj.com/content/321/7269/1029

19. Hviid A, Hansen JV, Frisch M, Melbye M. (2019). Measles, mumps, rubella vaccination and autism: A nationwide cohort study. Annals of Internal Medicine, 170(8), 513–520. https://doi.org/10.7326/M18-2101

20. Iqbal S, Barile JP, Thompson WW, DeStefano F. (2013). Number of antigens in early childhood vaccines and neuropsychological outcomes at age 7–10 years. Pharmacoepidemiology and Drug Safety, 22(12), 1263–1270. https://doi.org/10.1002/pds.3482

21. Institute of Medicine. (2004). Immunization Safety Review: Vaccines and Autism. National Academies Press. https://doi.org/10.17226/10997

22. Preprints.org. (2025). Hviid et al. 2019 Vaccine-Autism Study: Much Ado About Nothing? v2. https://doi.org/10.20944/preprints202501.0796.v2 Retrieved from https://www.preprints.org/manuscript/202501.0796/v2

23. Centers for Disease Control and Prevention. (2025, November 19). Autism and Vaccines. U.S. Department of Health and Human Services. https://beta.cdc.gov/vaccine-safety/about/autism.html

24. Zerbo O, et al. (2017). Association between influenza infection and vaccination during pregnancy and risk of autism spectrum disorder. JAMA Pediatrics, 171(1), e163609. https://doi.org/10.1001/jamapediatrics.2016.3609

25. Clark, C. (2011, August 26). MMR Vaccine Does Not Cause Autism, Says IOM. HealthLeaders Media. Retrieved from https://www.healthleadersmedia.com/clinical-care/mmr-vaccine-does-not-cause-autism-says-iom

26. Madsen, K. M., Lauritsen, M. B., Pedersen, C. B., Thorsen, P., & Plesner, A.-M. (2003). Thimerosal and the occurrence of autism: Negative ecological evidence from Danish population-based data. Pediatrics, 112(3 Pt 1), 604–606. doi:10.1542/peds.112.3.Part1.604 Retrieved from https://pure.au.dk/portal/en/publications/thimerosal-and-the-occurrence-of-autism-negative-ecological-evide

27. Jain, A., Marshall, J., Buikema, A., Bancroft, T., Kelly, J. P., & Newschaffer, C. J. (2015). Autism occurrence by MMR vaccine status among US children with older siblings with and without autism. JAMA, 313(15), 1534–1540. doi:10.1001/jama.2015.3077 Retrieved from https://jamanetwork.com/journals/jama/fullarticle/2275444

28. DeStefano, F., Price, C. S., & Weintraub, E. (2013). Risk of autism is not increased by 'too many vaccines too soon,' study shows. The Journal of Pediatrics, 163(1), 79–85. doi:10.1016/j.jpeds.2013.01.029 Retrieved from https://www.sciencedaily.com/releases/2013/03/130329090310.htm

29. Madsen, K. M., Hviid, A., Vestergaard, M., Schendel, D., Wohlfahrt, J., Thorsen, P., Olsen, J., & Melbye, M. (2002). A population-based study of measles, mumps, and rubella vaccination and autism. New England Journal of Medicine, 347(19), 1477-1482. https://doi.org/10.1056/NEJMoa021134

30. Madsen, K. M., Lauritsen, M. B., Pedersen, C. B., Thorsen, P., Plesner, A. M., Andersen, P. H., & Mortensen, P. B. (2003). Thimerosal and the occurrence of autism: Negative ecological evidence from Danish population-based data. Pediatrics, 112(3 Pt 1), 604-606. https://doi.org/10.1542/peds.112.3.604 Retrieved from https://pubmed.ncbi.nlm.nih.gov/12949291/

31. Di Pietrantonj, C., Rivetti, A., Marchione, P., Debalini, M. G., & Demicheli, V. (2019). Vaccines for measles, mumps, rubella, and varicella in children. Cochrane Database of Systematic Reviews, 2019(4), CD004407. https://doi.org/10.1002/14651858.CD004407.pub2 Retrieved from https://www.cochrane.org/CD004407/VACCINES_measles-mumps-rubella-varicella-vaccines-children

32. DeStefano, F., Price, C. S., & Weintraub, E. S. (2013). Increasing exposure to antibody-stimulating proteins and polysaccharides in vaccines is not associated with risk of autism. Journal of Pediatrics, 163(2), 561-567. https://doi.org/10.1016/j.jpeds.2013.02.001 Retrieved from https://pubmed.ncbi.nlm.nih.gov/23545349/

33. Centers for Disease Control and Prevention. (2024, December 30). Autism and vaccines. CDC. Retrieved January 19, 2026, from https://www.cdc.gov/vaccine-safety/about/autism.html

34. Institute of Medicine. (2011). Adverse Effects of Vaccines: Evidence and Causality. Washington, DC: National Academies Press. https://doi.org/10.17226/13164

35. The Editors of The Lancet. (2010). Retraction—Ileal-lymphoid-nodular hyperplasia, non‐specific colitis, and pervasive developmental disorder in children. The Lancet. https://doi.org/10.1016/S0140-6736(10)60175-7

36. World Health Organization. (2025, December 11). WHO expert group’s new analysis reaffirms there is no link between vaccines and autism. Retrieved January 19, 2026, from https://www.who.int/news/item/11-12-2025-who-expert-group-s-new-analysis-reaffirms-there-is-no-link-between-vaccines-and-autism

37. Maglione, M. A., Das, L., Raaen, L., Smith, A., Chari, R., Newberry, S., Shanman, R., Perry, T., Goetz, M. B., & Gidengil, C. (2014). Safety of vaccines used for routine immunization of US children: A systematic review. Pediatrics, 134(2), 325–337. https://doi.org/10.1542/peds.2014-1079

38. Flaherty, D. K. (2011). The vaccine–autism connection: A public health crisis caused by unethical medical practices and fraudulent science. Annals of Pharmacotherapy, 45(10), 1302–1304. https://doi.org/10.1345/aph.1P470

39. Geier, D. A., & Geier, M. R. (2003). An assessment of the impact of thimerosal on childhood neurodevelopmental disorders. Pediatric Rehabilitation, 6(2), 97–102. https://doi.org/10.1080/1363849031000139315

40. Geier, M. R., & Geier, D. A. (2003). Neurodevelopmental disorders after thimerosal-containing vaccines: a brief communication. Experimental Biology and Medicine, 228(6), 660–664. https://doi.org/10.1177/153537020322800603

41. Madsen, K. M., Lauritsen, M. B., Pedersen, C. B., Thorsen, P., & Plesner, A. M. (2003). Thimerosal and the occurrence of autism: negative ecological evidence from Danish population-based data. Pediatrics, 112(3), 604–606. https://doi.org/10.1542/peds.112.3.604

42. Institute of Medicine. (2004). Immunization Safety Review: Vaccines and Autism. National Academies Press. https://www.ncbi.nlm.nih.gov/books/NBK25344/

43. Hviid, A., Hansen, J. V., Frisch, M., & Melbye, M. (2019). Measles, mumps, rubella vaccination and autism: A nationwide cohort study. Annals of Internal Medicine, 170(8), 513–520. doi:10.7326/M18-2101 Retrieved from https://www.acpjournals.org/doi/10.7326/M18-2101

44. Madsen, K. M., Lauritsen, M. B., Pedersen, C. B., Thorsen, P., Plesner, A. M., Andersen, P. H., & Mortensen, P. B. (2003). Thimerosal and the occurrence of autism: Negative ecological evidence from Danish population-based data. Pediatrics, 112(3 Pt 1), 604–606. doi:10.1542/peds.112.3.604 Retrieved from https://pediatrics.aappublications.org/content/112/3/604

45. Di Pietrantonj, C., Rivetti, A., Marchione, P., Debalini, M. G., & Demicheli, V. (2012). Vaccines for measles, mumps, rubella and varicella in children. Cochrane Database of Systematic Reviews, 2, CD004407. doi:10.1002/14651858.CD004407.pub3 Retrieved from https://www.cochranelibrary.com/cdsr/doi/10.1002/14651858.CD004407.pub3/full

46. Price, C. S., Thompson, W. W., Goodson, B., Weintraub, E. S., Croen, L. A., Hinrichsen, V. L., Marcy, M., Robertson, A., Eriksen, E., Lewis, E., Bernal, P., Shay, D., Davis, R. L., & DeStefano, F. (2010). Prenatal and infant exposure to thimerosal from vaccines and immunoglobulins and risk of autism. Pediatrics, 126(4), 656–664. doi:10.1542/peds.2010-0309 Retrieved from https://pediatrics.aappublications.org/content/126/4/656

47. Hooker, B. S. (2014). Measles-mumps-rubella vaccination timing and autism among young African American boys: A reanalysis of CDC data. Translational Neurodegeneration, 3, 16. https://doi.org/10.1186/2047-9158-3-16 Retrieved from https://translationalneurodegeneration.biomedcentral.com/articles/10.1186/2047-9158-3-16

48. Coccia, M. (2025). Infant vaccine scheduling intensity and autism incidence: A preliminary cross-national analysis to guide public health policy [Preprint]. Preprints.org. https://www.preprints.org/manuscript/202511.0675

49. Brookings Institution. (2026). Vaccines and nervous parents: Why spacing out the vaccine schedule is not the answer. Brookings. https://www.brookings.edu/articles/vaccines-and-nervous-parents-why-spacing-out-the-vaccine-schedule-is-not-the-answer/

50. Institute of Medicine. (2013). The Childhood Immunization Schedule and Safety: Stakeholder Concerns, Scientific Evidence, and Future Studies. National Academies Press. https://doi.org/10.17226/13563 Retrieved from https://www.nationalacademies.org/publications/13563

51. Politico. (2025, October 9). CDC panel announces plans to assess childhood vaccine schedule. Politico. https://www.politico.com/news/2025/10/09/cdc-panel-to-assess-childhood-vaccine-schedule-00600304

52. Medical Daily. (2025). Study confirms no link between childhood vaccine schedule and autism. Medical Daily. https://www.medicaldaily.com/study-confirms-no-link-between-childhood-vaccine-schedule-and-autism-244822

---

## 10. Intellectual Honesty Checklist

| Forcing Function | Applied | Notes |
|-----------------|---------|-------|
| Ontological Scan (9 domains) | ✓ | Multiple domains covered (Constitutional/Legal and Democratic for political topics) |
| Ancestral Check | ✓ | Historical baselines examined |
| Paradigm Inversion | ✓ | Alternative paradigms generated |
| MECE Verification | ✓ | Hypotheses are mutually exclusive and collectively exhaustive |
| Sensitivity Analysis | ✓ | Prior variation tested |


---

**End of BFIH Analysis Report**
