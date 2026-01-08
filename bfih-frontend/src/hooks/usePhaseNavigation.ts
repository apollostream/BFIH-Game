// Hook for navigating between game phases

import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGameStore } from '../stores';
import { GAME_PHASES, type GamePhase } from '../types';

/**
 * Returns a handler for navigating to a game phase.
 * Allows navigation to:
 * - Any phase up to and including furthestPhase (previously visited)
 * - The next phase in sequence (one step forward from current)
 */
export function usePhaseNavigation() {
  const navigate = useNavigate();
  const { scenarioId, currentPhase, furthestPhase, setPhase } = useGameStore();

  const currentIndex = GAME_PHASES.indexOf(currentPhase);
  const furthestIndex = GAME_PHASES.indexOf(furthestPhase);

  // Calculate which phases are navigable
  const isPhaseNavigable = useCallback((phase: GamePhase) => {
    const phaseIndex = GAME_PHASES.indexOf(phase);
    // Can navigate to any phase up to furthestPhase
    if (phaseIndex <= furthestIndex) return true;
    // Can navigate to next phase (one step forward from current)
    if (phaseIndex === currentIndex + 1) return true;
    return false;
  }, [currentIndex, furthestIndex]);

  // Build list of completed phases (all phases before furthest)
  const completedPhases = GAME_PHASES.slice(0, furthestIndex);

  const handlePhaseClick = useCallback((phase: GamePhase) => {
    if (!scenarioId) return;

    // Check if navigation is allowed
    if (!isPhaseNavigable(phase)) return;

    // Update game state
    setPhase(phase);

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
  }, [scenarioId, isPhaseNavigable, setPhase, navigate]);

  return {
    handlePhaseClick,
    completedPhases,
    currentPhase,
    furthestPhase,
    isPhaseNavigable,
  };
}
