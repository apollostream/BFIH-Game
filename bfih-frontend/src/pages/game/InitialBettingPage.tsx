import { useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../../components/layout/PageContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { PhaseIndicator } from '../../components/game/PhaseIndicator';
import { BettingSlider, BudgetBar, BetSummary } from '../../components/game/BettingSlider';
import { HypothesisBarChart } from '../../components/visualizations/HypothesisBarChart';
import { useGameStore, useBettingStore } from '../../stores';
import { usePhaseNavigation } from '../../hooks';
import { pageVariants, staggerContainerVariants, cardVariants } from '../../utils';
import type { PosteriorsByParadigm } from '../../types';

export function InitialBettingPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();
  const {
    scenarioConfig,
    selectedParadigms,
    activeParadigm,
    setPhase,
  } = useGameStore();
  const {
    bets,
    budget,
    setBet,
    initializeBets,
    getTotalBet,
    hasBets,
  } = useBettingStore();
  const { handlePhaseClick, completedPhases } = usePhaseNavigation();

  useEffect(() => {
    setPhase('betting');
    if (scenarioConfig?.hypotheses) {
      initializeBets(scenarioConfig.hypotheses.map((h) => h.id));
    }
  }, [setPhase, scenarioConfig, initializeBets]);

  // Build priors data for visualization
  // Support both 'priors' and 'priors_by_paradigm' field names
  const priorsSource = scenarioConfig?.priors || scenarioConfig?.priors_by_paradigm;

  const priorsData = useMemo((): PosteriorsByParadigm => {
    if (!priorsSource) return {};
    const result: PosteriorsByParadigm = {};
    for (const paradigmId of Object.keys(priorsSource)) {
      result[paradigmId] = {};
      const paradigmPriors = priorsSource[paradigmId];
      for (const [hypId, prior] of Object.entries(paradigmPriors)) {
        result[paradigmId][hypId] = typeof prior === 'number' ? prior : prior.probability;
      }
    }
    return result;
  }, [priorsSource]);

  if (!scenarioConfig) {
    return (
      <PageContainer className="flex items-center justify-center min-h-[60vh]">
        <Card className="p-8 text-center">
          <p className="text-text-secondary mb-4">No scenario loaded</p>
          <Button onClick={() => navigate('/')}>Go Home</Button>
        </Card>
      </PageContainer>
    );
  }

  const _paradigms = scenarioConfig.paradigms?.filter(
    (p) => selectedParadigms.includes(p.id)
  ) || [];
  void _paradigms; // Reserved for future paradigm-specific betting hints

  const totalBet = getTotalBet();
  const canContinue = hasBets() && totalBet <= budget;

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <PageContainer>
        {/* Phase Indicator */}
        <PhaseIndicator
          currentPhase="betting"
          completedPhases={completedPhases}
          onPhaseClick={handlePhaseClick}
          className="mb-8"
        />

        {/* Title */}
        <motion.div variants={cardVariants} className="text-center mb-8">
          <h1 className="text-3xl font-bold text-text-primary mb-2">
            Initial Betting
          </h1>
          <p className="text-lg text-text-secondary">
            Place your bets on which hypotheses you believe are most likely
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Betting Interface */}
          <div className="lg:col-span-2 space-y-6">
            {/* Budget Bar */}
            <motion.div variants={cardVariants}>
              <BudgetBar
                budget={budget}
                spent={totalBet}
                className="mb-2"
              />
            </motion.div>

            {/* Instructions */}
            <motion.div variants={cardVariants}>
              <Card variant="bordered" className="p-4">
                <h3 className="text-sm font-medium text-text-primary mb-2">
                  How Betting Works
                </h3>
                <ul className="text-sm text-text-secondary space-y-1 list-disc list-inside">
                  <li>You have {budget} credits to allocate across hypotheses</li>
                  <li>Higher bets = higher potential payoffs (and losses)</li>
                  <li>Payoffs are calculated based on the final posterior probabilities</li>
                  <li>After evidence is revealed, you can raise (but not lower) your bets</li>
                </ul>
              </Card>
            </motion.div>

            {/* Betting Sliders */}
            <motion.div
              variants={staggerContainerVariants}
              initial="initial"
              animate="animate"
              className="space-y-4"
            >
              {scenarioConfig.hypotheses?.map((hypothesis) => {
                const currentPrior = priorsSource?.[activeParadigm]?.[hypothesis.id];
                const priorValue = typeof currentPrior === 'number'
                  ? currentPrior
                  : currentPrior?.probability || 0;

                return (
                  <motion.div key={hypothesis.id} variants={cardVariants}>
                    <BettingSlider
                      hypothesis={hypothesis}
                      currentBet={bets[hypothesis.id] || 0}
                      maxBet={budget - totalBet + (bets[hypothesis.id] || 0)}
                      prior={priorValue}
                      onBetChange={(value) => setBet(hypothesis.id, value)}
                    />
                  </motion.div>
                );
              })}
            </motion.div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-4">
            <motion.div variants={cardVariants} className="sticky top-24">
              {/* Bet Summary */}
              <BetSummary
                bets={bets}
                hypotheses={scenarioConfig.hypotheses || []}
                budget={budget}
              />

              {/* Prior Chart */}
              <div className="mt-4">
                <HypothesisBarChart
                  hypotheses={scenarioConfig.hypotheses || []}
                  posteriors={priorsData}
                  activeParadigm={activeParadigm}
                  showPriors={false}
                />
              </div>

              {/* Tips */}
              <Card className="mt-4 p-4">
                <h3 className="text-sm font-medium text-text-primary mb-2">
                  Betting Tips
                </h3>
                <ul className="text-xs text-text-secondary space-y-2">
                  <li>
                    <strong>Diversify:</strong> Spreading bets reduces risk but limits max returns
                  </li>
                  <li>
                    <strong>Consider priors:</strong> The AI's prior probabilities reflect baseline expectations
                  </li>
                  <li>
                    <strong>Think ahead:</strong> Evidence will update probabilities - bet on what you think will be supported
                  </li>
                </ul>
              </Card>
            </motion.div>
          </div>
        </div>

        {/* Navigation */}
        <motion.div
          variants={cardVariants}
          className="flex justify-between items-center mt-8"
        >
          <Button
            variant="ghost"
            onClick={() => navigate(`/game/${scenarioId}/priors`)}
          >
            Back to Priors
          </Button>
          <div className="flex items-center gap-4">
            {totalBet > budget && (
              <span className="text-error text-sm">
                Bets exceed budget!
              </span>
            )}
            <Button
              size="lg"
              onClick={() => navigate(`/game/${scenarioId}/evidence`)}
              disabled={!canContinue}
            >
              {hasBets() ? 'Continue to Evidence' : 'Place Some Bets First'}
            </Button>
          </div>
        </motion.div>
      </PageContainer>
    </motion.div>
  );
}
