import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../../components/layout/PageContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { PhaseIndicator } from '../../components/game/PhaseIndicator';
import { HypothesisRanking } from '../../components/game/HypothesisCard';
import { Leaderboard, VictoryMessage } from '../../components/game/Leaderboard';
import { VictoryOverlay } from '../../components/game/VictoryOverlay';
import { HypothesisBarChart } from '../../components/visualizations/HypothesisBarChart';
import { BeliefSpaceRadar } from '../../components/visualizations/BeliefSpaceRadar';
import { useGameStore, useBettingStore, useAnalysisStore, usePredictionStore } from '../../stores';
import { usePhaseNavigation } from '../../hooks';
import { pageVariants, cardVariants, formatPercent } from '../../utils';
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
    initializeCompetitors,
    calculateAllPayoffs,
    getLeaderboard,
    competitors,
    playerPayoff,
  } = useGameStore();
  const { bets, budget } = useBettingStore();
  const { currentAnalysis } = useAnalysisStore();
  const { results: predictionResults, totalBonus: predictionBonus, submitted: predictionSubmitted } = usePredictionStore();
  const { handlePhaseClick, completedPhases, furthestPhase, isPhaseNavigable } = usePhaseNavigation();

  const [showPayoffs, setShowPayoffs] = useState(false);
  const [showVictoryOverlay, setShowVictoryOverlay] = useState(false);

  // Support both 'priors' and 'priors_by_paradigm' field names
  const priorsSource = scenarioConfig?.priors || scenarioConfig?.priors_by_paradigm;

  useEffect(() => {
    setPhase('resolution');

    // Check if we need to initialize or reinitialize competitors
    const hasBets = Object.keys(bets).length > 0;
    if (!hasBets) return;

    // Find current player bets in competitors
    const playerCompetitor = competitors.find((c) => c.isPlayer);
    const playerBetsMatch = playerCompetitor &&
      Object.keys(bets).every((hypId) => playerCompetitor.bets[hypId] === bets[hypId]);

    // Initialize if no competitors, or reinitialize if player bets have changed
    if (competitors.length === 0 || !playerBetsMatch) {
      initializeCompetitors(bets, budget);
    }
  }, [setPhase, competitors, bets, budget, initializeCompetitors]);

  // Calculate payoffs once posteriors are available
  useEffect(() => {
    if (competitors.length > 0 && currentAnalysis?.posteriors && priorsSource) {
      const posteriors = currentAnalysis.posteriors[activeParadigm] || {};
      const paradigmPriors = priorsSource[activeParadigm] || {};

      // Extract prior probabilities
      const priors: Record<string, number> = {};
      for (const [hypId, prior] of Object.entries(paradigmPriors)) {
        priors[hypId] = typeof prior === 'number' ? prior : (prior as { probability: number })?.probability || 0;
      }

      calculateAllPayoffs(posteriors, priors);
    }
  }, [competitors.length, currentAnalysis, activeParadigm, priorsSource, calculateAllPayoffs]);

  // Show victory overlay after a delay
  useEffect(() => {
    if (showPayoffs && playerPayoff !== null) {
      const timer = setTimeout(() => setShowVictoryOverlay(true), 500);
      return () => clearTimeout(timer);
    }
  }, [showPayoffs, playerPayoff]);

  // Delayed reveal of payoffs
  useEffect(() => {
    const timer = setTimeout(() => setShowPayoffs(true), 1500);
    return () => clearTimeout(timer);
  }, []);

  // Get posteriors from analysis result
  const posteriorsData = useMemo((): PosteriorsByParadigm => {
    // Use actual posteriors from analysis result
    if (currentAnalysis?.posteriors) {
      return currentAnalysis.posteriors;
    }
    // Fallback to priors if no posteriors available
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
  }, [currentAnalysis, priorsSource]);

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

  // Get leaderboard data
  const leaderboard = getLeaderboard();
  const playerRank = leaderboard.find((c) => c.isPlayer)?.rank || 0;

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
          furthestPhase={furthestPhase}
          isPhaseNavigable={isPhaseNavigable}
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

        {/* Victory Message */}
        {showPayoffs && leaderboard.length > 0 && (
          <motion.div
            variants={cardVariants}
            className="mb-8"
          >
            <VictoryMessage
              playerRank={playerRank}
              totalCompetitors={leaderboard.length}
              winnerName={leaderboard[0]?.isPlayer ? undefined : leaderboard[0]?.name}
            />
          </motion.div>
        )}

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Leaderboard */}
          <motion.div
            variants={cardVariants}
            initial={{ opacity: 0 }}
            animate={{ opacity: showPayoffs ? 1 : 0.3 }}
          >
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-text-primary mb-4">
                Final Standings
              </h2>

              {showPayoffs && leaderboard.length > 0 ? (
                <Leaderboard entries={leaderboard} />
              ) : (
                <div className="text-center py-8">
                  <motion.div
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                    className="text-4xl mb-4"
                  >
                    🎲
                  </motion.div>
                  <p className="text-text-secondary">Calculating scores...</p>
                </div>
              )}
            </Card>
          </motion.div>

          {/* Hypothesis Rankings */}
          <motion.div variants={cardVariants}>
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-text-primary mb-4">
                Hypothesis Rankings
              </h2>
              <HypothesisRanking
                hypotheses={scenarioConfig.hypotheses || []}
                posteriors={posteriors}
              />
            </Card>
          </motion.div>
        </div>

        {/* Score Breakdown */}
        {showPayoffs && playerPayoff !== null && (
          <motion.div
            variants={cardVariants}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6"
          >
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-text-primary mb-4">
                Your Score Breakdown
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-surface-2">
                  <span className="text-text-secondary">Betting Payoff</span>
                  <span className={`text-lg font-semibold ${playerPayoff >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {playerPayoff >= 0 ? '+' : ''}{playerPayoff.toFixed(1)} credits
                  </span>
                </div>
                {predictionSubmitted && predictionResults.length > 0 && (
                  <div className="flex justify-between items-center py-2 border-b border-surface-2">
                    <span className="text-text-secondary">
                      Prediction Bonus ({predictionResults.filter(r => r.correct).length}/{predictionResults.length} correct)
                    </span>
                    <span className={`text-lg font-semibold ${predictionBonus >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {predictionBonus >= 0 ? '+' : ''}{predictionBonus} points
                    </span>
                  </div>
                )}
                <div className="flex justify-between items-center py-2">
                  <span className="text-text-primary font-semibold">Total Score</span>
                  <span className={`text-xl font-bold ${(playerPayoff + predictionBonus) >= 0 ? 'text-accent' : 'text-red-500'}`}>
                    {(playerPayoff + predictionBonus) >= 0 ? '+' : ''}{(playerPayoff + predictionBonus).toFixed(1)}
                  </span>
                </div>
              </div>
            </Card>
          </motion.div>
        )}

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

      {/* Victory Overlay */}
      <VictoryOverlay
        show={showVictoryOverlay}
        playerRank={playerRank}
        totalCompetitors={leaderboard.length}
        playerPayoff={playerPayoff || 0}
        predictionBonus={predictionSubmitted ? predictionBonus : 0}
        winnerName={leaderboard[0]?.isPlayer ? undefined : leaderboard[0]?.name}
        onClose={() => setShowVictoryOverlay(false)}
      />
    </motion.div>
  );
}
