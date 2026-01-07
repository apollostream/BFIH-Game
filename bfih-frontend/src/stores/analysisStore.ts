// Analysis management state

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { BFIHAnalysisResult, AnalysisStatusResponse } from '../types';
import {
  submitAnalysis,
  getAnalysisStatus,
  getAnalysis,
} from '../api';

type AnalysisStatusType = 'idle' | 'submitting' | 'processing' | 'completed' | 'failed' | string;

interface AnalysisState {
  // Current analysis
  pendingAnalysisId: string | null;
  status: AnalysisStatusType;
  analysisStatus: string | null; // Current phase status from backend
  currentAnalysis: BFIHAnalysisResult | null;
  progress: number; // 0-100 estimated progress
  errorMessage: string | null;
  error: string | null; // Alias for errorMessage
  estimatedSeconds: number | null;
  startTime: number | null;
  isSubmitting: boolean;
  isPolling: boolean;

  // Polling
  pollIntervalId: number | null;

  // Cached results
  cachedResults: Record<string, BFIHAnalysisResult>;

  // Actions
  submitNewAnalysis: (proposition: string) => Promise<string | null>;
  startPolling: (analysisId: string) => void;
  stopPolling: () => void;
  updateStatus: (status: AnalysisStatusResponse) => void;
  getCachedResult: (analysisId: string) => BFIHAnalysisResult | null;
  cacheResult: (result: BFIHAnalysisResult) => void;
  reset: () => void;
}

const POLL_INTERVAL = 3000; // 3 seconds

export const useAnalysisStore = create<AnalysisState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        pendingAnalysisId: null,
        status: 'idle' as AnalysisStatusType,
        analysisStatus: null,
        currentAnalysis: null,
        progress: 0,
        errorMessage: null,
        error: null,
        estimatedSeconds: null,
        startTime: null,
        isSubmitting: false,
        isPolling: false,
        pollIntervalId: null,
        cachedResults: {},

        // Actions
        submitNewAnalysis: async (proposition) => {
        set({
          status: 'submitting',
          isSubmitting: true,
          progress: 0,
          errorMessage: null,
          error: null,
          startTime: Date.now(),
        });

        try {
          const response = await submitAnalysis({ proposition });

          set({
            pendingAnalysisId: response.analysis_id,
            status: 'processing',
            analysisStatus: 'pending',
            estimatedSeconds: response.estimated_seconds,
            progress: 5,
            isSubmitting: false,
          });

          return response.analysis_id;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Submission failed';
          set({
            status: 'failed',
            errorMessage: message,
            error: message,
            isSubmitting: false,
          });
          return null;
        }
      },

      startPolling: (analysisId) => {
        const { pollIntervalId } = get();

        // Clear existing interval
        if (pollIntervalId !== null) {
          clearInterval(pollIntervalId);
        }

        set({ pendingAnalysisId: analysisId, isPolling: true });

        const intervalId = window.setInterval(async () => {
          const { pendingAnalysisId: currentId, status } = get();

          if (!currentId || status === 'completed' || status === 'failed') {
            get().stopPolling();
            return;
          }

          try {
            const statusResponse = await getAnalysisStatus(currentId);
            get().updateStatus(statusResponse);

            if (statusResponse.status === 'completed') {
              // Fetch the full result
              const result = await getAnalysis(currentId);
              get().cacheResult(result);
              // Set both status and analysis atomically to ensure useEffect triggers
              set({
                currentAnalysis: result,
                status: 'completed',
                analysisStatus: 'completed',
                progress: 100
              });
              get().stopPolling();
            } else if (statusResponse.status?.startsWith('failed')) {
              set({
                status: 'failed',
                analysisStatus: 'failed',
                errorMessage: statusResponse.status,
                error: statusResponse.status
              });
              get().stopPolling();
            }
          } catch (error) {
            console.error('Polling error:', error);
          }
        }, POLL_INTERVAL);

        set({ pollIntervalId: intervalId });
      },

      stopPolling: () => {
        const { pollIntervalId } = get();
        if (pollIntervalId !== null) {
          clearInterval(pollIntervalId);
          set({ pollIntervalId: null, isPolling: false });
        }
      },

      updateStatus: (statusResponse) => {
        const { startTime, estimatedSeconds } = get();

        let progress = 5;
        if (startTime && estimatedSeconds) {
          const elapsed = (Date.now() - startTime) / 1000;
          progress = Math.min(95, (elapsed / estimatedSeconds) * 100);
        }

        // Update analysisStatus with the current phase
        set({ analysisStatus: statusResponse.status });

        if (statusResponse.status === 'completed') {
          set({
            status: 'completed',
            analysisStatus: 'completed',
            progress: 100,
          });
        } else if (statusResponse.status === 'failed') {
          const errorMsg = statusResponse.error || 'Analysis failed';
          set({
            status: 'failed',
            analysisStatus: 'failed',
            errorMessage: errorMsg,
            error: errorMsg,
            progress: 0,
          });
        } else {
          set({ progress });
        }
      },

      getCachedResult: (analysisId) => {
        return get().cachedResults[analysisId] || null;
      },

      cacheResult: (result) => {
        set((state) => ({
          currentAnalysis: result,
          cachedResults: {
            ...state.cachedResults,
            [result.analysis_id]: result,
          },
        }));
      },

      reset: () => {
        get().stopPolling();
        set({
          pendingAnalysisId: null,
          status: 'idle',
          analysisStatus: null,
          currentAnalysis: null,
          progress: 0,
          errorMessage: null,
          error: null,
          estimatedSeconds: null,
          startTime: null,
          isSubmitting: false,
          isPolling: false,
        });
      },
      }),
      {
        name: 'bfih-analysis-store',
        partialize: (state) => ({
          // Persist analysis results so they survive navigation
          currentAnalysis: state.currentAnalysis,
          cachedResults: state.cachedResults,
          status: state.status,
        }),
      }
    ),
    { name: 'AnalysisStore' }
  )
);
