// API response types

import type { ScenarioConfig, EvidenceItem, EvidenceCluster, PosteriorsByParadigm } from './scenario';

export interface AnalysisSubmitRequest {
  scenario_id: string;
  proposition: string;
  scenario_config: ScenarioConfig;
  user_id?: string;
  reasoning_model?: string;  // Optional reasoning model override
}

// Reasoning model configuration
export interface ReasoningModel {
  id: string;
  name: string;
  description: string;
  cost: 'low' | 'medium' | 'high';
}

export interface ReasoningModelsResponse {
  models: ReasoningModel[];
  default: string;
}

export interface AnalysisSubmitResponse {
  analysis_id: string;
  status: 'processing';
  estimated_seconds: number;
  scenario_id: string;
}

export interface AnalysisStatusResponse {
  analysis_id: string;
  status: 'processing' | 'completed' | 'failed';
  timestamp: string;
  error?: string;
  is_stale?: boolean;  // True if backend hasn't updated status in 5+ minutes
}

export interface AnalysisMetadata {
  model: string;
  phases_completed: number;
  duration_seconds: number;
  user_id: string;
  evidence_items_count: number;
  evidence_clusters_count: number;
  evidence_items: EvidenceItem[];
  evidence_clusters: EvidenceCluster[];
  generated_config?: ScenarioConfig;
  autonomous: boolean;
}

export interface BFIHAnalysisResult {
  analysis_id: string;
  scenario_id: string;
  proposition: string;
  report: string;
  full_report?: string;
  posteriors: PosteriorsByParadigm;
  metadata: AnalysisMetadata;
  scenario_config: ScenarioConfig;
  created_at: string;
}

export interface ScenarioListResponse {
  scenarios: ScenarioSummary[];
  count: number;
  limit: number;
  offset: number;
}

export interface ScenarioSummary {
  scenario_id: string;
  title: string;
  domain: string;
  topic?: string;
  difficulty_level: string;
  created_date: string;
  creator?: string;
  model?: string;
  updated?: string;
}

export interface HealthCheckResponse {
  status: 'healthy';
  timestamp: string;
  service: string;
}

export interface ApiError {
  error: string;
  status_code: number;
  timestamp: string;
}

// Generic API response wrapper
export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  status: number;
}
