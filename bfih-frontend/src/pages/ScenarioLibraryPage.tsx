import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { PageContainer } from '../components/layout/PageContainer';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';
import { listScenarios } from '../api';
import { useGameStore, useAnalysisStore, useBettingStore } from '../stores';
import { pageVariants, cardVariants } from '../utils';
import type { ScenarioSummary } from '../types';

type SortField = 'created_date' | 'title' | 'creator' | 'domain' | 'model';
type SortDirection = 'asc' | 'desc';

// Truncate title for display
function truncateTitle(title: string, maxLength: number = 60): string {
  if (title.length <= maxLength) return title;
  return title.substring(0, maxLength - 3) + '...';
}

// Format date for display
function formatDate(dateString: string): string {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined,
    });
  } catch {
    return dateString;
  }
}

// Format model name for display
function formatModel(model: string | undefined): string {
  if (!model) return '-';
  // Shorten common model names
  if (model.includes('gpt-4o')) return 'GPT-4o';
  if (model.includes('o3')) return 'o3';
  if (model.includes('o1')) return 'o1';
  if (model.includes('gpt-4')) return 'GPT-4';
  if (model.includes('gpt-3.5')) return 'GPT-3.5';
  return model;
}

export function ScenarioLibraryPage() {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('created_date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [searchQuery, setSearchQuery] = useState('');

  // Get current game state to show "Continue" option
  const { scenarioId, scenarioConfig, isGameActive, clearScenarioCache } = useGameStore();
  const { clearCurrentAnalysis } = useAnalysisStore();
  const { resetBetting } = useBettingStore();

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

  // Sort and filter scenarios
  const sortedScenarios = useMemo(() => {
    let filtered = scenarios;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = scenarios.filter(s =>
        s.title.toLowerCase().includes(query) ||
        s.domain.toLowerCase().includes(query) ||
        (s.creator || '').toLowerCase().includes(query) ||
        (s.model || '').toLowerCase().includes(query)
      );
    }

    // Apply sorting
    return [...filtered].sort((a, b) => {
      let aVal: string | number = '';
      let bVal: string | number = '';

      switch (sortField) {
        case 'created_date':
          aVal = a.created_date || a.updated || '';
          bVal = b.created_date || b.updated || '';
          break;
        case 'title':
          aVal = a.title.toLowerCase();
          bVal = b.title.toLowerCase();
          break;
        case 'creator':
          aVal = (a.creator || 'anonymous').toLowerCase();
          bVal = (b.creator || 'anonymous').toLowerCase();
          break;
        case 'domain':
          aVal = (a.topic || a.domain).toLowerCase();
          bVal = (b.topic || b.domain).toLowerCase();
          break;
        case 'model':
          aVal = (a.model || '').toLowerCase();
          bVal = (b.model || '').toLowerCase();
          break;
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [scenarios, sortField, sortDirection, searchQuery]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <span className="text-text-muted ml-1">↕</span>;
    return <span className="text-accent ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>;
  };

  const handleSelectScenario = (scenarioId: string) => {
    // Clear all cached data to force fresh fetch
    clearScenarioCache();
    clearCurrentAnalysis();
    resetBetting();
    navigate(`/game/${scenarioId}/setup`);
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
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-text-primary">
              Scenario Library
            </h1>
            <p className="text-text-secondary mt-1">
              Browse and replay analyses from the community
            </p>
          </div>
          <Button onClick={() => navigate('/')}>
            New Analysis
          </Button>
        </div>

        {/* Continue Current Analysis */}
        {hasActiveGame && (
          <motion.div variants={cardVariants} className="mb-6">
            <Card variant="glass" className="p-4 border-2 border-accent/50">
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="success">Active</Badge>
                    <span className="text-sm font-medium text-text-primary">
                      Current Analysis
                    </span>
                  </div>
                  <p className="text-text-secondary text-sm line-clamp-1">
                    {scenarioConfig?.proposition || scenarioConfig?.narrative || 'Untitled'}
                  </p>
                </div>
                <Button size="sm" onClick={() => navigate(`/game/${scenarioId}/setup`)}>
                  Continue
                </Button>
              </div>
            </Card>
          </motion.div>
        )}

        {/* Search */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search scenarios..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full max-w-md px-4 py-2 rounded-lg bg-surface-1 border border-border
                       text-text-primary placeholder:text-text-muted text-sm
                       focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
          />
        </div>

        {/* Content */}
        {loading ? (
          <Card className="overflow-hidden">
            <div className="p-4 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex gap-4">
                  <Skeleton className="h-5 flex-1" />
                  <Skeleton className="h-5 w-20" />
                  <Skeleton className="h-5 w-20" />
                  <Skeleton className="h-5 w-16" />
                </div>
              ))}
            </div>
          </Card>
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
          <Card className="overflow-hidden">
            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-surface-1">
                    <th
                      className="text-left px-4 py-3 font-medium text-text-secondary cursor-pointer hover:text-text-primary"
                      onClick={() => handleSort('title')}
                    >
                      Title <SortIcon field="title" />
                    </th>
                    <th
                      className="text-left px-4 py-3 font-medium text-text-secondary cursor-pointer hover:text-text-primary whitespace-nowrap"
                      onClick={() => handleSort('domain')}
                    >
                      Topic <SortIcon field="domain" />
                    </th>
                    <th
                      className="text-left px-4 py-3 font-medium text-text-secondary cursor-pointer hover:text-text-primary whitespace-nowrap"
                      onClick={() => handleSort('creator')}
                    >
                      Creator <SortIcon field="creator" />
                    </th>
                    <th
                      className="text-left px-4 py-3 font-medium text-text-secondary cursor-pointer hover:text-text-primary whitespace-nowrap"
                      onClick={() => handleSort('model')}
                    >
                      Model <SortIcon field="model" />
                    </th>
                    <th
                      className="text-left px-4 py-3 font-medium text-text-secondary cursor-pointer hover:text-text-primary whitespace-nowrap"
                      onClick={() => handleSort('created_date')}
                    >
                      Date <SortIcon field="created_date" />
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sortedScenarios.map((scenario, index) => (
                    <tr
                      key={scenario.scenario_id}
                      className={`
                        border-b border-border/50 cursor-pointer
                        hover:bg-surface-1 transition-colors
                        ${index % 2 === 0 ? 'bg-surface-0' : 'bg-surface-0/50'}
                      `}
                      onClick={() => handleSelectScenario(scenario.scenario_id)}
                    >
                      <td className="px-4 py-3">
                        <span className="text-text-primary hover:text-accent transition-colors">
                          {truncateTitle(scenario.title)}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="secondary" className="text-xs">
                          {scenario.topic || scenario.domain}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-text-secondary">
                        {scenario.creator || 'anonymous'}
                      </td>
                      <td className="px-4 py-3 text-text-muted font-mono text-xs">
                        {formatModel(scenario.model)}
                      </td>
                      <td className="px-4 py-3 text-text-muted whitespace-nowrap">
                        {formatDate(scenario.created_date || scenario.updated || '')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Footer */}
            <div className="px-4 py-3 bg-surface-1 border-t border-border text-sm text-text-muted">
              {sortedScenarios.length} scenario{sortedScenarios.length !== 1 ? 's' : ''}
              {searchQuery && ` matching "${searchQuery}"`}
            </div>
          </Card>
        )}
      </PageContainer>
    </motion.div>
  );
}
