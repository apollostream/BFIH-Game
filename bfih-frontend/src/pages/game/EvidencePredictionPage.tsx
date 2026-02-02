import { useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../../components/layout/PageContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { PhaseIndicator } from '../../components/game/PhaseIndicator';
import { PredictionCard } from '../../components/game/PredictionCard';
import { useGameStore, usePredictionStore, useAnalysisStore } from '../../stores';
import { usePhaseNavigation } from '../../hooks';
import { pageVariants, staggerContainerVariants, cardVariants } from '../../utils';

export function EvidencePredictionPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();
  const {
    scenarioConfig,
    setPhase,
  } = useGameStore();
  const {
    predictions,
    submitted,
    initializeForScenario,
    setPrediction,
    submitPredictions,
    getPredictionCount,
  } = usePredictionStore();
  const { currentAnalysis } = useAnalysisStore();
  const { handlePhaseClick, completedPhases, furthestPhase, isPhaseNavigable } = usePhaseNavigation();

  // Get scenario ID for initialization
  const currentScenarioId = scenarioConfig?.scenario_id || scenarioConfig?.scenario_metadata?.scenario_id;

  useEffect(() => {
    setPhase('prediction');
    // Initialize predictions for this scenario
    if (currentScenarioId) {
      initializeForScenario(currentScenarioId);
    }
  }, [setPhase, currentScenarioId, initializeForScenario]);

  // Get clusters for predictions - check analysis metadata first, then scenarioConfig
  const clusters = useMemo(() => {
    return currentAnalysis?.metadata?.evidence_clusters
      || scenarioConfig?.evidence_clusters
      || scenarioConfig?.evidence?.clusters
      || [];
  }, [currentAnalysis, scenarioConfig]);

  const hypotheses = scenarioConfig?.hypotheses || [];
  const predictionCount = getPredictionCount();
  const allClustersHavePredictions = predictionCount === clusters.length;

  const handleSubmit = () => {
    submitPredictions();
    navigate(`/game/${scenarioId}/evidence`);
  };

  const handleSkip = () => {
    // Allow skipping without making predictions
    navigate(`/game/${scenarioId}/evidence`);
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
          currentPhase="prediction"
          completedPhases={completedPhases}
          furthestPhase={furthestPhase}
          isPhaseNavigable={isPhaseNavigable}
          onPhaseClick={handlePhaseClick}
          className="mb-8"
        />

        {/* Title */}
        <motion.div variants={cardVariants} className="text-center mb-8">
          <h1 className="text-3xl font-bold text-text-primary mb-2">
            Evidence Prediction
          </h1>
          <p className="text-lg text-text-secondary">
            Predict what the evidence will show before seeing it
          </p>
        </motion.div>

        {/* Instructions */}
        <motion.div variants={cardVariants} className="mb-8">
          <Card variant="glass" className="p-6">
            <h2 className="text-lg font-semibold text-text-primary mb-3">
              How This Works
            </h2>
            <ul className="space-y-2 text-text-secondary">
              <li className="flex items-start gap-2">
                <span className="text-accent">1.</span>
                <span>For each evidence cluster, predict which hypothesis it will most support</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-accent">2.</span>
                <span>Set your confidence level - high confidence earns more points if correct, but costs points if wrong</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-accent">3.</span>
                <span>After submitting, you'll see the actual evidence and learn how accurate your predictions were</span>
              </li>
            </ul>
            <div className="mt-4 p-3 bg-surface-2 rounded-lg">
              <p className="text-sm text-text-muted">
                <strong className="text-text-primary">Scoring:</strong>{' '}
                Correct prediction: +15 pts | High confidence correct: +25 pts | High confidence wrong: -5 pts
              </p>
            </div>
          </Card>
        </motion.div>

        {/* Progress */}
        <motion.div variants={cardVariants} className="mb-6">
          <div className="flex items-center justify-between">
            <span className="text-text-primary font-medium">
              Predictions: {predictionCount} / {clusters.length}
            </span>
            {predictionCount === clusters.length && (
              <span className="text-green-500 text-sm">All clusters predicted!</span>
            )}
          </div>
          <div className="mt-2 h-2 bg-surface-2 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(predictionCount / clusters.length) * 100}%` }}
              className="h-full bg-accent rounded-full"
            />
          </div>
        </motion.div>

        {/* Prediction Cards */}
        <motion.div
          variants={staggerContainerVariants}
          initial="initial"
          animate="animate"
          className="space-y-4 mb-8"
        >
          {clusters.map((cluster) => (
            <motion.div key={cluster.cluster_id} variants={cardVariants}>
              <PredictionCard
                clusterId={cluster.cluster_id}
                clusterName={cluster.cluster_name}
                clusterDescription={cluster.description}
                hypotheses={hypotheses}
                prediction={predictions[cluster.cluster_id] || null}
                onPredictionChange={setPrediction}
                disabled={submitted}
              />
            </motion.div>
          ))}
        </motion.div>

        {/* No Clusters Message */}
        {clusters.length === 0 && (
          <Card className="p-8 text-center mb-8">
            <p className="text-text-secondary">
              No evidence clusters available for this scenario.
            </p>
            <Button
              className="mt-4"
              onClick={() => navigate(`/game/${scenarioId}/evidence`)}
            >
              Continue to Evidence
            </Button>
          </Card>
        )}

        {/* Navigation */}
        {clusters.length > 0 && (
          <motion.div
            variants={cardVariants}
            className="flex justify-between items-center"
          >
            <Button
              variant="ghost"
              onClick={() => navigate(`/game/${scenarioId}/betting`)}
            >
              Back to Betting
            </Button>
            <div className="flex items-center gap-4">
              <Button
                variant="secondary"
                onClick={handleSkip}
              >
                Skip Predictions
              </Button>
              <Button
                size="lg"
                onClick={handleSubmit}
                disabled={submitted}
              >
                {allClustersHavePredictions
                  ? 'Submit & See Evidence'
                  : `Submit ${predictionCount} Predictions`}
              </Button>
            </div>
          </motion.div>
        )}
      </PageContainer>
    </motion.div>
  );
}
