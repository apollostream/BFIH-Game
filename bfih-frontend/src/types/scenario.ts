// Scenario configuration types matching backend JSON schema

export interface ScenarioMetadata {
  scenario_id: string;
  title: string;
  description: string;
  domain: string;
  difficulty_level: 'easy' | 'medium' | 'hard';
  created_date: string;
  contributors: string[];
  ground_truth_hypothesis_id: string | null;
}

export interface ScenarioNarrative {
  title: string;
  background: string;
  research_question: string;
  stakes?: string;
  time_horizon?: string;
  key_actors?: string;
}

export interface ParadigmCharacteristics {
  prefers_evidence_types: string[];
  skeptical_of: string[];
  causal_preference: string;
}

export interface Paradigm {
  id: string;
  name: string;
  description: string;
  inverse_paradigm_id: string | null;
  characteristics: ParadigmCharacteristics;
}

export type Domain =
  | 'Biological'
  | 'Economic'
  | 'Cultural'
  | 'Theological'
  | 'Historical'
  | 'Institutional'
  | 'Psychological'
  | 'Technological'
  | 'Constitutional_Legal'
  | 'Democratic';

export type TruthValueType = 'affirm' | 'deny' | 'qualify' | 'other';

export interface Hypothesis {
  id: string;
  name: string;
  narrative?: string;  // Legacy field
  statement?: string;  // Full statement of the hypothesis
  truth_value_type?: TruthValueType;  // What this hypothesis claims
  mechanism_if_true?: string;  // Causal mechanism if true
  testable_predictions?: string[];  // Observable predictions
  domains?: Domain[];  // Ontological domains covered
  associated_paradigms?: string[];  // Associated paradigm IDs
  is_ancestral_solution?: boolean;  // Informed by historical analogues
  is_catch_all?: boolean;  // H0 catch-all hypothesis
  is_paradigm_inversion?: boolean;  // Generated via paradigm inversion
  inverted_from_paradigm?: string;  // Which paradigm's blind spot
}

export interface EvidenceItem {
  evidence_id: string;
  description: string;
  content?: string; // Alias for description
  source_name?: string;  // May be omitted
  source_url?: string;  // May be omitted
  citation_apa?: string;  // May be omitted
  date_accessed?: string;  // May be omitted
  supports_hypotheses?: string[];  // May be omitted
  refutes_hypotheses?: string[];  // May be omitted
  evidence_type?: 'quantitative' | 'qualitative' | 'expert_testimony' | 'historical_analogy' | 'policy' | 'institutional';  // May be omitted
}

export interface ClusterLikelihood {
  probability: number;
  justification: string;
}

export interface EvidenceCluster {
  cluster_id: string;
  cluster_name: string;
  description?: string;  // May be omitted
  evidence_ids?: string[];  // May be omitted if items provided directly
  conditional_independence_justification?: string;  // May be omitted
  likelihoods?: Record<string, ClusterLikelihood>;
  likelihoods_by_paradigm?: Record<string, Record<string, ClusterLikelihood>>;  // Paradigm-specific likelihoods
  // Direct items for clusters that include evidence
  items?: EvidenceItem[];
}

export interface OntologicalDomain {
  hypothesis_id: string | null;
  justification: string;
}

export interface OntologicalScan {
  Biological?: OntologicalDomain;
  Economic?: OntologicalDomain;
  Cultural?: OntologicalDomain;
  Theological?: OntologicalDomain;
  Historical?: OntologicalDomain;
  Institutional?: OntologicalDomain;
  Psychological?: OntologicalDomain;
  // Alternative format
  domains_covered?: string[];
  gaps_identified?: string[];
}

export interface AncestralCheck {
  historical_analogue?: string;
  primary_mechanism?: string;
  hypothesis_id?: string | null;
  justification?: string;
  // Alternative format
  historical_solutions?: string[];
}

export interface ParadigmInversion {
  primary_paradigm?: string;
  inverse_paradigm?: string;
  generated_hypothesis_id?: string;
  quality_assessment?: string;
  // Alternative format
  inverse_hypotheses?: string[];
}

export interface MECESynthesis {
  total_candidates?: number;
  consolidated_to?: number;
  overlaps_resolved?: string[];
  validation?: string;
  // Alternative format
  is_mece?: boolean;
  notes?: string;
}

export interface ForcingFunctionsLog {
  ontological_scan?: OntologicalScan;
  ancestral_check?: AncestralCheck;
  paradigm_inversion?: ParadigmInversion | ParadigmInversion[];
  mece_synthesis?: MECESynthesis;
}

export interface Evidence {
  items: EvidenceItem[];
  clusters: EvidenceCluster[];
  total_items: number;
  total_clusters: number;
}

export interface PriorWithJustification {
  probability: number;
  justification?: string;
}

export interface ScenarioConfig {
  schema_version: string;
  scenario_metadata: ScenarioMetadata;
  scenario_narrative: ScenarioNarrative;
  paradigms: Paradigm[];
  hypotheses: Hypothesis[];
  forcing_functions_log: ForcingFunctionsLog;
  priors_by_paradigm: Record<string, Record<string, number>>;
  evidence: Evidence;

  // Alternative/aliased fields for easier access
  scenario_id?: string;
  proposition?: string;
  narrative?: string;
  priors?: Record<string, Record<string, number | PriorWithJustification>>;
  evidence_clusters?: EvidenceCluster[];
  created_at?: string;
}

// Utility type for paradigm-specific posteriors
export type PosteriorsByParadigm = Record<string, Record<string, number>>;
