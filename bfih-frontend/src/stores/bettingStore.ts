// Player betting state management

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { BetRound, GameSettings } from '../types';

interface BetHistoryEntry {
  hypothesisId: string;
  action: 'initial' | 'raise';
  amount: number;
  timestamp: string;
}

type BetHistoryItem = BetHistoryEntry | BetRound;

interface BettingState {
  // Budget
  initialBudget: number;
  currentBudget: number;
  budget: number; // Alias for currentBudget

  // Bets by hypothesis (cumulative across rounds)
  bets: Record<string, number>;

  // Bet history per round
  betHistory: BetHistoryItem[];

  // Player subjective probabilities (optional)
  subjectivePriors: Record<string, number> | null;

  // Game settings
  settings: GameSettings;

  // Lock state
  betsLocked: boolean;

  // Computed
  getTotalBet: () => number;
  getRemainingBudget: () => number;
  getBetForHypothesis: (hypothesisId: string) => number;
  hasBets: () => boolean;

  // Actions
  initBetting: (settings?: Partial<GameSettings>) => void;
  initializeBets: (hypothesisIds: string[]) => void;
  placeBet: (hypothesisId: string, amount: number) => void;
  setBet: (hypothesisId: string, amount: number) => void;
  adjustBet: (hypothesisId: string, newAmount: number) => void;
  raiseBet: (hypothesisId: string, additionalAmount: number) => void;
  removeBet: (hypothesisId: string) => void;
  lockBets: (roundNumber: number, type: 'initial' | 'raise') => void;
  setSubjectivePriors: (priors: Record<string, number>) => void;
  calculatePayoff: (
    hypothesisId: string,
    posterior: number,
    isWinner?: boolean,
    prior?: number
  ) => number;
  resetBetting: () => void;
  reset: () => void;
}

export const useBettingStore = create<BettingState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        initialBudget: 100,
        currentBudget: 100,
        budget: 100,
        bets: {},
        betHistory: [],
        subjectivePriors: null,
        settings: {
          initialBudget: 100,
          minimumBet: 1,
          payoffFunction: 'odds_against',  // Horse race style - odds set by priors
        },
        betsLocked: false,

        // Computed
        getTotalBet: () => {
          const { bets } = get();
          return Object.values(bets).reduce((sum, bet) => sum + bet, 0);
        },

        getRemainingBudget: () => {
          const { currentBudget, bets } = get();
          const totalBet = Object.values(bets).reduce((sum, bet) => sum + bet, 0);
          return currentBudget - totalBet;
        },

        getBetForHypothesis: (hypothesisId) => {
          return get().bets[hypothesisId] || 0;
        },

        hasBets: () => {
          const { bets } = get();
          return Object.values(bets).some((bet) => bet > 0);
        },

        // Actions
        initBetting: (customSettings) => {
          const settings = {
            ...get().settings,
            ...customSettings,
          };

          set({
            initialBudget: settings.initialBudget,
            currentBudget: settings.initialBudget,
            budget: settings.initialBudget,
            bets: {},
            betHistory: [],
            subjectivePriors: null,
            settings,
            betsLocked: false,
          });
        },

        initializeBets: (hypothesisIds) => {
          const bets: Record<string, number> = {};
          hypothesisIds.forEach((id) => {
            bets[id] = 0;
          });
          set({ bets });
        },

        placeBet: (hypothesisId, amount) => {
          const { bets, settings, betsLocked } = get();

          if (betsLocked) {
            console.warn('Bets are locked');
            return;
          }

          if (amount < 0) {
            console.warn('Bet amount cannot be negative');
            return;
          }

          if (amount > 0 && amount < settings.minimumBet) {
            console.warn(`Minimum bet is ${settings.minimumBet}`);
            return;
          }

          const remaining = get().getRemainingBudget();
          const currentBet = bets[hypothesisId] || 0;
          const additionalRequired = amount - currentBet;

          if (additionalRequired > remaining) {
            console.warn('Insufficient budget');
            return;
          }

          set({
            bets: {
              ...bets,
              [hypothesisId]: amount,
            },
          });
        },

        setBet: (hypothesisId, amount) => {
          get().placeBet(hypothesisId, amount);
        },

        adjustBet: (hypothesisId, newAmount) => {
          get().placeBet(hypothesisId, newAmount);
        },

        raiseBet: (hypothesisId, additionalAmount) => {
          const { bets, betHistory } = get();
          const currentBet = bets[hypothesisId] || 0;
          const newBet = currentBet + additionalAmount;

          get().placeBet(hypothesisId, newBet);

          // Add to history
          set({
            betHistory: [
              ...betHistory,
              {
                hypothesisId,
                action: 'raise',
                amount: additionalAmount,
                timestamp: new Date().toISOString(),
              },
            ],
          });
        },

        removeBet: (hypothesisId) => {
          const { bets, betsLocked } = get();

          if (betsLocked) {
            console.warn('Bets are locked');
            return;
          }

          const { [hypothesisId]: _, ...rest } = bets;
          set({ bets: rest });
        },

        lockBets: (roundNumber, type) => {
          const { bets, betHistory } = get();

          const round: BetRound = {
            roundNumber,
            bets: { ...bets },
            timestamp: new Date().toISOString(),
            type,
          };

          set({
            betHistory: [...betHistory, round],
            betsLocked: true,
          });
        },

        setSubjectivePriors: (priors) => {
          // Validate that priors sum to approximately 1
          const sum = Object.values(priors).reduce((s, p) => s + p, 0);
          if (Math.abs(sum - 1) > 0.01) {
            console.warn('Subjective priors should sum to 1');
          }

          set({ subjectivePriors: priors });
        },

        calculatePayoff: (hypothesisId, posterior, isWinner, prior) => {
          const { bets, settings } = get();
          const bet = bets[hypothesisId] || 0;

          switch (settings.payoffFunction) {
            case 'odds_against':
              // Horse race style: net profit = (bet / prior) - bet if winner, -bet if loser
              // Odds-against = (1-prior)/prior, so 1 + odds-against = 1/prior
              // Example: prior=0.2, bet=10 → total return=50, net profit=40
              // If loser: you lose your bet entirely (-bet)
              if (!prior || prior <= 0) return isWinner ? 0 : -bet;
              return isWinner ? (bet / prior) - bet : -bet;

            case 'proportional_posterior':
              // Payout = bet * (2 * posterior - 1) for expected value normalization
              return bet * (2 * posterior - 1);

            case 'log_score':
              // Log scoring rule
              if (posterior <= 0) return -bet;
              return bet * Math.log2(posterior + 0.01);

            case 'quadratic_score':
              // Quadratic scoring rule
              const score = 2 * posterior - 1;
              return bet * score;

            default:
              return bet * (posterior - 0.5);
          }
        },

        resetBetting: () => {
          const { settings } = get();
          set({
            initialBudget: settings.initialBudget,
            currentBudget: settings.initialBudget,
            budget: settings.initialBudget,
            bets: {},
            betHistory: [],
            subjectivePriors: null,
            betsLocked: false,
          });
        },

        reset: () => {
          get().resetBetting();
        },
      }),
      {
        name: 'bfih-betting-store',
        partialize: (state) => ({
          bets: state.bets,
          betHistory: state.betHistory,
          subjectivePriors: state.subjectivePriors,
        }),
      }
    ),
    { name: 'BettingStore' }
  )
);
