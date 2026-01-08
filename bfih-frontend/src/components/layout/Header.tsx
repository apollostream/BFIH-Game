import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { cn } from '../../utils';
import { useUIStore, useGameStore } from '../../stores';

export function Header() {
  const location = useLocation();
  const { theme, toggleTheme } = useUIStore();
  const { isGameActive, scenarioConfig } = useGameStore();

  const isHome = location.pathname === '/';
  const isLibrary = location.pathname === '/library';

  return (
    <header className="sticky top-0 z-40 w-full">
      <div className="glass border-b border-border">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3">
              <motion.div
                whileHover={{ scale: 1.05 }}
                className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center"
              >
                <span className="text-white font-bold text-lg">B</span>
              </motion.div>
              <div className="hidden sm:block">
                <h1 className="text-lg font-bold text-text-primary">
                  BFIH Tournament
                </h1>
                <p className="text-xs text-text-muted">
                  Bayesian Hypothesis Analysis
                </p>
              </div>
            </Link>

            {/* Current scenario indicator (when in game) */}
            {isGameActive && scenarioConfig && (
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-2">
                <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
                <span className="text-sm text-text-secondary truncate max-w-[200px]">
                  {scenarioConfig.scenario_metadata?.title ||
                   scenarioConfig.scenario_narrative?.research_question ||
                   scenarioConfig.scenario_narrative?.title ||
                   'Analysis in Progress'}
                </span>
              </div>
            )}

            {/* Navigation */}
            <nav className="flex items-center gap-2">
              <NavLink href="/" active={isHome}>
                Home
              </NavLink>
              <NavLink href="/library" active={isLibrary}>
                Library
              </NavLink>

              {/* Theme toggle */}
              <button
                onClick={toggleTheme}
                className={cn(
                  'p-2 rounded-lg',
                  'text-text-muted hover:text-text-primary',
                  'hover:bg-surface-2 transition-colors'
                )}
                aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              >
                {theme === 'dark' ? (
                  <SunIcon className="w-5 h-5" />
                ) : (
                  <MoonIcon className="w-5 h-5" />
                )}
              </button>
            </nav>
          </div>
        </div>
      </div>
    </header>
  );
}

interface NavLinkProps {
  href: string;
  active: boolean;
  children: React.ReactNode;
}

function NavLink({ href, active, children }: NavLinkProps) {
  return (
    <Link
      to={href}
      className={cn(
        'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
        active
          ? 'bg-accent/10 text-accent'
          : 'text-text-secondary hover:text-text-primary hover:bg-surface-2'
      )}
    >
      {children}
    </Link>
  );
}

function SunIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  );
}

function MoonIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
      />
    </svg>
  );
}
