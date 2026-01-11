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

// ============================================================================
// COMPETITOR SYSTEM (Player vs Paradigm Personas)
// ============================================================================

export interface Competitor {
  id: string;              // "player" or paradigm ID ("K0", "K1", etc.)
  name: string;            // Display name
  icon: string;            // Emoji icon
  description: string;     // Short description of betting style
  bets: Record<string, number>;  // Bets on each hypothesis
  payoff: number;          // Final payoff (calculated after resolution)
  isPlayer: boolean;       // True for human player, false for AI personas
}

export interface LeaderboardEntry extends Competitor {
  rank: number;
}

// Persona definitions for each paradigm type
export interface PersonaDefinition {
  icon: string;
  name: string;
  description: string;
}

// Default persona mappings - can be overridden by paradigm data
export const PARADIGM_PERSONAS: Record<string, PersonaDefinition> = {
  // Default personas for common paradigm patterns
  'K0': { icon: '🎯', name: 'The Empiricist', description: 'Bets based on balanced multi-domain analysis' },
  'K1': { icon: '🚀', name: 'The Techno-Optimist', description: 'Favors technology-driven solutions' },
  'K2': { icon: '📜', name: 'The Traditionalist', description: 'Trusts historical patterns and precedent' },
  'K3': { icon: '🔍', name: 'The Skeptic', description: 'Hedges bets across many hypotheses' },
  'K4': { icon: '⚖️', name: 'The Policy Wonk', description: 'Focuses on institutional factors' },
  'K5': { icon: '💹', name: 'The Market Watcher', description: 'Follows economic indicators' },
  'K0-inv': { icon: '🔄', name: 'The Contrarian', description: 'Inverts conventional wisdom' },
};

// Fallback persona for unknown paradigms
export const DEFAULT_PERSONA: PersonaDefinition = {
  icon: '🤖',
  name: 'AI Analyst',
  description: 'Bets according to paradigm priors'
};

// Get persona for a paradigm ID
export function getPersonaForParadigm(paradigmId: string, paradigmName?: string): PersonaDefinition {
  // Check if we have a predefined persona
  if (PARADIGM_PERSONAS[paradigmId]) {
    return PARADIGM_PERSONAS[paradigmId];
  }

  // Generate a persona based on the paradigm name if provided
  if (paradigmName) {
    const lowerName = paradigmName.toLowerCase();
    if (lowerName.includes('techno') || lowerName.includes('optim')) {
      return { icon: '🚀', name: paradigmName, description: 'Technology-focused outlook' };
    }
    if (lowerName.includes('tradition') || lowerName.includes('conserv')) {
      return { icon: '📜', name: paradigmName, description: 'Values historical precedent' };
    }
    if (lowerName.includes('skept') || lowerName.includes('critic')) {
      return { icon: '🔍', name: paradigmName, description: 'Cautious and questioning' };
    }
    if (lowerName.includes('empir') || lowerName.includes('ration')) {
      return { icon: '🎯', name: paradigmName, description: 'Evidence-based reasoning' };
    }
    if (lowerName.includes('market') || lowerName.includes('econom')) {
      return { icon: '💹', name: paradigmName, description: 'Market-driven perspective' };
    }
    if (lowerName.includes('policy') || lowerName.includes('regul')) {
      return { icon: '⚖️', name: paradigmName, description: 'Policy-focused analysis' };
    }
    if (lowerName.includes('cultur') || lowerName.includes('social')) {
      return { icon: '🌍', name: paradigmName, description: 'Cultural dynamics focus' };
    }
  }

  return { ...DEFAULT_PERSONA, name: paradigmName || DEFAULT_PERSONA.name };
}

// Calculate bets for a persona based on their paradigm priors
export function calculatePersonaBets(
  priors: Record<string, number>,
  budget: number
): Record<string, number> {
  const bets: Record<string, number> = {};
  let totalPrior = 0;

  // Sum priors to handle normalization
  for (const prior of Object.values(priors)) {
    const p = typeof prior === 'number' ? prior : (prior as { probability: number }).probability;
    totalPrior += p;
  }

  // Distribute budget proportionally to priors
  let allocated = 0;
  const entries = Object.entries(priors);

  for (let i = 0; i < entries.length; i++) {
    const [hypId, priorValue] = entries[i];
    const prior = typeof priorValue === 'number' ? priorValue : (priorValue as { probability: number }).probability;

    if (i === entries.length - 1) {
      // Last hypothesis gets remaining budget to avoid rounding issues
      bets[hypId] = budget - allocated;
    } else {
      const bet = Math.round((prior / totalPrior) * budget);
      bets[hypId] = bet;
      allocated += bet;
    }
  }

  return bets;
}
