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
  Competitor,
  LeaderboardEntry,
} from '../types';
import {
  getPersonaForParadigm,
  calculatePersonaBets,
} from '../types';

interface GameState {
  // Scenario data
  scenarioId: string | null;
  scenarioConfig: ScenarioConfig | null;
  analysisResult: BFIHAnalysisResult | null;

  // Game progression
  currentPhase: GamePhase;
  furthestPhase: GamePhase; // Track the furthest phase visited for navigation
  currentEvidenceRound: number;
  totalEvidenceRounds: number;
  isGameActive: boolean;

  // Paradigm selection
  homeParadigm: string | null; // Player's chosen "home" paradigm
  activeParadigm: string; // Currently viewing paradigm
  selectedParadigms: string[]; // Paradigms player has selected

  // Competitors (player + paradigm personas)
  competitors: Competitor[];
  playerPayoff: number | null;

  // Computed getters
  getParadigms: () => Paradigm[];
  getHypotheses: () => Hypothesis[];
  getEvidenceClusters: () => EvidenceCluster[];
  getCurrentCluster: () => EvidenceCluster | null;
  getPriors: (paradigmId?: string) => Record<string, number>;
  getPosteriors: (paradigmId?: string) => Record<string, number>;
  getLeaderboard: () => LeaderboardEntry[];

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
  initializeCompetitors: (playerBets: Record<string, number>, budget: number) => void;
  calculateAllPayoffs: (posteriors: Record<string, number>, priors: Record<string, number>) => void;
  updatePlayerBets: (bets: Record<string, number>) => void;
  clearScenarioCache: (scenarioIdToClear?: string) => void;
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
        furthestPhase: 'setup',
        currentEvidenceRound: 0,
        totalEvidenceRounds: 0,
        isGameActive: false,
        homeParadigm: null,
        activeParadigm: 'K1',
        selectedParadigms: [],
        competitors: [],
        playerPayoff: null,

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
          // Support both evidence.clusters and evidence_clusters field names
          return config?.evidence_clusters || config?.evidence?.clusters || [];
        },

        getCurrentCluster: () => {
          const { currentEvidenceRound, scenarioConfig } = get();
          // Support both field names
          const clusters = scenarioConfig?.evidence_clusters || scenarioConfig?.evidence?.clusters || [];
          return clusters[currentEvidenceRound] || null;
        },

        getPriors: (paradigmId?: string) => {
          const { scenarioConfig, activeParadigm } = get();
          const pid = paradigmId || activeParadigm;
          // Support both priors and priors_by_paradigm field names
          const priorsSource = scenarioConfig?.priors || scenarioConfig?.priors_by_paradigm;
          const paradigmPriors = priorsSource?.[pid] || {};
          // Normalize: extract probability from object if needed
          const result: Record<string, number> = {};
          for (const [hypId, prior] of Object.entries(paradigmPriors)) {
            result[hypId] = typeof prior === 'number' ? prior : (prior as { probability: number })?.probability || 0;
          }
          return result;
        },

        getPosteriors: (paradigmId?: string) => {
          const { analysisResult, activeParadigm } = get();
          const pid = paradigmId || activeParadigm;
          return analysisResult?.posteriors?.[pid] || {};
        },

        getLeaderboard: () => {
          const { competitors } = get();
          if (competitors.length === 0) return [];

          // Sort by payoff descending
          const sorted = [...competitors].sort((a, b) => b.payoff - a.payoff);

          // Assign ranks (handling ties)
          return sorted.map((competitor, index) => ({
            ...competitor,
            rank: index + 1,
          }));
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
            furthestPhase: 'setup',
            currentEvidenceRound: 0,
            totalEvidenceRounds: totalRounds,
            isGameActive: true,
            homeParadigm: null,
            activeParadigm: firstParadigm,
            selectedParadigms: paradigmIds,
          });
        },

        loadScenario: (scenarioConfig) => {
          const totalRounds = scenarioConfig.evidence_clusters?.length || scenarioConfig.evidence?.clusters?.length || 0;
          const paradigmIds = scenarioConfig.paradigms?.map((p) => p.id) || [];
          const firstParadigm = paradigmIds[0] || 'K1';

          // Determine furthestPhase based on available data
          // For completed scenarios from library, allow navigation to all phases
          const hasEvidence = totalRounds > 0 || (scenarioConfig.evidence?.items?.length || 0) > 0;
          const hasPriors = Object.keys(scenarioConfig.priors_by_paradigm || {}).length > 0;
          const hasHypotheses = (scenarioConfig.hypotheses?.length || 0) > 0;

          let furthestPhase: GamePhase = 'setup';
          if (hasHypotheses) furthestPhase = 'hypotheses';
          if (hasPriors) furthestPhase = 'priors';
          if (hasEvidence) furthestPhase = 'report'; // Allow jumping to report for completed scenarios

          set({
            scenarioId: scenarioConfig.scenario_id,
            scenarioConfig,
            currentPhase: 'setup',
            furthestPhase,
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
          const { furthestPhase } = get();
          const phaseIndex = PHASE_ORDER.indexOf(phase);
          const furthestIndex = PHASE_ORDER.indexOf(furthestPhase);

          // Update furthestPhase if we're advancing beyond it
          if (phaseIndex > furthestIndex) {
            set({ currentPhase: phase, furthestPhase: phase });
          } else {
            set({ currentPhase: phase });
          }
        },

        advancePhase: () => {
          const { currentPhase, furthestPhase } = get();
          const currentIndex = PHASE_ORDER.indexOf(currentPhase);
          const furthestIndex = PHASE_ORDER.indexOf(furthestPhase);

          if (currentIndex < PHASE_ORDER.length - 1) {
            const nextPhase = PHASE_ORDER[currentIndex + 1];
            const nextIndex = currentIndex + 1;

            // Update furthestPhase if advancing beyond it
            if (nextIndex > furthestIndex) {
              set({ currentPhase: nextPhase, furthestPhase: nextPhase });
            } else {
              set({ currentPhase: nextPhase });
            }
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

        initializeCompetitors: (playerBets, budget) => {
          const { scenarioConfig, homeParadigm } = get();
          if (!scenarioConfig) return;

          const competitors: Competitor[] = [];
          const priorsSource = scenarioConfig.priors || scenarioConfig.priors_by_paradigm || {};

          // Add player as first competitor
          competitors.push({
            id: 'player',
            name: 'You',
            icon: '🎮',
            description: 'Human player',
            bets: { ...playerBets },
            payoff: 0,
            isPlayer: true,
          });

          // Add paradigm personas (excluding player's home paradigm if they chose one)
          for (const paradigm of scenarioConfig.paradigms || []) {
            // Skip player's home paradigm to avoid duplicate betting strategy
            if (homeParadigm && paradigm.id === homeParadigm) continue;

            const persona = getPersonaForParadigm(paradigm.id, paradigm.name);
            const paradigmPriors = priorsSource[paradigm.id] || {};

            // Extract probabilities from priors (handle both formats)
            const priorProbs: Record<string, number> = {};
            for (const [hypId, prior] of Object.entries(paradigmPriors)) {
              priorProbs[hypId] = typeof prior === 'number' ? prior : (prior as { probability: number })?.probability || 0;
            }

            const personaBets = calculatePersonaBets(priorProbs, budget);

            competitors.push({
              id: paradigm.id,
              name: persona.name,
              icon: persona.icon,
              description: persona.description,
              bets: personaBets,
              payoff: 0,
              isPlayer: false,
            });
          }

          set({ competitors });
        },

        calculateAllPayoffs: (posteriors, priors) => {
          const { competitors, scenarioConfig } = get();
          if (competitors.length === 0 || !scenarioConfig) return;

          const hypotheses = scenarioConfig.hypotheses || [];

          // Find the winner (highest posterior)
          let winnerId = '';
          let maxPosterior = -1;
          for (const h of hypotheses) {
            const post = posteriors[h.id] || 0;
            if (post > maxPosterior) {
              maxPosterior = post;
              winnerId = h.id;
            }
          }

          // Calculate payoffs for each competitor using odds_against formula
          const updatedCompetitors = competitors.map((competitor) => {
            let totalPayoff = 0;

            for (const hypothesis of hypotheses) {
              const bet = competitor.bets[hypothesis.id] || 0;
              const prior = priors[hypothesis.id] || 0.01; // Avoid division by zero
              const isWinner = hypothesis.id === winnerId;

              if (isWinner) {
                // Payoff = (bet / prior) - bet for the winning hypothesis
                totalPayoff += (bet / prior) - bet;
              } else {
                // Lose the bet on non-winning hypotheses
                totalPayoff -= bet;
              }
            }

            return {
              ...competitor,
              payoff: Math.round(totalPayoff * 100) / 100, // Round to 2 decimal places
            };
          });

          // Find player payoff
          const playerCompetitor = updatedCompetitors.find((c) => c.isPlayer);

          set({
            competitors: updatedCompetitors,
            playerPayoff: playerCompetitor?.payoff || null,
          });
        },

        updatePlayerBets: (bets) => {
          const { competitors } = get();
          const updated = competitors.map((c) =>
            c.isPlayer ? { ...c, bets: { ...bets } } : c
          );
          set({ competitors: updated });
        },

        clearScenarioCache: (scenarioIdToClear) => {
          const { scenarioId } = get();
          // Clear cache if no specific ID given, or if it matches
          if (!scenarioIdToClear || scenarioId === scenarioIdToClear) {
            set({
              scenarioId: null,
              scenarioConfig: null,
              analysisResult: null,
              competitors: [],  // Clear stale competitors with old bets
              playerPayoff: null,
            });
          }
        },

        resetGame: () => {
          set({
            scenarioId: null,
            scenarioConfig: null,
            analysisResult: null,
            currentPhase: 'setup',
            furthestPhase: 'setup',
            currentEvidenceRound: 0,
            totalEvidenceRounds: 0,
            isGameActive: false,
            homeParadigm: null,
            activeParadigm: 'K1',
            selectedParadigms: [],
            competitors: [],
            playerPayoff: null,
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
          furthestPhase: state.furthestPhase,  // Persist furthest visited phase
          currentEvidenceRound: state.currentEvidenceRound,
          totalEvidenceRounds: state.totalEvidenceRounds,
          isGameActive: state.isGameActive,
          homeParadigm: state.homeParadigm,
          activeParadigm: state.activeParadigm,
          selectedParadigms: state.selectedParadigms,
          competitors: state.competitors,  // Persist competitors for leaderboard
          playerPayoff: state.playerPayoff,
        }),
      }
    ),
    { name: 'GameStore' }
  )
);
