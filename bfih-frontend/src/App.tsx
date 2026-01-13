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
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-surface-0 text-text-primary">
        <Header />
        <main>
          <AnimatedRoutes />
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
