// Analysis API endpoints

import { get, post } from './client';
import type {
  AnalysisSubmitResponse,
  AnalysisStatusResponse,
  BFIHAnalysisResult,
  ScenarioConfig,
  ReasoningModelsResponse,
} from '../types';

export interface SubmitAnalysisParams {
  proposition: string;
  scenario_config?: ScenarioConfig;
  user_id?: string;
  reasoning_model?: string;  // Optional model override
}

// Get available reasoning models
export async function getReasoningModels(): Promise<ReasoningModelsResponse> {
  const response = await get<ReasoningModelsResponse>('/api/reasoning-models');

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

// Submit a new analysis (autonomous mode - just proposition)
export async function submitAnalysis(params: SubmitAnalysisParams): Promise<AnalysisSubmitResponse> {
  const body: Record<string, unknown> = {
    scenario_id: `auto_${Date.now().toString(16).slice(-8)}`,
    proposition: params.proposition,
    scenario_config: params.scenario_config || {},
    user_id: params.user_id,
  };

  // Only include reasoning_model if specified
  if (params.reasoning_model) {
    body.reasoning_model = params.reasoning_model;
  }

  const response = await post<AnalysisSubmitResponse>('/api/bfih-analysis', body);

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

// Get analysis status (for polling)
export async function getAnalysisStatus(analysisId: string): Promise<AnalysisStatusResponse> {
  const response = await get<AnalysisStatusResponse>(`/api/analysis-status/${analysisId}`);

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

// Get completed analysis result
export async function getAnalysis(analysisId: string): Promise<BFIHAnalysisResult> {
  const response = await get<BFIHAnalysisResult>(`/api/bfih-analysis/${analysisId}`);

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

// Generate magazine-style synopsis from completed analysis
export interface SynopsisResponse {
  scenario_id: string;
  synopsis: string;
  status: string;
}

export interface GenerateSynopsisParams {
  report: string;
  scenarioId?: string;
}

export async function generateSynopsis(params: GenerateSynopsisParams): Promise<SynopsisResponse> {
  // Use the new endpoint that accepts report content directly
  const response = await post<SynopsisResponse>('/api/generate-synopsis', {
    report: params.report,
    scenario_id: params.scenarioId,
  });

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

// Poll analysis until complete
export async function pollAnalysisUntilComplete(
  analysisId: string,
  onStatusUpdate?: (status: AnalysisStatusResponse) => void,
  intervalMs: number = 3000,
  maxAttempts: number = 100
): Promise<BFIHAnalysisResult> {
  let attempts = 0;

  return new Promise((resolve, reject) => {
    const poll = async () => {
      attempts++;

      if (attempts > maxAttempts) {
        reject(new Error('Analysis polling timed out'));
        return;
      }

      try {
        const status = await getAnalysisStatus(analysisId);
        onStatusUpdate?.(status);

        if (status.status === 'completed') {
          const result = await getAnalysis(analysisId);
          resolve(result);
          return;
        }

        if (status.status === 'failed') {
          reject(new Error(status.error || 'Analysis failed'));
          return;
        }

        // Still processing, poll again
        setTimeout(poll, intervalMs);
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
}
