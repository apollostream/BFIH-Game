import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../../components/layout/PageContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { PhaseIndicator } from '../../components/game/PhaseIndicator';
import { BeliefSpaceRadar } from '../../components/visualizations/BeliefSpaceRadar';
import { HypothesisBarChart } from '../../components/visualizations/HypothesisBarChart';
import { useGameStore, useBettingStore, useAnalysisStore } from '../../stores';
import { usePhaseNavigation } from '../../hooks';
import { pageVariants, staggerContainerVariants, cardVariants, formatPercent, formatCredits } from '../../utils';
import type { PosteriorsByParadigm } from '../../types';

export function DebriefPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();
  const {
    scenarioConfig,
    selectedParadigms,
    activeParadigm,
    setActiveParadigm,
    setPhase,
    resetGame,
  } = useGameStore();
  const { bets, budget, getTotalBet, betHistory, reset: resetBetting } = useBettingStore();
  const { currentAnalysis } = useAnalysisStore();
  const { handlePhaseClick, completedPhases } = usePhaseNavigation();

  const [showInsights, setShowInsights] = useState(false);

  useEffect(() => {
    setPhase('debrief');
    setTimeout(() => setShowInsights(true), 500);
  }, [setPhase]);

  // Support both 'priors' and 'priors_by_paradigm' field names
  const priorsSource = scenarioConfig?.priors || scenarioConfig?.priors_by_paradigm;

  // Build posteriors and priors
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

  // Same as priors for now (in real impl, would use actual posteriors)
  const posteriorsData = priorsData;

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

  const totalBet = getTotalBet();
  const posteriors = posteriorsData[activeParadigm] || {};

  // Calculate insights
  const insights = useMemo(() => {
    const results: string[] = [];

    // Paradigm divergence
    const paradigmPosteriorsForH1 = paradigms.map((p) => {
      const post = posteriorsData[p.id] || {};
      const h1 = scenarioConfig.hypotheses?.[0]?.id;
      return { paradigm: p.name, value: post[h1 || ''] || 0 };
    });
    const maxDiff = Math.max(...paradigmPosteriorsForH1.map((p) => p.value)) -
                    Math.min(...paradigmPosteriorsForH1.map((p) => p.value));
    if (maxDiff > 0.2) {
      results.push(`Paradigm choice matters! Different worldviews led to posteriors differing by ${formatPercent(maxDiff)}`);
    }

    // Betting strategy
    const bettedHypotheses = Object.entries(bets).filter(([, v]) => v > 0);
    if (bettedHypotheses.length === 1) {
      results.push("You concentrated all bets on a single hypothesis - high risk, high reward strategy");
    } else if (bettedHypotheses.length >= 4) {
      results.push("You diversified your bets across many hypotheses - conservative strategy");
    }

    // Evidence impact - check analysis metadata first, then scenarioConfig
    const clusters = currentAnalysis?.metadata?.evidence_clusters
      || scenarioConfig.evidence_clusters
      || [];
    if (clusters.length >= 3) {
      results.push(`${clusters.length} evidence clusters were analyzed, each updating posterior probabilities`);
    }

    // Default insights
    if (results.length === 0) {
      results.push("This analysis demonstrated how Bayesian reasoning can structure complex debates");
      results.push("Different paradigms naturally lead to different conclusions from the same evidence");
    }

    return results;
  }, [scenarioConfig, paradigms, posteriorsData, bets, currentAnalysis]);

  const handlePlayAgain = () => {
    resetBetting();
    navigate(`/game/${scenarioId}/setup`);
  };

  const handleNewAnalysis = () => {
    resetGame();
    resetBetting();
    navigate('/');
  };

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
          currentPhase="debrief"
          completedPhases={completedPhases}
          onPhaseClick={handlePhaseClick}
          className="mb-8"
        />

        {/* Title */}
        <motion.div variants={cardVariants} className="text-center mb-8">
          <h1 className="text-3xl font-bold text-text-primary mb-2">
            Post-Game Debrief
          </h1>
          <p className="text-lg text-text-secondary">
            Reflect on your analysis and learn from the experience
          </p>
        </motion.div>

        {/* Summary Card */}
        <motion.div variants={cardVariants} className="mb-8">
          <Card variant="glass" className="p-8">
            <div className="grid md:grid-cols-4 gap-6 text-center">
              <div>
                <div className="text-4xl font-bold text-accent mb-1">
                  {scenarioConfig.paradigms?.length || 0}
                </div>
                <div className="text-text-secondary">Paradigms</div>
              </div>
              <div>
                <div className="text-4xl font-bold text-paradigm-k2 mb-1">
                  {scenarioConfig.hypotheses?.length || 0}
                </div>
                <div className="text-text-secondary">Hypotheses</div>
              </div>
              <div>
                <div className="text-4xl font-bold text-paradigm-k3 mb-1">
                  {currentAnalysis?.metadata?.evidence_clusters?.length
                    || scenarioConfig.evidence_clusters?.length
                    || 0}
                </div>
                <div className="text-text-secondary">Evidence Clusters</div>
              </div>
              <div>
                <div className="text-4xl font-bold text-paradigm-k1 mb-1">
                  {formatCredits(totalBet)}
                </div>
                <div className="text-text-secondary">Total Wagered</div>
              </div>
            </div>
          </Card>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Key Insights */}
          <motion.div variants={cardVariants}>
            <Card className="p-6 h-full">
              <h2 className="text-xl font-semibold text-text-primary mb-4">
                Key Insights
              </h2>
              {showInsights ? (
                <motion.div
                  variants={staggerContainerVariants}
                  initial="initial"
                  animate="animate"
                  className="space-y-4"
                >
                  {insights.map((insight, index) => (
                    <motion.div
                      key={index}
                      variants={cardVariants}
                      className="flex items-start gap-3 p-3 rounded-lg bg-surface-2"
                    >
                      <span className="text-accent text-lg">💡</span>
                      <p className="text-text-secondary">{insight}</p>
                    </motion.div>
                  ))}
                </motion.div>
              ) : (
                <div className="flex items-center justify-center h-32">
                  <motion.div
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                    className="text-text-muted"
                  >
                    Generating insights...
                  </motion.div>
                </div>
              )}
            </Card>
          </motion.div>

          {/* Your Betting Journey */}
          <motion.div variants={cardVariants}>
            <Card className="p-6 h-full">
              <h2 className="text-xl font-semibold text-text-primary mb-4">
                Your Betting Journey
              </h2>
              <div className="space-y-4">
                {/* Initial Bets */}
                <div>
                  <h3 className="text-sm font-medium text-text-muted mb-2">
                    Initial Allocations
                  </h3>
                  <div className="grid grid-cols-3 gap-2">
                    {scenarioConfig.hypotheses?.map((h) => {
                      const bet = bets[h.id] || 0;
                      const _posterior = posteriors[h.id] || 0;
                      void _posterior; // Used for future payoff calculation display
                      return (
                        <div
                          key={h.id}
                          className="p-2 rounded-lg bg-surface-2 text-center"
                        >
                          <div className="text-xs text-text-muted">{h.id}</div>
                          <div className="font-medium text-text-primary">
                            {formatCredits(bet)}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Bet History */}
                {betHistory.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-text-muted mb-2">
                      Bet History
                    </h3>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {betHistory.map((entry, i) => {
                        // Type guard for BetHistoryEntry vs BetRound
                        if ('action' in entry && 'hypothesisId' in entry) {
                          return (
                            <div
                              key={i}
                              className="flex items-center justify-between text-sm p-2 rounded bg-surface-2"
                            >
                              <span className="text-text-secondary">
                                {entry.action} on {entry.hypothesisId}
                              </span>
                              <Badge variant={entry.action === 'raise' ? 'success' : 'secondary'}>
                                {entry.action === 'raise' ? '+' : ''}{entry.amount}
                              </Badge>
                            </div>
                          );
                        }
                        // BetRound entry
                        return (
                          <div
                            key={i}
                            className="flex items-center justify-between text-sm p-2 rounded bg-surface-2"
                          >
                            <span className="text-text-secondary">
                              Round {entry.roundNumber} ({entry.type})
                            </span>
                            <Badge variant={entry.type === 'raise' ? 'success' : 'secondary'}>
                              {Object.values(entry.bets).reduce((a, b) => a + b, 0)} total
                            </Badge>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Budget utilization */}
                <div>
                  <h3 className="text-sm font-medium text-text-muted mb-2">
                    Budget Utilization
                  </h3>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-4 bg-surface-2 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(totalBet / budget) * 100}%` }}
                        transition={{ duration: 1, delay: 0.5 }}
                        className="h-full bg-accent rounded-full"
                      />
                    </div>
                    <span className="text-sm text-text-primary font-medium">
                      {formatPercent(totalBet / budget)}
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        </div>

        {/* Final Visualizations */}
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

        {/* What-If Section */}
        <motion.div variants={cardVariants} className="mt-6">
          <Card className="p-6">
            <h2 className="text-xl font-semibold text-text-primary mb-4">
              What If...?
            </h2>
            <p className="text-text-secondary mb-4">
              Explore how different choices might have led to different outcomes:
            </p>
            <div className="grid md:grid-cols-3 gap-4">
              <Card variant="bordered" className="p-4">
                <h3 className="font-medium text-text-primary mb-2">
                  Different Paradigm
                </h3>
                <p className="text-sm text-text-secondary">
                  What if you had analyzed from a {
                    paradigms.find((p) => p.id !== activeParadigm)?.name || 'different'
                  } perspective?
                </p>
              </Card>
              <Card variant="bordered" className="p-4">
                <h3 className="font-medium text-text-primary mb-2">
                  Alternative Betting
                </h3>
                <p className="text-sm text-text-secondary">
                  What if you had bet more on {
                    scenarioConfig.hypotheses?.find((h) => !bets[h.id])?.id || 'other hypotheses'
                  }?
                </p>
              </Card>
              <Card variant="bordered" className="p-4">
                <h3 className="font-medium text-text-primary mb-2">
                  New Evidence
                </h3>
                <p className="text-sm text-text-secondary">
                  What other evidence might shift these probabilities?
                </p>
              </Card>
            </div>
          </Card>
        </motion.div>

        {/* Actions */}
        <motion.div
          variants={cardVariants}
          className="flex flex-col sm:flex-row justify-center items-center gap-4 mt-8"
        >
          <Button
            variant="ghost"
            onClick={() => navigate(`/game/${scenarioId}/report`)}
          >
            Back to Report
          </Button>
          <Button
            variant="secondary"
            onClick={handlePlayAgain}
          >
            Play Again (Same Scenario)
          </Button>
          <Button
            size="lg"
            onClick={handleNewAnalysis}
          >
            Analyze New Topic
          </Button>
        </motion.div>

        {/* Thanks */}
        <motion.div
          variants={cardVariants}
          className="text-center mt-12 py-8 border-t border-border"
        >
          <p className="text-text-muted text-sm">
            Thank you for playing the BFIH Hypothesis Tournament.
          </p>
          <p className="text-text-muted text-sm mt-1">
            Remember: The goal is not to be right, but to think more clearly.
          </p>
        </motion.div>
      </PageContainer>
    </motion.div>
  );
}
