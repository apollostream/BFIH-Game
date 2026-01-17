import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useGameStore } from '../stores';
import { useAnalysisStore } from '../stores/analysisStore';
import { getAnalysisStatus, getAnalysis, storeScenario } from '../api';
import { pageVariants } from '../utils';
import type { BFIHAnalysisResult } from '../types';

// All phases in order (autonomous mode includes 0a-0c, then 1-5)
const ANALYSIS_PHASES = [
  { id: 'paradigms', label: 'Generating Paradigms', icon: '🎭' },
  { id: 'hypotheses', label: 'Creating Hypotheses', icon: '💡' },
  { id: 'priors', label: 'Assigning Priors', icon: '🎲' },
  { id: 'methodology', label: 'Retrieving Methodology', icon: '📚' },
  { id: 'evidence', label: 'Gathering Evidence', icon: '🔍' },
  { id: 'likelihoods', label: 'Assigning Likelihoods', icon: '⚖️' },
  { id: 'computation', label: 'Computing Posteriors', icon: '📊' },
  { id: 'report', label: 'Writing Report', icon: '📝' },
];

// Extract phase from status string like "processing:phase:evidence" or "processing:phase:evidence:3/10"
function extractPhaseFromStatus(status: string | undefined | null): { phase: string | null; detail: string | null } {
  if (!status) return { phase: null, detail: null };
  // Format: "processing:phase:XXX" or "processing:phase:XXX:detail" -> extract XXX and optional detail
  const match = status.match(/processing:phase:(\w+)(?::(.+))?/);
  if (match) {
    return { phase: match[1], detail: match[2] || null };
  }
  return { phase: null, detail: null };
}

// Get phase index from phase ID
function getPhaseIndex(phaseId: string | null): number {
  if (!phaseId) return 0;
  const index = ANALYSIS_PHASES.findIndex(p => p.id === phaseId);
  return index >= 0 ? index : 0;
}

// Helper to normalize status string
function normalizeStatus(status: string | undefined | null): 'processing' | 'completed' | 'failed' | 'auth_error' {
  if (!status) return 'processing';
  const s = status.toLowerCase().trim();
  if (s === 'completed') return 'completed';
  if (s.startsWith('auth_error')) return 'auth_error'; // Will trigger immediate redirect
  if (s.startsWith('failed')) return 'failed';
  return 'processing';
}

