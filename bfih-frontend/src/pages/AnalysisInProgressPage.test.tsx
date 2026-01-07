import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AnalysisInProgressPage } from './AnalysisInProgressPage';
import * as api from '../api';

// Mock the API module
vi.mock('../api', () => ({
  getAnalysisStatus: vi.fn(),
  getAnalysis: vi.fn(),
}));

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, 'data-testid': testId }: any) => <div className={className} data-testid={testId}>{children}</div>,
    span: ({ children, className }: any) => <span className={className}>{children}</span>,
    p: ({ children, className }: any) => <p className={className}>{children}</p>,
    button: ({ children, className, onClick, disabled }: any) =>
      <button className={className} onClick={onClick} disabled={disabled}>{children}</button>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock layout components
vi.mock('../components/layout/PageContainer', () => ({
  PageContainer: ({ children, className }: any) => <div className={className}>{children}</div>,
}));

// Mock UI components
vi.mock('../components/ui/Card', () => ({
  Card: ({ children, className }: any) => <div className={className}>{children}</div>,
}));

vi.mock('../components/ui/Button', () => ({
  Button: ({ children, onClick, disabled, className }: any) => (
    <button onClick={onClick} disabled={disabled} className={className}>{children}</button>
  ),
}));

// Mock the game store
const mockLoadScenario = vi.fn();
const mockCacheResult = vi.fn();
vi.mock('../stores', () => ({
  useGameStore: () => ({
    loadScenario: mockLoadScenario,
  }),
  useAnalysisStore: () => ({
    cacheResult: mockCacheResult,
  }),
}));

// Mock navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockAnalysisResult = {
  analysis_id: 'test-123',
  scenario_id: 'scenario-456',
  proposition: 'Test proposition',
  report: '# Test Report',
  posteriors: {},
  metadata: {
    model: 'test',
    phases_completed: 5,
    duration_seconds: 60,
    user_id: 'test-user',
    evidence_items_count: 0,
    evidence_clusters_count: 0,
    evidence_items: [],
    evidence_clusters: [],
    autonomous: true,
  },
  created_at: '2026-01-07T00:00:00Z',
  scenario_config: {
    paradigms: [],
    hypotheses: [],
    priors_by_paradigm: {},
  },
};

