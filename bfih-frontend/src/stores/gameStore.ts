// Core game state management

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type {
  ScenarioConfig,
  BFIHAnalysisResult,
  GamePhase,
  Paradigm,
  Hypothesis,
  EvidenceCluster,
} from '../types';

interface GameState {
  // Scenario data
  scenarioId: string | null;
  scenarioConfig: ScenarioConfig | null;
  analysisResult: BFIHAnalysisResult | null;

  // Game progression
  currentPhase: GamePhase;
  currentEvidenceRound: number;
  totalEvidenceRounds: number;
  isGameActive: boolean;

  // Paradigm selection
  homeParadigm: string | null; // Player's chosen "home" paradigm
  activeParadigm: string; // Currently viewing paradigm
  selectedParadigms: string[]; // Paradigms player has selected

  // Computed getters
  getParadigms: () => Paradigm[];
  getHypotheses: () => Hypothesis[];
  getEvidenceClusters: () => EvidenceCluster[];
  getCurrentCluster: () => EvidenceCluster | null;
  getPriors: (paradigmId?: string) => Record<string, number>;
  getPosteriors: (paradigmId?: string) => Record<string, number>;

  // Actions
  initGame: (scenarioConfig: ScenarioConfig, analysisResult?: BFIHAnalysisResult) => void;
  loadScenario: (scenarioConfig: ScenarioConfig) => void;
  setAnalysisResult: (result: BFIHAnalysisResult) => void;
  setPhase: (phase: GamePhase) => void;
  advancePhase: () => void;
  advanceEvidenceRound: () => void;
  selectHomeParadigm: (paradigmId: string) => void;
  setActiveParadigm: (paradigmId: string) => void;
  toggleParadigm: (paradigmId: string) => void;
  resetGame: () => void;
}

const PHASE_ORDER: GamePhase[] = [
  'setup',
  'hypotheses',
  'priors',
  'betting',
  'evidence',
  'resolution',
  'report',
  'debrief',
];

export const useGameStore = create<GameState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        scenarioId: null,
        scenarioConfig: null,
        analysisResult: null,
        currentPhase: 'setup',
        currentEvidenceRound: 0,
        totalEvidenceRounds: 0,
        isGameActive: false,
        homeParadigm: null,
        activeParadigm: 'K1',
        selectedParadigms: [],

        // Getters
        getParadigms: () => {
          const config = get().scenarioConfig;
          return config?.paradigms || [];
        },

        getHypotheses: () => {
          const config = get().scenarioConfig;
          return config?.hypotheses || [];
        },

        getEvidenceClusters: () => {
          const config = get().scenarioConfig;
          return config?.evidence?.clusters || [];
        },

        getCurrentCluster: () => {
          const { currentEvidenceRound, scenarioConfig } = get();
          const clusters = scenarioConfig?.evidence?.clusters || [];
          return clusters[currentEvidenceRound] || null;
        },

        getPriors: (paradigmId?: string) => {
          const { scenarioConfig, activeParadigm } = get();
          const pid = paradigmId || activeParadigm;
          return scenarioConfig?.priors_by_paradigm?.[pid] || {};
        },

        getPosteriors: (paradigmId?: string) => {
          const { analysisResult, activeParadigm } = get();
          const pid = paradigmId || activeParadigm;
          return analysisResult?.posteriors?.[pid] || {};
        },

        // Actions
        initGame: (scenarioConfig, analysisResult) => {
          const totalRounds = scenarioConfig.evidence_clusters?.length || 0;
          const paradigmIds = scenarioConfig.paradigms?.map((p) => p.id) || [];
          const firstParadigm = paradigmIds[0] || 'K1';

          set({
            scenarioId: scenarioConfig.scenario_id,
            scenarioConfig,
            analysisResult: analysisResult || null,
            currentPhase: 'setup',
            currentEvidenceRound: 0,
            totalEvidenceRounds: totalRounds,
            isGameActive: true,
            homeParadigm: null,
            activeParadigm: firstParadigm,
            selectedParadigms: paradigmIds,
          });
        },

        loadScenario: (scenarioConfig) => {
          const totalRounds = scenarioConfig.evidence_clusters?.length || 0;
          const paradigmIds = scenarioConfig.paradigms?.map((p) => p.id) || [];
          const firstParadigm = paradigmIds[0] || 'K1';

          set({
            scenarioId: scenarioConfig.scenario_id,
            scenarioConfig,
            currentPhase: 'setup',
            currentEvidenceRound: 0,
            totalEvidenceRounds: totalRounds,
            isGameActive: true,
            homeParadigm: null,
            activeParadigm: firstParadigm,
            selectedParadigms: paradigmIds,
          });
        },

        setAnalysisResult: (result) => {
          set({ analysisResult: result });
        },

        setPhase: (phase) => {
          set({ currentPhase: phase });
        },

        advancePhase: () => {
          const { currentPhase } = get();
          const currentIndex = PHASE_ORDER.indexOf(currentPhase);

          if (currentIndex < PHASE_ORDER.length - 1) {
            set({ currentPhase: PHASE_ORDER[currentIndex + 1] });
          }
        },

        advanceEvidenceRound: () => {
          const { currentEvidenceRound, totalEvidenceRounds } = get();

          if (currentEvidenceRound < totalEvidenceRounds - 1) {
            set({ currentEvidenceRound: currentEvidenceRound + 1 });
          } else {
            // All evidence rounds complete, advance to resolution
            set({
              currentPhase: 'resolution',
              currentEvidenceRound: totalEvidenceRounds - 1,
            });
          }
        },

        selectHomeParadigm: (paradigmId) => {
          set({
            homeParadigm: paradigmId,
            activeParadigm: paradigmId,
          });
        },

        setActiveParadigm: (paradigmId) => {
          set({ activeParadigm: paradigmId });
        },

        toggleParadigm: (paradigmId) => {
          const { selectedParadigms } = get();
          const isSelected = selectedParadigms.includes(paradigmId);

          if (isSelected) {
            // Don't allow deselecting if only one paradigm selected
            if (selectedParadigms.length > 1) {
              set({
                selectedParadigms: selectedParadigms.filter((id) => id !== paradigmId),
              });
            }
          } else {
            set({
              selectedParadigms: [...selectedParadigms, paradigmId],
            });
          }
        },

        resetGame: () => {
          set({
            scenarioId: null,
            scenarioConfig: null,
            analysisResult: null,
            currentPhase: 'setup',
            currentEvidenceRound: 0,
            totalEvidenceRounds: 0,
            isGameActive: false,
            homeParadigm: null,
            activeParadigm: 'K1',
            selectedParadigms: [],
          });
        },
      }),
      {
        name: 'bfih-game-store',
        partialize: (state) => ({
          scenarioId: state.scenarioId,
          scenarioConfig: state.scenarioConfig,  // Persist full config
          analysisResult: state.analysisResult,  // Persist analysis result
          currentPhase: state.currentPhase,
          currentEvidenceRound: state.currentEvidenceRound,
          totalEvidenceRounds: state.totalEvidenceRounds,
          isGameActive: state.isGameActive,
          homeParadigm: state.homeParadigm,
          activeParadigm: state.activeParadigm,
          selectedParadigms: state.selectedParadigms,
        }),
      }
    ),
    { name: 'GameStore' }
  )
);
