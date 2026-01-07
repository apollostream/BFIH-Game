import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../../components/layout/PageContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { PhaseIndicator } from '../../components/game/PhaseIndicator';
import { ParadigmCard } from '../../components/game/ParadigmCard';
import { useGameStore } from '../../stores';
import { usePhaseNavigation } from '../../hooks';
import { pageVariants, staggerContainerVariants, cardVariants } from '../../utils';

export function ScenarioSetupPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();
  const {
    scenarioConfig,
    selectedParadigms,
    toggleParadigm,
    setPhase,
  } = useGameStore();
  const { handlePhaseClick, completedPhases } = usePhaseNavigation();

  useEffect(() => {
    setPhase('setup');
  }, [setPhase]);

  const handleContinue = () => {
    if (selectedParadigms.length > 0) {
      navigate(`/game/${scenarioId}/hypotheses`);
    }
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
          currentPhase="setup"
          completedPhases={completedPhases}
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
              "{scenarioConfig.proposition || scenarioConfig.narrative}"
            </p>
          </Card>
        </motion.div>

        {/* Narrative Context */}
        {scenarioConfig.narrative && scenarioConfig.proposition && (
          <motion.div variants={cardVariants}>
            <Card className="p-6 mb-8">
              <h2 className="text-sm font-medium text-text-muted uppercase tracking-wide mb-2">
                Context
              </h2>
              <p className="text-text-secondary leading-relaxed">
                {scenarioConfig.narrative}
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
