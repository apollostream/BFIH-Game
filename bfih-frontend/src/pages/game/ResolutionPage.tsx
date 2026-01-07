import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../../components/layout/PageContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { PhaseIndicator } from '../../components/game/PhaseIndicator';
import { HypothesisRanking } from '../../components/game/HypothesisCard';
import { HypothesisBarChart } from '../../components/visualizations/HypothesisBarChart';
import { BeliefSpaceRadar } from '../../components/visualizations/BeliefSpaceRadar';
import { useGameStore, useBettingStore } from '../../stores';
import { usePhaseNavigation } from '../../hooks';
import { pageVariants, cardVariants, formatPercent, formatCredits } from '../../utils';
import type { PosteriorsByParadigm } from '../../types';

export function ResolutionPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();
  const {
    scenarioConfig,
    selectedParadigms,
    activeParadigm,
    setActiveParadigm,
    setPhase,
  } = useGameStore();
  const { bets, calculatePayoff } = useBettingStore();
  const { handlePhaseClick, completedPhases } = usePhaseNavigation();

  const [showPayoffs, setShowPayoffs] = useState(false);

  useEffect(() => {
    setPhase('resolution');
    // Delayed reveal of payoffs
    const timer = setTimeout(() => setShowPayoffs(true), 1500);
    return () => clearTimeout(timer);
  }, [setPhase]);

  // Support both 'priors' and 'priors_by_paradigm' field names
  const priorsSource = scenarioConfig?.priors || scenarioConfig?.priors_by_paradigm;

  // Get posteriors from analysis result (or use priors as fallback)
  const posteriorsData = useMemo((): PosteriorsByParadigm => {
    // In real implementation, this would come from the analysis result
    if (!priorsSource) return {};
    const result: PosteriorsByParadigm = {};
    for (const paradigmId of Object.keys(priorsSource)) {
      result[paradigmId] = {};
      const paradigmPriors = priorsSource[paradigmId];
      for (const [hypId, prior] of Object.entries(paradigmPriors)) {
        // Simulate some posterior updates
        const priorVal = typeof prior === 'number' ? prior : prior.probability;
        result[paradigmId][hypId] = priorVal;
      }
    }
    return result;
  }, [priorsSource]);

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

  const paradigms = scenarioConfig.paradigms?.filter(
    (p) => selectedParadigms.includes(p.id)
  ) || [];

  // Calculate payoffs for each hypothesis
  const payoffs = useMemo(() => {
    const result: Record<string, number> = {};
    const posteriors = posteriorsData[activeParadigm] || {};

    for (const hypothesis of scenarioConfig.hypotheses || []) {
      const posterior = posteriors[hypothesis.id] || 0;
      const _bet = bets[hypothesis.id] || 0;
      void _bet; // Used internally by calculatePayoff
      result[hypothesis.id] = calculatePayoff(hypothesis.id, posterior);
    }
    return result;
  }, [scenarioConfig.hypotheses, bets, posteriorsData, activeParadigm, calculatePayoff]);

  const totalPayoff = Object.values(payoffs).reduce((sum, p) => sum + p, 0);

  // Find winner (highest posterior)
  const posteriors = posteriorsData[activeParadigm] || {};
  const sortedHypotheses = [...(scenarioConfig.hypotheses || [])]
    .sort((a, b) => (posteriors[b.id] || 0) - (posteriors[a.id] || 0));
  const winner = sortedHypotheses[0];

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
          currentPhase="resolution"
          completedPhases={completedPhases}
          onPhaseClick={handlePhaseClick}
          className="mb-8"
        />

        {/* Title */}
        <motion.div variants={cardVariants} className="text-center mb-8">
          <h1 className="text-3xl font-bold text-text-primary mb-2">
            Resolution
          </h1>
          <p className="text-lg text-text-secondary">
            Final posterior probabilities and your betting results
          </p>
        </motion.div>

        {/* Winner Announcement */}
        {winner && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="mb-8"
          >
            <Card variant="glass" className="p-8 text-center">
              <div className="text-sm text-text-muted uppercase tracking-wide mb-2">
                Most Probable Hypothesis
              </div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="text-4xl font-bold text-accent mb-2"
              >
                {winner.id}: {winner.name}
              </motion.div>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.9 }}
                className="text-2xl text-text-primary"
              >
                {formatPercent(posteriors[winner.id] || 0)} posterior probability
              </motion.div>
            </Card>
          </motion.div>
        )}

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Final Rankings */}
          <motion.div variants={cardVariants}>
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-text-primary mb-4">
                Final Hypothesis Rankings
              </h2>
              <HypothesisRanking
                hypotheses={scenarioConfig.hypotheses || []}
                posteriors={posteriors}
              />
            </Card>
          </motion.div>

          {/* Payoffs */}
          <motion.div
            variants={cardVariants}
            initial={{ opacity: 0 }}
            animate={{ opacity: showPayoffs ? 1 : 0.3 }}
          >
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-text-primary mb-4">
                Your Betting Results
              </h2>

              {showPayoffs ? (
                <>
                  <div className="space-y-3 mb-6">
                    {scenarioConfig.hypotheses?.map((hypothesis) => {
                      const bet = bets[hypothesis.id] || 0;
                      const payoff = payoffs[hypothesis.id] || 0;
                      const posterior = posteriors[hypothesis.id] || 0;

                      return (
                        <div
                          key={hypothesis.id}
                          className="flex items-center justify-between p-3 rounded-lg bg-surface-2"
                        >
                          <div>
                            <span className="font-medium text-text-primary">
                              {hypothesis.id}
                            </span>
                            <span className="text-text-muted ml-2">
                              Bet: {formatCredits(bet)}
                            </span>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-text-muted">
                              {formatPercent(posterior)}
                            </div>
                            <div
                              className={`font-bold ${
                                payoff >= 0 ? 'text-success' : 'text-error'
                              }`}
                            >
                              {payoff >= 0 ? '+' : ''}
                              {formatCredits(payoff)}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Total */}
                  <div className="pt-4 border-t border-border">
                    <div className="flex items-center justify-between">
                      <span className="text-lg font-medium text-text-primary">
                        Net Result
                      </span>
                      <motion.span
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.3, type: 'spring' }}
                        className={`text-2xl font-bold ${
                          totalPayoff >= 0 ? 'text-success' : 'text-error'
                        }`}
                      >
                        {totalPayoff >= 0 ? '+' : ''}
                        {formatCredits(totalPayoff)}
                      </motion.span>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <motion.div
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                    className="text-4xl mb-4"
                  >
                    🎲
                  </motion.div>
                  <p className="text-text-secondary">Calculating payoffs...</p>
                </div>
              )}
            </Card>
          </motion.div>
        </div>

        {/* Visualizations */}
        <div className="grid lg:grid-cols-2 gap-6 mt-6">
          <motion.div variants={cardVariants}>
            <HypothesisBarChart
              hypotheses={scenarioConfig.hypotheses || []}
              posteriors={posteriorsData}
              priors={priorsData[activeParadigm]}
              activeParadigm={activeParadigm}
              onParadigmChange={setActiveParadigm}
              showPriors
            />
          </motion.div>

          <motion.div variants={cardVariants}>
            <BeliefSpaceRadar
              hypotheses={scenarioConfig.hypotheses || []}
              paradigms={paradigms}
              posteriors={posteriorsData}
              priors={priorsData}
              showPriors
              enabledParadigms={selectedParadigms}
            />
          </motion.div>
        </div>

        {/* Navigation */}
        <motion.div
          variants={cardVariants}
          className="flex justify-between items-center mt-8"
        >
          <Button
            variant="ghost"
            onClick={() => navigate(`/game/${scenarioId}/evidence`)}
          >
            Back to Evidence
          </Button>
          <Button
            size="lg"
            onClick={() => navigate(`/game/${scenarioId}/report`)}
          >
            View Full Report
          </Button>
        </motion.div>
      </PageContainer>
    </motion.div>
  );
}
