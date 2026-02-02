import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';

// Pages
import { HomePage } from './pages/HomePage';
import { ScenarioLibraryPage } from './pages/ScenarioLibraryPage';
import { AnalysisInProgressPage } from './pages/AnalysisInProgressPage';
import { ScenarioSetupPage } from './pages/game/ScenarioSetupPage';
import { HypothesisGenerationPage } from './pages/game/HypothesisGenerationPage';
import { PriorAssignmentPage } from './pages/game/PriorAssignmentPage';
import { InitialBettingPage } from './pages/game/InitialBettingPage';
import { EvidencePredictionPage } from './pages/game/EvidencePredictionPage';
import { EvidenceRoundPage } from './pages/game/EvidenceRoundPage';
import { ResolutionPage } from './pages/game/ResolutionPage';
import { ReportPage } from './pages/game/ReportPage';
import { DebriefPage } from './pages/game/DebriefPage';

// Layout
import { Header } from './components/layout/Header';

// Components
import { SetupModal } from './components/ui';

// API
import { checkSetupNeeded } from './api';

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        {/* Main routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/library" element={<ScenarioLibraryPage />} />
        <Route path="/analysis/:id" element={<AnalysisInProgressPage />} />

        {/* Game phase routes */}
        <Route path="/game/:scenarioId/setup" element={<ScenarioSetupPage />} />
        <Route path="/game/:scenarioId/hypotheses" element={<HypothesisGenerationPage />} />
        <Route path="/game/:scenarioId/priors" element={<PriorAssignmentPage />} />
        <Route path="/game/:scenarioId/betting" element={<InitialBettingPage />} />
        <Route path="/game/:scenarioId/prediction" element={<EvidencePredictionPage />} />
        <Route path="/game/:scenarioId/evidence" element={<EvidenceRoundPage />} />
        <Route path="/game/:scenarioId/evidence/:round" element={<EvidenceRoundPage />} />
        <Route path="/game/:scenarioId/resolution" element={<ResolutionPage />} />
        <Route path="/game/:scenarioId/report" element={<ReportPage />} />
        <Route path="/game/:scenarioId/debrief" element={<DebriefPage />} />
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  const [showSetup, setShowSetup] = useState(false);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Check if setup is needed on initial load (async - checks server status too)
    const checkSetup = async () => {
      try {
        const needsSetup = await checkSetupNeeded();
        setShowSetup(needsSetup);
      } catch (error) {
        // If check fails, assume setup is needed
        console.error('Failed to check setup status:', error);
        setShowSetup(true);
      }
      setIsReady(true);
    };
    checkSetup();
  }, []);

  const handleSetupComplete = () => {
    setShowSetup(false);
  };

  // Don't render until we've checked setup status
  if (!isReady) {
    return (
      <div className="min-h-screen bg-surface-0 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-surface-0 text-text-primary">
        <Header />
        <main>
          <AnimatedRoutes />
        </main>

        {/* Setup modal for first-time users */}
        <SetupModal
          isOpen={showSetup}
          onComplete={handleSetupComplete}
        />
      </div>
    </BrowserRouter>
  );
}

export default App;
