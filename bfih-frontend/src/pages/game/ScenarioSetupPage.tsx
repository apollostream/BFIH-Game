import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../../components/layout/PageContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { PhaseIndicator } from '../../components/game/PhaseIndicator';
import { ParadigmCard } from '../../components/game/ParadigmCard';
import { Skeleton } from '../../components/ui/Skeleton';
import { useGameStore, useAnalysisStore } from '../../stores';
import { usePhaseNavigation } from '../../hooks';
import { getScenario, getAnalysis } from '../../api';
import { pageVariants, staggerContainerVariants, cardVariants } from '../../utils';

export function ScenarioSetupPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const {
    scenarioId: storeScenarioId,
    scenarioConfig,
    selectedParadigms,
    toggleParadigm,
    setPhase,
    loadScenario,
  } = useGameStore();
  const { setCurrentAnalysis } = useAnalysisStore();
  const { handlePhaseClick, completedPhases, furthestPhase, isPhaseNavigable } = usePhaseNavigation();

  // Load scenario from API if not in store or different scenario
  useEffect(() => {
    async function fetchScenario() {
      if (!scenarioId) return;

      // Skip if we already have this scenario loaded
      if (storeScenarioId === scenarioId && scenarioConfig) {
        return;
      }

      setLoading(true);
      setError(null);

      try {
        // Fetch scenario config
        const config = await getScenario(scenarioId);
        loadScenario(config);

        // Try to fetch analysis result (may not exist)
        try {
          const analysis = await getAnalysis(scenarioId);
          if (analysis && !('error' in analysis)) {
            setCurrentAnalysis(analysis);
          }
        } catch {
          // Analysis not found is OK - scenario can work without it
          console.log('No analysis result for scenario:', scenarioId);
        }
      } catch (err) {
        console.error('Failed to load scenario:', err);
        setError(err instanceof Error ? err.message : 'Failed to load scenario');
      } finally {
        setLoading(false);
      }
    }

    fetchScenario();
  }, [scenarioId, storeScenarioId, scenarioConfig, loadScenario, setCurrentAnalysis]);

  useEffect(() => {
    setPhase('setup');
  }, [setPhase]);

  const handleContinue = () => {
    if (selectedParadigms.length > 0) {
      navigate(`/game/${scenarioId}/hypotheses`);
    }
  };

  // Loading state
  if (loading) {
    return (
      <PageContainer>
        <div className="mb-8">
          <Skeleton className="h-16 w-full" />
        </div>
        <div className="text-center mb-8">
          <Skeleton className="h-10 w-64 mx-auto mb-2" />
          <Skeleton className="h-6 w-96 mx-auto" />
        </div>
        <Skeleton className="h-32 w-full mb-8" />
        <div className="grid md:grid-cols-2 gap-4 mb-8">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
      </PageContainer>
    );
  }

  // Error state
  if (error) {
    return (
      <PageContainer className="flex items-center justify-center min-h-[60vh]">
        <Card className="p-8 text-center max-w-md">
          <div className="text-red-500 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-text-primary mb-2">Failed to Load Scenario</h2>
          <p className="text-text-secondary mb-4">{error}</p>
          <div className="flex gap-4 justify-center">
            <Button variant="ghost" onClick={() => navigate('/library')}>
              Back to Library
            </Button>
            <Button onClick={() => window.location.reload()}>
              Try Again
            </Button>
          </div>
        </Card>
      </PageContainer>
    );
  }

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
          currentPhase="setup"
          completedPhases={completedPhases}
          furthestPhase={furthestPhase}
          isPhaseNavigable={isPhaseNavigable}
          onPhaseClick={handlePhaseClick}
          className="mb-8"
        />

        {/* Title */}
        <motion.div
          variants={cardVariants}
          className="text-center mb-8"
        >
          <h1 className="text-3xl font-bold text-text-primary mb-2">
            Scenario Setup
          </h1>
          <p className="text-lg text-text-secondary">
            Review the proposition and select your epistemic paradigms
          </p>
        </motion.div>

        {/* Proposition */}
        <motion.div variants={cardVariants}>
          <Card variant="glass" className="p-6 mb-8">
            <h2 className="text-sm font-medium text-text-muted uppercase tracking-wide mb-2">
              Proposition Under Analysis
            </h2>
            <p className="text-xl text-text-primary font-medium">
              "{scenarioConfig.proposition || scenarioConfig.scenario_narrative?.research_question || scenarioConfig.scenario_narrative?.title || scenarioConfig.narrative}"
            </p>
          </Card>
        </motion.div>

        {/* Narrative Context */}
        {scenarioConfig.scenario_narrative?.background && (
          <motion.div variants={cardVariants}>
            <Card className="p-6 mb-8">
              <h2 className="text-sm font-medium text-text-muted uppercase tracking-wide mb-2">
                Context
              </h2>
              <p className="text-text-secondary leading-relaxed">
                {scenarioConfig.scenario_narrative.background}
              </p>
            </Card>
          </motion.div>
        )}

        {/* Paradigm Selection */}
        <motion.div variants={cardVariants} className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-text-primary">
              Epistemic Paradigms
            </h2>
            <span className="text-sm text-text-muted">
              {selectedParadigms.length} of {scenarioConfig.paradigms?.length || 0} selected
            </span>
          </div>
          <p className="text-text-secondary mb-6">
            Each paradigm represents a different worldview or interpretive lens.
            Select the paradigms you want to analyze this proposition through.
          </p>

          <motion.div
            variants={staggerContainerVariants}
            initial="initial"
            animate="animate"
            className="grid md:grid-cols-2 gap-4"
          >
            {scenarioConfig.paradigms?.map((paradigm) => (
              <motion.div key={paradigm.id} variants={cardVariants}>
                <ParadigmCard
                  paradigm={paradigm}
                  selected={selectedParadigms.includes(paradigm.id)}
                  onClick={() => toggleParadigm(paradigm.id)}
                />
              </motion.div>
            ))}
          </motion.div>
        </motion.div>

        {/* Action */}
        <motion.div
          variants={cardVariants}
          className="flex justify-between items-center"
        >
          <Button variant="ghost" onClick={() => navigate('/library')}>
            Back to Library
          </Button>
          <Button
            size="lg"
            onClick={handleContinue}
            disabled={selectedParadigms.length === 0}
          >
            Continue to Hypotheses
          </Button>
        </motion.div>
      </PageContainer>
    </motion.div>
  );
}
