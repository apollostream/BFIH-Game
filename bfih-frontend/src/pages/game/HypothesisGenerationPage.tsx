import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../../components/layout/PageContainer';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { PhaseIndicator } from '../../components/game/PhaseIndicator';
import { HypothesisCard } from '../../components/game/HypothesisCard';
import { Badge, DomainBadge } from '../../components/ui/Badge';
import { useGameStore } from '../../stores';
import { pageVariants, staggerContainerVariants, cardVariants } from '../../utils';

export function HypothesisGenerationPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();
  const { scenarioConfig, setPhase } = useGameStore();

  useEffect(() => {
    setPhase('hypotheses');
  }, [setPhase]);

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

  const forcingFunctions = scenarioConfig.forcing_functions_log;

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <PageContainer>
        {/* Phase Indicator */}
        <PhaseIndicator currentPhase="hypotheses" className="mb-8" />

        {/* Title */}
        <motion.div variants={cardVariants} className="text-center mb-8">
          <h1 className="text-3xl font-bold text-text-primary mb-2">
            Hypothesis Generation
          </h1>
          <p className="text-lg text-text-secondary">
            AI-generated hypotheses using BFIH forcing functions
          </p>
        </motion.div>

        {/* Forcing Functions Log */}
        {forcingFunctions && (
          <motion.div variants={cardVariants} className="mb-8">
            <Card variant="bordered" className="p-6">
              <h2 className="text-lg font-semibold text-text-primary mb-4">
                Forcing Functions Applied
              </h2>
              <div className="space-y-4">
                {/* Ontological Scan */}
                {forcingFunctions.ontological_scan && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="primary">Ontological Scan</Badge>
                      <span className="text-sm text-text-muted">
                        7 Domain Coverage
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {forcingFunctions.ontological_scan.domains_covered?.map((domain) => (
                        <DomainBadge key={domain} domain={domain} />
                      ))}
                    </div>
                    {(forcingFunctions.ontological_scan.gaps_identified?.length ?? 0) > 0 && (
                      <p className="mt-2 text-sm text-warning">
                        Gaps: {forcingFunctions.ontological_scan.gaps_identified?.join(', ')}
                      </p>
                    )}
                  </div>
                )}

                {/* Ancestral Check */}
                {forcingFunctions.ancestral_check && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="secondary">Ancestral Check</Badge>
                      <span className="text-sm text-text-muted">
                        Historical Solutions
                      </span>
                    </div>
                    <p className="text-sm text-text-secondary">
                      {forcingFunctions.ancestral_check.historical_solutions?.join('; ')}
                    </p>
                  </div>
                )}

                {/* Paradigm Inversion */}
                {forcingFunctions.paradigm_inversion && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="warning">Paradigm Inversion</Badge>
                      <span className="text-sm text-text-muted">
                        Inverse Hypotheses
                      </span>
                    </div>
                    <ul className="text-sm text-text-secondary list-disc list-inside">
                      {Array.isArray(forcingFunctions.paradigm_inversion)
                        ? forcingFunctions.paradigm_inversion.map((inv, i) => (
                            <li key={i}>
                              {inv.inverse_paradigm && `${inv.inverse_paradigm}: `}
                              {inv.generated_hypothesis_id || inv.inverse_hypotheses?.join(', ')}
                            </li>
                          ))
                        : forcingFunctions.paradigm_inversion.inverse_hypotheses?.map((hyp, i) => (
                            <li key={i}>{hyp}</li>
                          ))
                      }
                    </ul>
                  </div>
                )}

                {/* MECE Synthesis */}
                {forcingFunctions.mece_synthesis && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="success">MECE Synthesis</Badge>
                      <span className="text-sm text-text-muted">
                        {forcingFunctions.mece_synthesis.is_mece ? 'Verified' : 'Needs Review'}
                      </span>
                    </div>
                    {forcingFunctions.mece_synthesis.notes && (
                      <p className="text-sm text-text-secondary">
                        {forcingFunctions.mece_synthesis.notes}
                      </p>
                    )}
                  </div>
                )}
              </div>
            </Card>
          </motion.div>
        )}

        {/* Hypotheses */}
        <motion.div variants={cardVariants} className="mb-8">
          <h2 className="text-xl font-semibold text-text-primary mb-4">
            Generated Hypotheses
          </h2>
          <p className="text-text-secondary mb-6">
            These hypotheses form a MECE (Mutually Exclusive, Collectively Exhaustive) set.
            H0 is the catch-all hypothesis representing "none of the above."
          </p>

          <motion.div
            variants={staggerContainerVariants}
            initial="initial"
            animate="animate"
            className="grid gap-4"
          >
            {scenarioConfig.hypotheses?.map((hypothesis) => (
              <motion.div key={hypothesis.id} variants={cardVariants}>
                <HypothesisCard
                  hypothesis={hypothesis}
                  variant="detailed"
                />
              </motion.div>
            ))}
          </motion.div>
        </motion.div>

        {/* Navigation */}
        <motion.div
          variants={cardVariants}
          className="flex justify-between items-center"
        >
          <Button
            variant="ghost"
            onClick={() => navigate(`/game/${scenarioId}/setup`)}
          >
            Back to Setup
          </Button>
          <Button
            size="lg"
            onClick={() => navigate(`/game/${scenarioId}/priors`)}
          >
            Continue to Priors
          </Button>
        </motion.div>
      </PageContainer>
    </motion.div>
  );
}