export function AnalysisInProgressPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { loadScenario } = useGameStore();
  const { cacheResult, pendingProposition } = useAnalysisStore();

  const [status, setStatus] = useState<'processing' | 'completed' | 'failed' | 'auth_error'>('processing');
  const [rawStatus, setRawStatus] = useState<string>(''); // For debugging
  const [result, setResult] = useState<BFIHAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);
  const [phaseDetail, setPhaseDetail] = useState<string | null>(null); // e.g., "3/10" for search progress
  const [pollCount, setPollCount] = useState(0);
  const [showDebug, setShowDebug] = useState(false);

  // Ref to prevent duplicate navigation
  const hasNavigated = useRef(false);
  const isPolling = useRef(false);

  // Navigate to game
  const navigateToGame = useCallback((scenarioId: string, config: BFIHAnalysisResult['scenario_config']) => {
    if (hasNavigated.current) {
      console.log('Navigation already triggered, skipping');
      return;
    }
    hasNavigated.current = true;

    try {
      console.log('Navigating to game:', scenarioId);

      const configWithId = {
        ...config,
        scenario_id: scenarioId
      };

      loadScenario(configWithId);

      // Try react-router navigate first
      navigate(`/game/${scenarioId}/setup`);

      // Fallback after 500ms if still on same page
      setTimeout(() => {
        if (window.location.pathname.includes('/analysis/')) {
          console.log('React Router navigate failed, using window.location');
          window.location.href = `/game/${scenarioId}/setup`;
        }
      }, 500);
    } catch (err) {
      console.error('Navigation error:', err);
      hasNavigated.current = false; // Allow retry
      window.location.href = `/game/${scenarioId}/setup`;
    }
  }, [loadScenario, navigate]);

  // Direct polling function
  const checkStatus = useCallback(async () => {
    if (!id || isPolling.current) return;
    isPolling.current = true;

    try {
      setPollCount(c => c + 1);
      const statusResponse = await getAnalysisStatus(id);
      setRawStatus(JSON.stringify(statusResponse, null, 2));
      console.log('Status response:', statusResponse);

      const normalized = normalizeStatus(statusResponse.status);

      // Extract real phase from status (e.g., "processing:phase:evidence" -> "evidence")
      const { phase: currentPhase, detail } = extractPhaseFromStatus(statusResponse.status);
      if (currentPhase) {
        const phaseIdx = getPhaseIndex(currentPhase);
        setCurrentPhaseIndex(phaseIdx);
        setPhaseDetail(detail); // e.g., "3/10" for search progress
      }

      if (normalized === 'completed') {
        console.log('Status is completed, fetching full result...');
        setStatus('completed');

        // Fetch full result
        try {
          const fullResult = await getAnalysis(id);
          console.log('Full result received:', fullResult?.scenario_id);
          setResult(fullResult);

          // Cache the result in the analysis store for other pages to access
          cacheResult(fullResult);

          // Store scenario to backend for Library access
          try {
            const config = fullResult.scenario_config;
            await storeScenario({
              scenario_id: fullResult.scenario_id,
              title: config?.proposition || config?.narrative || 'Untitled Analysis',
              domain: config?.paradigms?.[0]?.name || 'General',
              difficulty_level: 'intermediate',
              scenario_config: config,
              model: fullResult.metadata?.model,
            });
            console.log('Scenario stored to library:', fullResult.scenario_id);
          } catch (storeErr) {
            // Non-fatal: log but don't block navigation
            console.warn('Failed to store scenario to library:', storeErr);
          }

          // Navigate immediately after setting result
          if (fullResult?.scenario_id) {
            navigateToGame(fullResult.scenario_id, fullResult.scenario_config);
          }
        } catch (fetchErr) {
          console.error('Failed to fetch full result:', fetchErr);
          setError(`Failed to fetch result: ${fetchErr instanceof Error ? fetchErr.message : 'Unknown error'}`);
        }
      } else if (normalized === 'auth_error') {
        // Immediately clear credentials and redirect to setup
        console.log('Auth error detected - clearing credentials and redirecting to setup');
        localStorage.removeItem('bfih_openai_api_key');
        localStorage.removeItem('bfih_vector_store_id');
        localStorage.removeItem('bfih_setup_complete');
        // Force reload to show setup modal
        window.location.href = '/';
        return;
      } else if (normalized === 'failed') {
        setStatus('failed');
        setError(statusResponse.error || statusResponse.status || 'Analysis failed');
      } else {
        setStatus('processing');
      }
    } catch (err) {
      console.error('Status check error:', err);
      setError(err instanceof Error ? err.message : 'Failed to check status');
    } finally {
      isPolling.current = false;
    }
  }, [id, navigateToGame, cacheResult]);

  // Polling effect - only runs once on mount, uses ref to track status
  const statusRef = useRef(status);
  statusRef.current = status;

  useEffect(() => {
    if (!id) return;

    console.log('Starting polling for:', id);

    // Initial check
    checkStatus();

    // Set up polling interval
    const interval = setInterval(() => {
      // Check ref for current status (not closure)
      if (statusRef.current !== 'completed' && statusRef.current !== 'failed') {
        checkStatus();
      }
    }, 3000);

    return () => {
      console.log('Clearing polling interval');
      clearInterval(interval);
    };
  }, [id, checkStatus]);

  // Timer for elapsed time
  useEffect(() => {
    if (status === 'completed' || status === 'failed') return;

    const timer = setInterval(() => {
      setElapsedTime(t => t + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [status]);

  // Phase progression is now driven by real backend status updates
  // (extracted from status response in checkStatus callback)

  // Manual start game handler
  const handleStartGame = useCallback(() => {
    if (!result) {
      console.error('Cannot start game: no result');
      return;
    }
    hasNavigated.current = false; // Allow manual navigation
    navigateToGame(result.scenario_id, result.scenario_config);
  }, [result, navigateToGame]);

  const isComplete = status === 'completed';
  const isFailed = status === 'failed';
  // Note: auth_error triggers immediate redirect in checkStatus, so no UI handling needed
  const isProcessing = !isComplete && !isFailed;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="min-h-screen flex items-center justify-center py-12"
    >
      <PageContainer className="max-w-2xl mx-auto">
        <Card variant="elevated" className="p-8 md:p-12 rounded-2xl relative overflow-hidden">
          {/* Background decorative elements */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            <motion.div
              className="absolute -top-24 -right-24 w-48 h-48 rounded-full bg-accent/10 blur-3xl"
              animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.5, 0.3] }}
              transition={{ duration: 4, repeat: Infinity }}
            />
            <motion.div
              className="absolute -bottom-24 -left-24 w-48 h-48 rounded-full bg-paradigm-k2/10 blur-3xl"
              animate={{ scale: [1.2, 1, 1.2], opacity: [0.3, 0.5, 0.3] }}
              transition={{ duration: 5, repeat: Infinity }}
            />
          </div>

          <div className="relative z-10">
            {/* Animated Icon */}
            <div className="flex justify-center mb-8">
              {isFailed ? (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-28 h-28 rounded-full bg-error/20 border-2 border-error/40 flex items-center justify-center"
                >
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-error">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M15 9l-6 6M9 9l6 6" />
                  </svg>
                </motion.div>
              ) : isComplete ? (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-28 h-28 rounded-full bg-success/20 border-2 border-success/40 flex items-center justify-center glow-success"
                >
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-success">
                    <path d="M5 13l4 4L19 7" />
                  </svg>
                </motion.div>
              ) : (
                <div className="relative w-28 h-28">
                  <motion.div
                    className="absolute inset-0 rounded-full border-4 border-surface-3"
                    style={{
                      borderTopColor: 'var(--color-accent)',
                      borderRightColor: 'var(--color-paradigm-k2)',
                    }}
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                  />
                  <motion.div
                    className="absolute inset-4 rounded-full bg-gradient-to-br from-accent/20 to-paradigm-k2/20"
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <AnimatePresence mode="wait">
                      <motion.span
                        key={currentPhaseIndex}
                        initial={{ scale: 0.5, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.5, opacity: 0 }}
                        className="text-4xl"
                      >
                        {ANALYSIS_PHASES[currentPhaseIndex]?.icon || '🔬'}
                      </motion.span>
                    </AnimatePresence>
                  </div>
                </div>
              )}
            </div>

            {/* Proposition Display */}
            {pendingProposition && (
              <div className="text-center mb-6">
                <div className="inline-block px-4 py-3 rounded-xl bg-surface-2/80 border border-border/50 max-w-xl">
                  <div className="text-xs text-text-muted uppercase tracking-wider mb-1">
                    Analyzing
                  </div>
                  <p className="text-text-primary font-medium text-lg leading-relaxed">
                    "{pendingProposition}"
                  </p>
                </div>
              </div>
            )}

            {/* Status Text */}
            <div className="text-center mb-8">
              <h2 className="text-2xl md:text-3xl font-bold text-text-primary mb-3">
                {isFailed ? 'Analysis Failed' :
                 isComplete ? 'Analysis Complete!' :
                 'Analysis in Progress'}
              </h2>
              <AnimatePresence mode="wait">
                <motion.p
                  key={isProcessing ? currentPhaseIndex : status}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="text-lg text-text-secondary"
                >
                  {isFailed ? 'Something went wrong. Please try again.' :
                   isComplete ? 'Your analysis is ready!' :
                   (ANALYSIS_PHASES[currentPhaseIndex]?.label || 'Processing...') +
                   (phaseDetail ? ` (${phaseDetail})` : '')}
                </motion.p>
              </AnimatePresence>
            </div>

            {/* Phase Progress Steps */}
            {isProcessing && (
              <div className="mb-8">
                <div className="flex items-center justify-between mb-6">
                  {ANALYSIS_PHASES.map((phase, index) => {
                    const isActive = index === currentPhaseIndex;
                    const isDone = index < currentPhaseIndex;

                    return (
                      <div key={phase.id} className="flex flex-col items-center flex-1">
                        <motion.div
                          className={`w-10 h-10 rounded-full flex items-center justify-center text-lg transition-all duration-300 ${
                            isDone
                              ? 'bg-success/20 text-success border border-success/50'
                              : isActive
                              ? 'bg-accent/20 text-accent border border-accent/50 animate-pulse-glow'
                              : 'bg-surface-2 text-text-muted border border-border'
                          }`}
                          animate={isActive ? { scale: [1, 1.1, 1] } : {}}
                          transition={{ duration: 1, repeat: Infinity }}
                        >
                          {isDone ? '✓' : phase.icon}
                        </motion.div>
                        <div className={`text-xs mt-2 text-center max-w-[60px] ${
                          isActive ? 'text-accent font-medium' :
                          isDone ? 'text-success' : 'text-text-muted'
                        }`}>
                          {phase.label.split(' ')[0]}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Progress bar */}
                <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-accent via-paradigm-k2 to-paradigm-k3"
                    initial={{ width: '0%' }}
                    animate={{ width: `${((currentPhaseIndex + 1) / ANALYSIS_PHASES.length) * 100}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>
            )}

            {/* Timer */}
            {isProcessing && (
              <div className="text-center mb-8">
                <div className="inline-flex items-center gap-3 px-4 py-2 rounded-lg bg-surface-2 border border-border">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-text-muted">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M12 6v6l4 2" />
                  </svg>
                  <span className="text-text-secondary font-mono">
                    {formatTime(elapsedTime)}
                  </span>
                  <span className="text-text-muted text-sm">elapsed</span>
                </div>
              </div>
            )}

            {/* Error State */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 rounded-xl bg-error/10 border border-error/30 text-error text-center mb-6"
              >
                <div className="flex items-center justify-center gap-2 mb-1">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M12 8v4m0 4h.01" />
                  </svg>
                  <span className="font-medium">Error</span>
                </div>
                <p className="text-sm opacity-90">{error}</p>
              </motion.div>
            )}

            {/* Actions */}
            <div className="flex justify-center gap-4">
              {isFailed ? (
                <>
                  <Button variant="ghost" onClick={() => navigate('/')}>
                    Back to Home
                  </Button>
                  <Button onClick={() => {
                    setStatus('processing');
                    setError(null);
                    setCurrentPhaseIndex(0);
                    setElapsedTime(0);
                  }}>
                    Retry
                  </Button>
                </>
              ) : isComplete && result ? (
                <Button
                  size="lg"
                  className="px-8"
                  onClick={handleStartGame}
                >
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
              <div className="mt-8 text-center">
                <div className="text-xs text-text-muted mb-1">Analysis ID</div>
                <code className="text-xs bg-surface-2 px-3 py-1.5 rounded-lg text-text-secondary">
                  {id}
                </code>
                <button
                  onClick={() => setShowDebug(!showDebug)}
                  className="ml-2 text-xs text-text-muted hover:text-text-secondary underline"
                >
                  {showDebug ? 'Hide Debug' : 'Debug'}
                </button>
              </div>
            )}

            {/* Debug Panel */}
            {showDebug && (
              <div className="mt-4 p-4 bg-surface-2 rounded-lg text-left text-xs font-mono overflow-auto max-h-64">
                <div className="text-text-muted mb-2">Debug Info:</div>
                <div><span className="text-accent">Status:</span> {status}</div>
                <div><span className="text-accent">Poll Count:</span> {pollCount}</div>
                <div><span className="text-accent">Has Result:</span> {result ? 'yes' : 'no'}</div>
                <div><span className="text-accent">Scenario ID:</span> {result?.scenario_id || 'n/a'}</div>
                <div><span className="text-accent">Has Config:</span> {result?.scenario_config ? 'yes' : 'no'}</div>
                <div className="mt-2"><span className="text-accent">Raw Response:</span></div>
                <pre className="text-text-secondary whitespace-pre-wrap break-all">{rawStatus || 'waiting...'}</pre>
              </div>
            )}
          </div>
        </Card>
      </PageContainer>
    </motion.div>
  );
}