function renderWithRouter(analysisId: string) {
  return render(
    <MemoryRouter initialEntries={[`/analysis/${analysisId}`]}>
      <Routes>
        <Route path="/analysis/:id" element={<AnalysisInProgressPage />} />
        <Route path="/game/:scenarioId/setup" element={<div>Game Setup Page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe('AnalysisInProgressPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show processing state initially', async () => {
    vi.mocked(api.getAnalysisStatus).mockResolvedValue({
      analysis_id: 'test-123',
      status: 'processing',
      timestamp: '2026-01-07T00:00:00Z',
    });

    renderWithRouter('test-123');

    expect(screen.getByText('Analysis in Progress')).toBeInTheDocument();
  });

  it('should call status API on mount', async () => {
    vi.mocked(api.getAnalysisStatus).mockResolvedValue({
      analysis_id: 'test-123',
      status: 'processing',
      timestamp: '2026-01-07T00:00:00Z',
    });

    renderWithRouter('test-123');

    await waitFor(() => {
      expect(api.getAnalysisStatus).toHaveBeenCalledWith('test-123');
    });
  });

  it('should navigate when status is completed', async () => {
    vi.mocked(api.getAnalysisStatus).mockResolvedValue({
      analysis_id: 'test-123',
      status: 'completed',
      timestamp: '2026-01-07T00:00:00Z',
    });

    vi.mocked(api.getAnalysis).mockResolvedValue(mockAnalysisResult as any);

    renderWithRouter('test-123');

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/game/scenario-456/setup');
    });
  });

  it('should fetch full analysis result when status is completed', async () => {
    vi.mocked(api.getAnalysisStatus).mockResolvedValue({
      analysis_id: 'test-123',
      status: 'completed',
      timestamp: '2026-01-07T00:00:00Z',
    });

    vi.mocked(api.getAnalysis).mockResolvedValue(mockAnalysisResult as any);

    renderWithRouter('test-123');

    await waitFor(() => {
      expect(api.getAnalysis).toHaveBeenCalledWith('test-123');
    });
  });

  it('should load scenario with scenario_id in config', async () => {
    vi.mocked(api.getAnalysisStatus).mockResolvedValue({
      analysis_id: 'test-123',
      status: 'completed',
      timestamp: '2026-01-07T00:00:00Z',
    });

    vi.mocked(api.getAnalysis).mockResolvedValue(mockAnalysisResult as any);

    renderWithRouter('test-123');

    await waitFor(() => {
      expect(mockLoadScenario).toHaveBeenCalled();
      const loadedConfig = mockLoadScenario.mock.calls[0][0];
      expect(loadedConfig.scenario_id).toBe('scenario-456');
    });
  });

  it('should handle failed status', async () => {
    vi.mocked(api.getAnalysisStatus).mockResolvedValue({
      analysis_id: 'test-123',
      status: 'failed: API error' as any,
      timestamp: '2026-01-07T00:00:00Z',
    });

    renderWithRouter('test-123');

    await waitFor(() => {
      expect(screen.getByText('Analysis Failed')).toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    vi.mocked(api.getAnalysisStatus).mockRejectedValue(new Error('Network error'));

    renderWithRouter('test-123');

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });

  it('should handle case-insensitive completed status', async () => {
    vi.mocked(api.getAnalysisStatus).mockResolvedValue({
      analysis_id: 'test-123',
      status: 'COMPLETED' as any,
      timestamp: '2026-01-07T00:00:00Z',
    });

    vi.mocked(api.getAnalysis).mockResolvedValue(mockAnalysisResult as any);

    renderWithRouter('test-123');

    await waitFor(() => {
      expect(api.getAnalysis).toHaveBeenCalled();
    });
  });

  it('should handle failed prefix status', async () => {
    vi.mocked(api.getAnalysisStatus).mockResolvedValue({
      analysis_id: 'test-123',
      status: 'failed: Something went wrong' as any,
      timestamp: '2026-01-07T00:00:00Z',
    });

    renderWithRouter('test-123');

    await waitFor(() => {
      expect(screen.getByText('Analysis Failed')).toBeInTheDocument();
    });
  });
});

describe('AnalysisInProgressPage - Polling with fake timers', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should poll for status updates at 3s intervals', async () => {
    vi.mocked(api.getAnalysisStatus).mockResolvedValue({
      analysis_id: 'test-123',
      status: 'processing',
      timestamp: '2026-01-07T00:00:00Z',
    });

    renderWithRouter('test-123');

    // Wait for initial check
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });

    const initialCallCount = vi.mocked(api.getAnalysisStatus).mock.calls.length;
    expect(initialCallCount).toBeGreaterThanOrEqual(1);

    // Advance to trigger polling interval (3 seconds)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    // Should have polled at least once more
    expect(api.getAnalysisStatus).toHaveBeenCalledTimes(initialCallCount + 1);
  });

  it('should stop polling after status becomes completed', async () => {
    let callCount = 0;
    vi.mocked(api.getAnalysisStatus).mockImplementation(async () => {
      callCount++;
      // Return completed on 2nd call
      if (callCount >= 2) {
        return {
          analysis_id: 'test-123',
          status: 'completed',
          timestamp: '2026-01-07T00:00:00Z',
        };
      }
      return {
        analysis_id: 'test-123',
        status: 'processing',
        timestamp: '2026-01-07T00:00:00Z',
      };
    });

    vi.mocked(api.getAnalysis).mockResolvedValue(mockAnalysisResult as any);

    renderWithRouter('test-123');

    // First call - processing
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });

    // Second call - completed
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    const callsAfterComplete = vi.mocked(api.getAnalysisStatus).mock.calls.length;

    // Wait more - should not poll again
    await act(async () => {
      await vi.advanceTimersByTimeAsync(6000);
    });

    // Polling should have stopped
    expect(api.getAnalysisStatus).toHaveBeenCalledTimes(callsAfterComplete);
  });
});
