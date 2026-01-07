// Game state types

export type GamePhase =
  | 'setup'           // Phase 1: Scenario & Paradigms
  | 'hypotheses'      // Phase 2: Hypothesis Generation
  | 'priors'          // Phase 3: AI Prior Assignment
  | 'betting'         // Phase 4: Initial Player Betting
  | 'evidence'        // Phase 5: Evidence Rounds
  | 'resolution'      // Phase 6: Final Resolution
  | 'report'          // Phase 7: BFIH Report
  | 'debrief';        // Phase 8: Post-Game Analysis

export const GAME_PHASES: GamePhase[] = [
  'setup',
  'hypotheses',
  'priors',
  'betting',
  'evidence',
  'resolution',
  'report',
  'debrief'
];

export const PHASE_LABELS: Record<GamePhase, string> = {
  setup: 'Scenario Setup',
  hypotheses: 'Hypothesis Generation',
  priors: 'Prior Assignment',
  betting: 'Initial Betting',
  evidence: 'Evidence Rounds',
  resolution: 'Resolution',
  report: 'BFIH Report',
  debrief: 'Debrief'
};

export const PHASE_DESCRIPTIONS: Record<GamePhase, string> = {
  setup: 'Review the scenario and select your home paradigm',
  hypotheses: 'Explore the AI-generated hypotheses and forcing functions',
  priors: 'Review the AI-assigned prior probabilities',
  betting: 'Place your initial bets on hypotheses',
  evidence: 'Review evidence and adjust your bets',
  resolution: 'See the final posteriors and payoffs',
  report: 'Read the full BFIH analysis report',
  debrief: 'Analyze your performance and explore what-if scenarios'
};

export interface BetRound {
  roundNumber: number;
  bets: Record<string, number>;
  timestamp: string;
  type: 'initial' | 'raise';
}

export interface PlayerState {
  playerId: string;
  name: string;
  initialBudget: number;
  currentBudget: number;
  bets: Record<string, number>;
  betHistory: BetRound[];
  subjectivePriors: Record<string, number> | null;
  homeParadigm: string | null;
  finalPayoff: number | null;
}

export interface GameSettings {
  initialBudget: number;
  minimumBet: number;
  payoffFunction: 'odds_against' | 'log_score' | 'quadratic_score' | 'proportional_posterior';
}

export const DEFAULT_GAME_SETTINGS: GameSettings = {
  initialBudget: 100,
  minimumBet: 1,
  payoffFunction: 'odds_against'  // Horse race style - odds set by priors
};

// Weight of Evidence helpers
export interface WoEValue {
  hypothesisId: string;
  evidenceId: string;
  paradigmId: string;
  likelihoodRatio: number;
  weightOfEvidence: number; // in decibans
}

export type WoELevel = 'strong_support' | 'weak_support' | 'neutral' | 'weak_refute' | 'strong_refute';

export function getWoELevel(woe: number): WoELevel {
  if (woe >= 5) return 'strong_support';
  if (woe > 0) return 'weak_support';
  if (woe > -0.5 && woe < 0.5) return 'neutral';
  if (woe > -5) return 'weak_refute';
  return 'strong_refute';
}

export function calculateWoE(likelihoodRatio: number): number {
  // Weight of Evidence in decibans = 10 * log10(LR)
  if (likelihoodRatio <= 0) return -Infinity;
  return 10 * Math.log10(likelihoodRatio);
}
