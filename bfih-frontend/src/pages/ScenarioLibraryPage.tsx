import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { listScenarios } from '../api';
import { useGameStore, useAnalysisStore } from '../stores';
import { pageVariants, staggerContainerVariants, cardVariants, formatDate } from '../utils';
import type { ScenarioSummary } from '../types';

export function ScenarioLibraryPage() {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get current game state to show "Continue" option
  const { scenarioId, scenarioConfig, isGameActive } = useGameStore();
  const { currentAnalysis } = useAnalysisStore();

  // Check if there's an active game to continue
  const hasActiveGame = isGameActive && scenarioId && scenarioConfig;

  useEffect(() => {
    loadScenarios();
  }, []);

  const loadScenarios = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listScenarios();
      setScenarios(data.scenarios);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scenarios');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <PageContainer>
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-text-primary">
              Scenario Library
            </h1>
            <p className="text-text-secondary mt-1">
              Browse and replay previous analyses
            </p>
          </div>
          <Button onClick={() => navigate('/')}>
            New Analysis
          </Button>
        </div>

        {/* Continue Current Analysis */}
        {hasActiveGame && (
          <motion.div variants={cardVariants} className="mb-8">
            <Card variant="glass" className="p-6 border-2 border-accent/50">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="success">Active</Badge>
                    <h3 className="text-lg font-semibold text-text-primary">
                      Current Analysis
                    </h3>
                  </div>
                  <p className="text-text-secondary line-clamp-1">
                    {scenarioConfig?.proposition || scenarioConfig?.narrative || 'Untitled'}
                  </p>
                </div>
                <Button onClick={() => navigate(`/game/${scenarioId}/setup`)}>
                  Continue Game
                </Button>
              </div>
            </Card>
          </motion.div>
        )}

        {/* Content */}
        {loading ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Card key={i} className="p-6">
                <Skeleton className="h-6 w-3/4 mb-4" />
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-2/3 mb-4" />
                <div className="flex gap-2">
                  <Skeleton className="h-6 w-16" />
                  <Skeleton className="h-6 w-16" />
                </div>
              </Card>
            ))}
          </div>
        ) : error ? (
          <Card variant="bordered" className="p-8 text-center">
            <div className="text-error mb-4">{error}</div>
            <Button onClick={loadScenarios}>Retry</Button>
          </Card>
        ) : scenarios.length === 0 ? (
          <Card variant="bordered" className="p-12 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-xl font-semibold text-text-primary mb-2">
              No scenarios yet
            </h2>
            <p className="text-text-secondary mb-6">
              Submit your first analysis to get started
            </p>
            <Button onClick={() => navigate('/')}>
              Create New Analysis
            </Button>
          </Card>
        ) : (
          <motion.div
            variants={staggerContainerVariants}
            initial="initial"
            animate="animate"
            className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {scenarios.map((scenario) => (
              <motion.div key={scenario.scenario_id} variants={cardVariants}>
                <Card
                  variant="elevated"
                  className="p-6 cursor-pointer group"
                  onClick={() => navigate(`/game/${scenario.scenario_id}/setup`)}
                >
                  {/* Title */}
                  <h3 className="text-lg font-semibold text-text-primary mb-2
                               group-hover:text-accent transition-colors line-clamp-2">
                    {scenario.title}
                  </h3>

                  {/* Domain & Difficulty */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    <Badge variant="primary">{scenario.domain}</Badge>
                    <Badge variant="secondary">{scenario.difficulty_level}</Badge>
                  </div>

                  {/* Stats */}
                  <div className="flex items-center gap-4 text-xs text-text-muted">
                    {scenario.created_date && (
                      <span>{formatDate(scenario.created_date)}</span>
                    )}
                  </div>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        )}
      </PageContainer>
    </motion.div>
  );
}
