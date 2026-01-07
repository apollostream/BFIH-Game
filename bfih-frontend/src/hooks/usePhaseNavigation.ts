// Hook for navigating between game phases

import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameStore } from '../stores';
import { GAME_PHASES, type GamePhase } from '../types';

/**
 * Returns a handler for navigating to a game phase.
 * Only allows navigation to completed phases (not forward skipping).
 */
export function usePhaseNavigation() {
  const navigate = useNavigate();
  const { scenarioId, currentPhase } = useGameStore();

  const currentIndex = GAME_PHASES.indexOf(currentPhase);

  // Build list of completed phases (all phases before current)
  const completedPhases = GAME_PHASES.slice(0, currentIndex);

  const handlePhaseClick = useCallback((phase: GamePhase) => {
    if (!scenarioId) return;

    const phaseIndex = GAME_PHASES.indexOf(phase);

    // Only allow navigation to completed phases or current phase
    if (phaseIndex > currentIndex) return;

    // Map phase to route
    const phaseRoutes: Record<GamePhase, string> = {
      setup: `/game/${scenarioId}/setup`,
      hypotheses: `/game/${scenarioId}/hypotheses`,
      priors: `/game/${scenarioId}/priors`,
      betting: `/game/${scenarioId}/betting`,
      evidence: `/game/${scenarioId}/evidence/0`,
      resolution: `/game/${scenarioId}/resolution`,
      report: `/game/${scenarioId}/report`,
      debrief: `/game/${scenarioId}/debrief`,
    };

    navigate(phaseRoutes[phase]);
  }, [scenarioId, currentIndex, navigate]);

  return {
    handlePhaseClick,
    completedPhases,
    currentPhase,
  };
}
