import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Progress } from '../components/ui/Progress';
import { Button } from '../components/ui/Button';
import { useAnalysisStore, useGameStore } from '../stores';
import { pageVariants } from '../utils';

const PHASE_DESCRIPTIONS = {
  pending: 'Preparing analysis...',
  generating_paradigms: 'Generating epistemic paradigms (K1-K4)...',
  generating_hypotheses: 'Generating hypotheses and running forcing functions...',
  assigning_priors: 'AI is assigning prior probabilities...',
  gathering_evidence: 'Searching for evidence via web search...',
  assigning_likelihoods: 'Computing likelihood ratios for each hypothesis...',
  computing_posteriors: 'Running Bayesian computation...',
  generating_report: 'Writing the final BFIH report...',
  completed: 'Analysis complete!',
  failed: 'Analysis failed',
};

const PHASE_PROGRESS: Record<string, number> = {
  pending: 5,
  generating_paradigms: 15,
  generating_hypotheses: 30,
  assigning_priors: 45,
  gathering_evidence: 60,
  assigning_likelihoods: 75,
  computing_posteriors: 85,
  generating_report: 95,
  completed: 100,
  failed: 0,
};

export function AnalysisInProgressPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    currentAnalysis,
    analysisStatus,
    error,
    startPolling,
    stopPolling,
    isPolling: _isPolling
  } = useAnalysisStore();
  void _isPolling; // Reserved for future polling status UI indicator
  const { loadScenario } = useGameStore();

  useEffect(() => {
    if (id) {
      startPolling(id);
    }
    return () => stopPolling();
  }, [id, startPolling, stopPolling]);

  useEffect(() => {
    if (analysisStatus === 'completed' && currentAnalysis) {
      // Load the scenario into game store and navigate
      loadScenario(currentAnalysis.scenario_config);
      navigate(`/game/${currentAnalysis.scenario_config.scenario_id}/setup`);
    }
  }, [analysisStatus, currentAnalysis, loadScenario, navigate]);

  const progress = PHASE_PROGRESS[analysisStatus || 'pending'] || 0;
  const description = PHASE_DESCRIPTIONS[analysisStatus as keyof typeof PHASE_DESCRIPTIONS] || 'Processing...';

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <PageContainer className="max-w-2xl mx-auto flex items-center justify-center min-h-[60vh]">
        <Card variant="elevated" className="p-8 w-full">
          {/* Animated Icon */}
          <div className="flex justify-center mb-8">
            {analysisStatus === 'failed' ? (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="w-24 h-24 rounded-full bg-error/20 flex items-center justify-center"
              >
                <span className="text-4xl">❌</span>
              </motion.div>
            ) : analysisStatus === 'completed' ? (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1, rotate: 360 }}
                className="w-24 h-24 rounded-full bg-success/20 flex items-center justify-center"
              >
                <span className="text-4xl">✓</span>
              </motion.div>
            ) : (
              <div className="relative w-24 h-24">
                {/* Spinning outer ring */}
                <motion.div
                  className="absolute inset-0 rounded-full border-4 border-accent/30"
                  style={{ borderTopColor: 'var(--color-accent)' }}
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                />
                {/* Inner pulsing circle */}
                <motion.div
                  className="absolute inset-4 rounded-full bg-accent/20"
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
                {/* Center icon */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <motion.span
                    className="text-3xl"
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    🔬
                  </motion.span>
                </div>
              </div>
            )}
          </div>

          {/* Status Text */}
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-text-primary mb-2">
              {analysisStatus === 'failed' ? 'Analysis Failed' :
               analysisStatus === 'completed' ? 'Analysis Complete' :
               'Analysis in Progress'}
            </h2>
            <motion.p
              key={description}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-text-secondary"
            >
              {description}
            </motion.p>
          </div>

          {/* Progress Bar */}
          {analysisStatus !== 'failed' && (
            <div className="mb-6">
              <Progress value={progress} showLabel animated />
            </div>
          )}

          {/* Phase Steps */}
          <div className="grid grid-cols-4 gap-2 mb-6">
            {['Paradigms', 'Hypotheses', 'Evidence', 'Report'].map((phase, index) => {
              const phaseProgress = (index + 1) * 25;
              const isActive = progress >= phaseProgress - 25 && progress < phaseProgress;
              const isComplete = progress >= phaseProgress;

              return (
                <div
                  key={phase}
                  className={`text-center py-2 px-1 rounded-lg text-xs transition-all ${
                    isComplete
                      ? 'bg-success/20 text-success'
                      : isActive
                      ? 'bg-accent/20 text-accent'
                      : 'bg-surface-2 text-text-muted'
                  }`}
                >
                  <div className="font-medium">{phase}</div>
                  {isActive && (
                    <motion.div
                      className="w-1 h-1 rounded-full bg-current mx-auto mt-1"
                      animate={{ opacity: [0, 1, 0] }}
                      transition={{ duration: 1, repeat: Infinity }}
                    />
                  )}
                </div>
              );
            })}
          </div>

          {/* Error State */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 rounded-lg bg-error/10 border border-error text-error text-center mb-4"
            >
              {error}
            </motion.div>
          )}

          {/* Actions */}
          <div className="flex justify-center gap-4">
            {analysisStatus === 'failed' ? (
              <>
                <Button variant="ghost" onClick={() => navigate('/')}>
                  Try Again
                </Button>
                <Button onClick={() => id && startPolling(id)}>
                  Retry
                </Button>
              </>
            ) : analysisStatus === 'completed' ? (
              <Button onClick={() => currentAnalysis &&
                navigate(`/game/${currentAnalysis.scenario_config.scenario_id}/setup`)
              }>
                Start Game
              </Button>
            ) : (
              <Button variant="ghost" onClick={() => navigate('/')}>
                Cancel
              </Button>
            )}
          </div>

          {/* Analysis ID */}
          {id && (
            <div className="mt-6 text-center text-xs text-text-muted">
              Analysis ID: <code className="bg-surface-2 px-2 py-1 rounded">{id}</code>
            </div>
          )}
        </Card>
      </PageContainer>
    </motion.div>
  );
}
