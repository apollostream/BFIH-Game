import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { PageContainer } from '../../components/layout/PageContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { PhaseIndicator } from '../../components/game/PhaseIndicator';
import { EvidenceClusterCard } from '../../components/game/EvidenceCard';
import { EvidenceMatrixHeatmap } from '../../components/visualizations/EvidenceMatrixHeatmap';
import { HypothesisBarChart } from '../../components/visualizations/HypothesisBarChart';
import { BudgetBar, BetSummary } from '../../components/game/BettingSlider';
import { useGameStore, useBettingStore, useAnalysisStore, usePredictionStore } from '../../stores';
import { usePhaseNavigation } from '../../hooks';
import { pageVariants, staggerContainerVariants, cardVariants } from '../../utils';
import type { PosteriorsByParadigm } from '../../types';

export function EvidenceRoundPage() {
  const { scenarioId, round: roundParam } = useParams<{ scenarioId: string; round?: string }>();
  const navigate = useNavigate();
  const {
    scenarioConfig,
    selectedParadigms,
    activeParadigm,
    setActiveParadigm,
    setPhase,
  } = useGameStore();
  const { bets, budget, getTotalBet, raiseBet } = useBettingStore();
  const { currentAnalysis } = useAnalysisStore();
  const {
    submitted: predictionsSubmitted,
    results: predictionResults,
    totalBonus: predictionBonus,
    calculateResults: calculatePredictionResults,
  } = usePredictionStore();
  const { handlePhaseClick, completedPhases, furthestPhase, isPhaseNavigable } = usePhaseNavigation();

  const [revealedClusters, setRevealedClusters] = useState<string[]>([]);
  const [isRevealing, setIsRevealing] = useState(false);
  const [showPredictionResults, setShowPredictionResults] = useState(false);

  const currentRound = parseInt(roundParam || '1', 10);

  useEffect(() => {
    setPhase('evidence');
  }, [setPhase]);

  // Get clusters for this round - check analysis metadata first, then scenarioConfig
  // Note: Clusters can be at scenarioConfig.evidence_clusters (legacy) or scenarioConfig.evidence.clusters (current)
  const clusters = useMemo(() => {
    return currentAnalysis?.metadata?.evidence_clusters
      || scenarioConfig?.evidence_clusters
      || scenarioConfig?.evidence?.clusters
      || [];
  }, [currentAnalysis, scenarioConfig]);

  // Get evidence items to pass to cluster cards
  const evidenceItems = useMemo(() => {
    return currentAnalysis?.metadata?.evidence_items
      || scenarioConfig?.evidence?.items
      || [];
  }, [currentAnalysis, scenarioConfig]);

  // Build posteriors data (using priors initially, would be updated after evidence)
  // Support both 'priors' and 'priors_by_paradigm' field names
  const priorsSource = scenarioConfig?.priors || scenarioConfig?.priors_by_paradigm;

  const posteriorsData = useMemo((): PosteriorsByParadigm => {
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

  const revealNextCluster = () => {
    const unrevealedCluster = clusters.find(
      (c) => !revealedClusters.includes(c.cluster_id)
    );
    if (unrevealedCluster) {
      setIsRevealing(true);
      setTimeout(() => {
        setRevealedClusters((prev) => [...prev, unrevealedCluster.cluster_id]);
        setIsRevealing(false);
      }, 500);
    }
  };

  const revealAllClusters = () => {
    setRevealedClusters(clusters.map((c) => c.cluster_id));
  };

  const allRevealed = revealedClusters.length === clusters.length;

  // Calculate prediction results when all clusters are revealed
  useEffect(() => {
    if (allRevealed && predictionsSubmitted && predictionResults.length === 0) {
      calculatePredictionResults(clusters, activeParadigm);
      setShowPredictionResults(true);
    }
  }, [allRevealed, predictionsSubmitted, predictionResults.length, clusters, activeParadigm, calculatePredictionResults]);

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
          currentPhase="evidence"
          completedPhases={completedPhases}
          furthestPhase={furthestPhase}
          isPhaseNavigable={isPhaseNavigable}
          onPhaseClick={handlePhaseClick}
          className="mb-8"
        />

        {/* Title */}
        <motion.div variants={cardVariants} className="text-center mb-8">
          <h1 className="text-3xl font-bold text-text-primary mb-2">
            Evidence Round {currentRound}
          </h1>
          <p className="text-lg text-text-secondary">
            Review evidence and update your beliefs
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Reveal Controls */}
            <motion.div variants={cardVariants}>
              <Card className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-text-primary font-medium">
                      Evidence Clusters: {revealedClusters.length} / {clusters.length}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={revealNextCluster}
                      disabled={allRevealed || isRevealing}
                      loading={isRevealing}
                    >
                      Reveal Next
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={revealAllClusters}
                      disabled={allRevealed}
                    >
                      Reveal All
                    </Button>
                  </div>
                </div>
              </Card>
            </motion.div>

            {/* Evidence Clusters */}
            <motion.div
              variants={staggerContainerVariants}
              initial="initial"
              animate="animate"
              className="space-y-4"
            >
              <AnimatePresence mode="popLayout">
                {clusters.map((cluster) => {
                  const isRevealed = revealedClusters.includes(cluster.cluster_id);

                  return (
                    <motion.div
                      key={cluster.cluster_id}
                      variants={cardVariants}
                      initial={{ opacity: 0, height: 0 }}
                      animate={{
                        opacity: isRevealed ? 1 : 0.3,
                        height: 'auto',
                      }}
                      transition={{ duration: 0.3 }}
                    >
                      <EvidenceClusterCard
                        cluster={cluster}
                        evidenceItems={evidenceItems}
                        revealed={isRevealed}
                        hypotheses={scenarioConfig.hypotheses || []}
                        onClick={() => {
                          if (!isRevealed) {
                            setRevealedClusters((prev) => [...prev, cluster.cluster_id]);
                          }
                        }}
                      />
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </motion.div>

            {/* Prediction Results Summary */}
            {showPredictionResults && predictionResults.length > 0 && (
              <motion.div
                variants={cardVariants}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card className="p-6 border-2 border-accent">
                  <h3 className="text-lg font-semibold text-text-primary mb-4">
                    Prediction Results
                  </h3>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="text-center p-3 bg-surface-2 rounded-lg">
                      <div className="text-2xl font-bold text-accent">
                        {predictionResults.filter(r => r.correct).length} / {predictionResults.length}
                      </div>
                      <div className="text-sm text-text-secondary">Correct Predictions</div>
                    </div>
                    <div className="text-center p-3 bg-surface-2 rounded-lg">
                      <div className={`text-2xl font-bold ${predictionBonus >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {predictionBonus >= 0 ? '+' : ''}{predictionBonus}
                      </div>
                      <div className="text-sm text-text-secondary">Bonus Points</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {predictionResults.map((result) => {
                      const hypothesis = scenarioConfig.hypotheses?.find(h => h.id === result.predicted);
                      const actualHypothesis = scenarioConfig.hypotheses?.find(h => h.id === result.actual);
                      return (
                        <div
                          key={result.clusterId}
                          className={`p-3 rounded-lg ${result.correct ? 'bg-green-500/10' : 'bg-surface-2'}`}
                        >
                          <div className="flex justify-between items-start">
                            <div>
                              <span className="text-sm font-medium text-text-primary">
                                {result.clusterName}
                              </span>
                              <div className="text-xs text-text-secondary mt-1">
                                Predicted: {hypothesis?.name || result.predicted || 'None/Mixed'}
                                {result.actual && result.predicted !== result.actual && (
                                  <span className="ml-2">
                                    → Actual: {actualHypothesis?.name || result.actual || 'None/Mixed'}
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className={`text-sm font-semibold ${
                              result.points > 0 ? 'text-green-500' :
                              result.points < 0 ? 'text-red-500' : 'text-text-muted'
                            }`}>
                              {result.points > 0 ? '+' : ''}{result.points}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              </motion.div>
            )}

            {/* Evidence Matrix Heatmap */}
            {revealedClusters.length > 0 && (
              <motion.div
                variants={cardVariants}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <EvidenceMatrixHeatmap
                  hypotheses={scenarioConfig.hypotheses || []}
                  clusters={clusters.filter((c) =>
                    revealedClusters.includes(c.cluster_id)
                  )}
                  paradigms={paradigms}
                  activeParadigm={activeParadigm}
                  priorsByParadigm={priorsSource}
                  onParadigmChange={setActiveParadigm}
                />
              </motion.div>
            )}
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-4">
            <motion.div variants={cardVariants} className="sticky top-24">
              {/* Budget */}
              <BudgetBar budget={budget} spent={totalBet} />

              {/* Current Bets */}
              <div className="mt-4">
                <BetSummary
                  bets={bets}
                  hypotheses={scenarioConfig.hypotheses || []}
                  budget={budget}
                />
              </div>

              {/* Posterior Chart */}
              <div className="mt-4">
                <HypothesisBarChart
                  hypotheses={scenarioConfig.hypotheses || []}
                  posteriors={posteriorsData}
                  activeParadigm={activeParadigm}
                />
              </div>

              {/* Raise Bet Option */}
              {allRevealed && (
                <Card className="mt-4 p-4">
                  <h3 className="text-sm font-medium text-text-primary mb-2">
                    Raise Your Bets?
                  </h3>
                  <p className="text-xs text-text-secondary mb-3">
                    Based on the evidence, you can raise (but not lower) your bets.
                    Remaining budget: {budget - totalBet} credits
                  </p>
                  {scenarioConfig.hypotheses?.map((h) => (
                    <div key={h.id} className="flex items-center justify-between py-1">
                      <span className="text-sm text-text-primary">{h.id}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-text-muted">
                          {bets[h.id] || 0}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => raiseBet(h.id, 10)}
                          disabled={totalBet + 10 > budget}
                        >
                          +10
                        </Button>
                      </div>
                    </div>
                  ))}
                </Card>
              )}
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
            onClick={() => navigate(`/game/${scenarioId}/prediction`)}
          >
            Back to Predictions
          </Button>
          <Button
            size="lg"
            onClick={() => navigate(`/game/${scenarioId}/resolution`)}
            disabled={!allRevealed}
          >
            {allRevealed ? 'Continue to Resolution' : 'Reveal All Evidence First'}
          </Button>
        </motion.div>
      </PageContainer>
    </motion.div>
  );
}
