import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useGameStore } from '../stores';
import { useAnalysisStore } from '../stores/analysisStore';
import { getAnalysis } from '../api';
import { pageVariants } from '../utils';
import type { BFIHAnalysisResult, ProgressLogEntry } from '../types';

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
  const [pollCount, setPollCount] = useState(0);  // Now tracks SSE event count
  const [showDebug, setShowDebug] = useState(false);
  const [progressLog, setProgressLog] = useState<ProgressLogEntry[]>([]); // Real-time log from backend

  // Ref to prevent duplicate navigation
  const hasNavigated = useRef(false);

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


  // SSE connection for real-time updates
  useEffect(() => {
    if (!id) return;

    console.log('Starting SSE connection for:', id);

    // Use SSE for real-time updates (more reliable than polling)
    const apiBase = import.meta.env.VITE_API_URL || '';
    const eventSource = new EventSource(`${apiBase}/api/analysis-status/${id}/stream`);

    // Handler for processing SSE data (works for both named and unnamed events)
    const handleSSEData = (data: string) => {
      try {
        const statusResponse = JSON.parse(data);
        console.log('SSE parsed:', statusResponse?.sse_iteration, statusResponse?.progress_log_count);
        setRawStatus(JSON.stringify(statusResponse, null, 2));
        setPollCount(c => c + 1);

        // Update progress log
        if (statusResponse.progress_log) {
          setProgressLog(statusResponse.progress_log);
        }

        // Check for stale status
        if (statusResponse.is_stale && statusResponse.status?.startsWith('processing')) {
          console.log('Stale status detected');
          setStatus('failed');
          setError('Analysis appears stuck. Backend has not updated status in 5+ minutes.');
          eventSource.close();
          return;
        }

        const normalized = normalizeStatus(statusResponse.status);

        // Extract phase from status
        const { phase: currentPhase, detail } = extractPhaseFromStatus(statusResponse.status);
        if (currentPhase) {
          setCurrentPhaseIndex(getPhaseIndex(currentPhase));
          setPhaseDetail(detail);
        }

        if (normalized === 'completed') {
          console.log('Status is completed, fetching full result...');
          setStatus('completed');
          // Fetch full result
          getAnalysis(id).then(fullResult => {
            console.log('Full result received:', fullResult?.scenario_id);
            setResult(fullResult);
            cacheResult(fullResult);
            if (fullResult?.scenario_id) {
              navigateToGame(fullResult.scenario_id, fullResult.scenario_config);
            }
          }).catch(err => {
            console.error('Failed to fetch full result:', err);
            setError(`Failed to fetch result: ${err.message}`);
          });
          eventSource.close();
        } else if (normalized === 'auth_error') {
          localStorage.removeItem('bfih_openai_api_key');
          localStorage.removeItem('bfih_vector_store_id');
          localStorage.removeItem('bfih_setup_complete');
          window.location.href = '/';
          eventSource.close();
        } else if (normalized === 'failed') {
          setStatus('failed');
          setError(statusResponse.error || statusResponse.status || 'Analysis failed');
          eventSource.close();
        } else {
          setStatus('processing');
        }
      } catch (err) {
        console.error('Error parsing SSE data:', err);
      }
    };

    // Listen for named 'status' events
    eventSource.addEventListener('status', (event) => {
      handleSSEData(event.data);
    });

    // Also handle unnamed messages (fallback for proxies that strip event names)
    eventSource.onmessage = (event) => {
      handleSSEData(event.data);
    };

    eventSource.addEventListener('complete', (event) => {
      console.log('SSE complete event:', event.data);
      eventSource.close();
    });

    eventSource.addEventListener('error', (event) => {
      console.log('SSE error event:', event);
      // Don't close - let EventSource auto-reconnect
    });

    eventSource.onerror = (err) => {
      console.error('SSE connection error:', err);
      // Don't close on error - EventSource auto-reconnects
    };

    return () => {
      console.log('Closing SSE connection');
      eventSource.close();
    };
  }, [id, navigateToGame, cacheResult]);

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

            {/* Live Progress Log */}
            {isProcessing && progressLog.length > 0 && (
              <div className="mb-6">
                <div className="text-xs text-text-muted uppercase tracking-wider mb-2 flex items-center gap-2">
                  <span className="inline-block w-2 h-2 rounded-full bg-accent animate-pulse" />
                  Live Activity
                </div>
                <div className="bg-surface-2 rounded-lg border border-border p-3 max-h-32 overflow-y-auto font-mono text-xs">
                  {progressLog.slice(-5).map((entry, idx) => (
                    <motion.div
                      key={`${entry.timestamp}-${idx}`}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`py-1 ${idx === progressLog.slice(-5).length - 1 ? 'text-accent' : 'text-text-secondary'}`}
                    >
                      {entry.message}
                    </motion.div>
                  ))}
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
