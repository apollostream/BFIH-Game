// Scenario API endpoints

import { get, post } from './client';
import type { ScenarioConfig, ScenarioListResponse, ScenarioSummary } from '../types';

// List all scenarios
export async function listScenarios(
  limit: number = 50,
  offset: number = 0
): Promise<ScenarioListResponse> {
  const response = await get<ScenarioListResponse>(
    `/api/scenarios/list?limit=${limit}&offset=${offset}`
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

// Get a specific scenario
export async function getScenario(scenarioId: string): Promise<ScenarioConfig> {
  const response = await get<ScenarioConfig>(`/api/scenario/${scenarioId}`);

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

// Store a new scenario
export async function storeScenario(scenario: {
  scenario_id: string;
  title: string;
  domain: string;
  difficulty_level: string;
  scenario_config: ScenarioConfig;
}): Promise<{ scenario_id: string; status: string; created_at: string }> {
  const response = await post<{ scenario_id: string; status: string; created_at: string }>(
    '/api/scenario',
    scenario
  );

  if (response.error) {
    throw new Error(response.error);
  }

  return response.data!;
}

// Search scenarios by domain
export async function searchScenariosByDomain(
  domain: string,
  limit: number = 20
): Promise<ScenarioSummary[]> {
  const response = await listScenarios(limit, 0);
  return response.scenarios.filter(s =>
    s.domain.toLowerCase() === domain.toLowerCase()
  );
}

// Get recent scenarios
export async function getRecentScenarios(limit: number = 5): Promise<ScenarioSummary[]> {
  const response = await listScenarios(limit, 0);
  return response.scenarios;
}
