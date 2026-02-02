// Evidence Prediction state management

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type {
  ClusterPrediction,
  PredictionResult,
  PredictionConfidence,
} from '../types';
import { PREDICTION_POINTS } from '../types';
import type { EvidenceCluster } from '../types/scenario';

interface PredictionState {
  // Scenario tracking (to reset predictions when switching scenarios)
  scenarioId: string | null;

  // Predictions by cluster ID
  predictions: Record<string, ClusterPrediction>;
  submitted: boolean;

  // Results (calculated after evidence revealed)
  results: PredictionResult[];
  totalBonus: number;

  // Getters
  getPrediction: (clusterId: string) => ClusterPrediction | null;
  hasPredictions: () => boolean;
  getPredictionCount: () => number;

  // Actions
  initializeForScenario: (scenarioId: string) => void;
  setPrediction: (
    clusterId: string,
    hypothesisId: string | null,
    confidence: PredictionConfidence
  ) => void;
  submitPredictions: () => void;
  calculateResults: (
    clusters: EvidenceCluster[],
    paradigmId: string
  ) => void;
  reset: () => void;
}

/**
 * Determine which hypothesis a cluster most supports based on Bayesian metrics.
 * Returns the hypothesis ID with the highest positive WoE, or null if mixed/neutral.
 */
function getClusterWinner(
  cluster: EvidenceCluster,
  paradigmId: string
): string | null {
  // Try paradigm-specific metrics first
  const metrics = cluster.bayesian_metrics_by_paradigm?.[paradigmId]
    || cluster.bayesian_metrics;

  if (!metrics) {
    // Fall back to likelihoods if no metrics
    const likelihoods = cluster.likelihoods_by_paradigm?.[paradigmId]
      || cluster.likelihoods;

    if (!likelihoods) return null;

    // Find hypothesis with highest likelihood
    let maxProb = 0.5; // Threshold: must be > 0.5 to be considered "supporting"
    let winner: string | null = null;

    for (const [hypId, likelihood] of Object.entries(likelihoods)) {
      const prob = typeof likelihood === 'number'
        ? likelihood
        : likelihood.probability;
      if (prob > maxProb) {
        maxProb = prob;
        winner = hypId;
      }
    }
    return winner;
  }

  // Find hypothesis with highest positive WoE (weight of evidence)
  let maxWoe = 1; // Threshold: WoE > 1 deciban to count as support
  let winner: string | null = null;

  for (const [hypId, m] of Object.entries(metrics)) {
    if (m.woe > maxWoe) {
      maxWoe = m.woe;
      winner = hypId;
    }
  }

  return winner;
}

/**
 * Calculate points for a single prediction
 */
function calculatePredictionPoints(
  predicted: string | null,
  actual: string | null,
  confidence: PredictionConfidence
): number {
  const correct = predicted === actual;

  if (correct) {
    return confidence === 'high'
      ? PREDICTION_POINTS.correctHighConfidence
      : PREDICTION_POINTS.correct;
  } else {
    return confidence === 'high'
      ? PREDICTION_POINTS.wrongHighConfidence
      : PREDICTION_POINTS.wrong;
  }
}

export const usePredictionStore = create<PredictionState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        scenarioId: null,
        predictions: {},
        submitted: false,
        results: [],
        totalBonus: 0,

        // Getters
        getPrediction: (clusterId) => {
          return get().predictions[clusterId] || null;
        },

        hasPredictions: () => {
          return Object.keys(get().predictions).length > 0;
        },

        getPredictionCount: () => {
          return Object.keys(get().predictions).length;
        },

        // Actions
        initializeForScenario: (scenarioId) => {
          const currentScenarioId = get().scenarioId;
          // Only reset if switching to a different scenario
          if (currentScenarioId === scenarioId) {
            return; // Same scenario, keep existing predictions
          }
          // New scenario - reset everything
          set({
            scenarioId,
            predictions: {},
            submitted: false,
            results: [],
            totalBonus: 0,
          });
        },

        setPrediction: (clusterId, hypothesisId, confidence) => {
          const { predictions, submitted } = get();

          if (submitted) {
            console.warn('Predictions are already submitted');
            return;
          }

          set({
            predictions: {
              ...predictions,
              [clusterId]: {
                clusterId,
                predictedSupports: hypothesisId,
                confidence,
              },
            },
          });
        },

        submitPredictions: () => {
          set({ submitted: true });
        },

        calculateResults: (clusters, paradigmId) => {
          const { predictions } = get();
          const results: PredictionResult[] = [];
          let totalBonus = 0;

          for (const cluster of clusters) {
            const prediction = predictions[cluster.cluster_id];
            const actual = getClusterWinner(cluster, paradigmId);
            const predicted = prediction?.predictedSupports ?? null;
            const confidence = prediction?.confidence ?? 'medium';

            const points = calculatePredictionPoints(predicted, actual, confidence);
            totalBonus += points;

            results.push({
              clusterId: cluster.cluster_id,
              clusterName: cluster.cluster_name,
              predicted,
              actual,
              correct: predicted === actual,
              confidence,
              points,
            });
          }

          set({
            results,
            totalBonus: Math.max(0, totalBonus), // Floor at 0
          });
        },

        reset: () => {
          set({
            scenarioId: null,
            predictions: {},
            submitted: false,
            results: [],
            totalBonus: 0,
          });
        },
      }),
      {
        name: 'bfih-prediction-store',
        partialize: (state) => ({
          scenarioId: state.scenarioId,
          predictions: state.predictions,
          submitted: state.submitted,
          results: state.results,
          totalBonus: state.totalBonus,
        }),
      }
    ),
    { name: 'PredictionStore' }
  )
);
