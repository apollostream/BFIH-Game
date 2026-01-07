import { useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../../components/layout/PageContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { PhaseIndicator } from '../../components/game/PhaseIndicator';
import { ParadigmSelector } from '../../components/game/ParadigmCard';
import { HypothesisCard } from '../../components/game/HypothesisCard';
import { BeliefSpaceRadar } from '../../components/visualizations/BeliefSpaceRadar';
import { useGameStore } from '../../stores';
import { pageVariants, staggerContainerVariants, cardVariants, formatPercent } from '../../utils';
import type { PosteriorsByParadigm } from '../../types';

export function PriorAssignmentPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();
  const {
    scenarioConfig,
    selectedParadigms,
    activeParadigm,
    setActiveParadigm,
    setPhase,
  } = useGameStore();

  useEffect(() => {
    setPhase('priors');
  }, [setPhase]);

  // Build priors data structure for visualization
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

  const paradigms = scenarioConfig.paradigms?.filter(
    (p) => selectedParadigms.includes(p.id)
  ) || [];

  const currentPriors = priorsSource?.[activeParadigm] || {};

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <PageContainer>
        {/* Phase Indicator */}
        <PhaseIndicator currentPhase="priors" className="mb-8" />

        {/* Title */}
        <motion.div variants={cardVariants} className="text-center mb-8">
          <h1 className="text-3xl font-bold text-text-primary mb-2">
            AI Prior Assignment
          </h1>
          <p className="text-lg text-text-secondary">
            Review how the AI has assigned prior probabilities under each paradigm
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Paradigm Selector */}
            <motion.div variants={cardVariants}>
              <Card className="p-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-text-primary">
                    Viewing Priors Under:
                  </h2>
                  <ParadigmSelector
                    paradigms={paradigms}
                    selectedId={activeParadigm}
                    onChange={setActiveParadigm}
                  />
                </div>
              </Card>
            </motion.div>

            {/* Prior Cards */}
            <motion.div
              variants={staggerContainerVariants}
              initial="initial"
              animate="animate"
              className="space-y-4"
            >
              {scenarioConfig.hypotheses?.map((hypothesis) => {
                const prior = currentPriors[hypothesis.id];
                const priorValue = typeof prior === 'number' ? prior : prior?.probability || 0;
                const justification = typeof prior === 'object' ? prior.justification : undefined;

                return (
                  <motion.div key={hypothesis.id} variants={cardVariants}>
                    <Card className="p-4">
                      <div className="flex items-start gap-4">
                        {/* Hypothesis info */}
                        <div className="flex-1">
                          <HypothesisCard
                            hypothesis={hypothesis}
                            variant="compact"
                          />
                        </div>

                        {/* Prior value */}
                        <div className="text-right">
                          <div className="text-2xl font-bold text-accent">
                            {formatPercent(priorValue)}
                          </div>
                          <div className="text-xs text-text-muted">
                            Prior P(H)
                          </div>
                        </div>
                      </div>

                      {/* Justification */}
                      {justification && (
                        <div className="mt-4 pt-4 border-t border-border">
                          <p className="text-sm text-text-secondary italic">
                            "{justification}"
                          </p>
                        </div>
                      )}
                    </Card>
                  </motion.div>
                );
              })}
            </motion.div>

            {/* Prior Sum Check */}
            <motion.div variants={cardVariants}>
              <Card variant="bordered" className="p-4">
                <div className="flex items-center justify-between">
                  <span className="text-text-secondary">
                    Sum of Priors (should equal 100%):
                  </span>
                  <span className="text-lg font-bold text-text-primary">
                    {formatPercent(
                      Object.values(currentPriors).reduce<number>(
                        (sum, p) => sum + (typeof p === 'number' ? p : p?.probability || 0),
                        0
                      )
                    )}
                  </span>
                </div>
              </Card>
            </motion.div>
          </div>

          {/* Sidebar - Radar Chart */}
          <div className="lg:col-span-1">
            <motion.div variants={cardVariants} className="sticky top-24">
              <BeliefSpaceRadar
                hypotheses={scenarioConfig.hypotheses || []}
                paradigms={paradigms}
                posteriors={priorsData}
                enabledParadigms={selectedParadigms}
              />

              {/* Paradigm Comparison */}
              <Card className="mt-4 p-4">
                <h3 className="text-sm font-medium text-text-muted mb-3">
                  Prior Distribution by Paradigm
                </h3>
                <div className="space-y-3">
                  {paradigms.map((paradigm) => {
                    const pPriors = priorsSource?.[paradigm.id] || {};
                    const topHypothesis = Object.entries(pPriors)
                      .map(([id, p]) => ({
                        id,
                        value: typeof p === 'number' ? p : p.probability || 0
                      }))
                      .sort((a, b) => b.value - a.value)[0];

                    return (
                      <div
                        key={paradigm.id}
                        className={`p-2 rounded-lg transition-colors ${
                          paradigm.id === activeParadigm
                            ? 'bg-accent/10 border border-accent'
                            : 'bg-surface-2'
                        }`}
                      >
                        <div className="text-sm font-medium text-text-primary">
                          {paradigm.name}
                        </div>
                        {topHypothesis && (
                          <div className="text-xs text-text-muted">
                            Favors {topHypothesis.id} ({formatPercent(topHypothesis.value)})
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
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
            onClick={() => navigate(`/game/${scenarioId}/hypotheses`)}
          >
            Back to Hypotheses
          </Button>
          <Button
            size="lg"
            onClick={() => navigate(`/game/${scenarioId}/betting`)}
          >
            Continue to Betting
          </Button>
        </motion.div>
      </PageContainer>
    </motion.div>
  );
}
