// Analysis API endpoints

import { get, post, isSetupComplete, checkHealth } from './client';
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
  // Check if server requires API key from user
  const health = await checkHealth();

  // Only require user setup if server doesn't have its own API key
  if (health.requiresApiKey && !isSetupComplete()) {
    // Clear any stale credentials and force setup
    localStorage.removeItem('bfih_openai_api_key');
    localStorage.removeItem('bfih_vector_store_id');
    localStorage.removeItem('bfih_setup_complete');
    window.location.href = '/';
    throw new Error('API key not configured. Please complete setup.');
  }

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

// Get analysis status (for polling) - uses cache busting to ensure fresh data
export async function getAnalysisStatus(analysisId: string): Promise<AnalysisStatusResponse> {
  const response = await get<AnalysisStatusResponse>(`/api/analysis-status/${analysisId}`, true);

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

        // Check for auth error - redirect to setup immediately
        if (status.status?.toLowerCase().startsWith('auth_error')) {
          localStorage.removeItem('bfih_openai_api_key');
          localStorage.removeItem('bfih_vector_store_id');
          localStorage.removeItem('bfih_setup_complete');
          window.location.href = '/';
          reject(new Error('Invalid API key. Please reconfigure.'));
          return;
        }

        if (status.status === 'failed' || status.status?.toLowerCase().startsWith('failed')) {
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
