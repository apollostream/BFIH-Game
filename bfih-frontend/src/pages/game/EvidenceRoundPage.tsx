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
import { useGameStore, useBettingStore, useAnalysisStore } from '../../stores';
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

  const [revealedClusters, setRevealedClusters] = useState<string[]>([]);
  const [isRevealing, setIsRevealing] = useState(false);

  const currentRound = parseInt(roundParam || '1', 10);

  useEffect(() => {
    setPhase('evidence');
  }, [setPhase]);

  // Get clusters for this round - check analysis metadata first, then scenarioConfig
  const clusters = useMemo(() => {
    return currentAnalysis?.metadata?.evidence_clusters
      || scenarioConfig?.evidence_clusters
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

  const allRevealed = revealedClusters.length === clusters.length;
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
        <PhaseIndicator currentPhase="evidence" className="mb-8" />

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
            onClick={() => navigate(`/game/${scenarioId}/betting`)}
          >
            Back to Betting
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
