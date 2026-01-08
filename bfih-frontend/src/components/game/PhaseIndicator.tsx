import { motion } from 'framer-motion';
import { cn } from '../../utils';
import { GAME_PHASES, PHASE_LABELS, type GamePhase } from '../../types';

interface PhaseIndicatorProps {
  currentPhase: GamePhase;
  onPhaseClick?: (phase: GamePhase) => void;
  completedPhases?: GamePhase[];
  isPhaseNavigable?: (phase: GamePhase) => boolean;
  furthestPhase?: GamePhase;
  className?: string;
  variant?: 'full' | 'compact';
}

export function PhaseIndicator({
  currentPhase,
  onPhaseClick,
  completedPhases = [],
  isPhaseNavigable,
  furthestPhase,
  className,
  variant = 'full',
}: PhaseIndicatorProps) {
  const currentIndex = GAME_PHASES.indexOf(currentPhase);
  const furthestIndex = furthestPhase ? GAME_PHASES.indexOf(furthestPhase) : currentIndex;

  if (variant === 'compact') {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        {GAME_PHASES.map((phase, index) => {
          const isCompleted = completedPhases.includes(phase) || index < furthestIndex;
          const isCurrent = phase === currentPhase;
          const isNavigable = isPhaseNavigable ? isPhaseNavigable(phase) : (isCompleted || isCurrent);
          const isNextPhase = index === currentIndex + 1;

          return (
            <motion.button
              key={phase}
              onClick={() => onPhaseClick?.(phase)}
              disabled={!onPhaseClick || !isNavigable}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: index * 0.05 }}
              className={cn(
                'w-3 h-3 rounded-full transition-colors',
                isCompleted && 'bg-success',
                isCurrent && 'bg-accent animate-pulse',
                isNextPhase && !isCompleted && 'bg-accent/50 ring-2 ring-accent/30',
                !isCompleted && !isCurrent && !isNextPhase && 'bg-surface-3',
                onPhaseClick && isNavigable && 'cursor-pointer hover:scale-110'
              )}
              aria-label={PHASE_LABELS[phase]}
            />
          );
        })}
        <span className="text-sm text-text-secondary ml-2">
          Phase {currentIndex + 1} of {GAME_PHASES.length}
        </span>
      </div>
    );
  }

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center justify-between">
        {GAME_PHASES.map((phase, index) => {
          const isCompleted = completedPhases.includes(phase) || index < furthestIndex;
          const isCurrent = phase === currentPhase;
          const isNavigable = isPhaseNavigable ? isPhaseNavigable(phase) : (isCompleted || isCurrent);
          const isNextPhase = index === currentIndex + 1;
          const isClickable = onPhaseClick && isNavigable;

          return (
            <div key={phase} className="flex items-center flex-1">
              {/* Step circle */}
              <motion.button
                onClick={() => isClickable && onPhaseClick?.(phase)}
                disabled={!isClickable}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: index * 0.1, type: 'spring' }}
                className={cn(
                  'relative flex items-center justify-center',
                  'w-10 h-10 rounded-full',
                  'text-sm font-semibold',
                  'transition-all duration-300',
                  isCompleted && !isCurrent && 'bg-success text-white',
                  isCurrent && 'bg-accent text-white ring-4 ring-accent/30',
                  isNextPhase && !isCompleted && !isCurrent && 'bg-accent/50 text-white ring-2 ring-accent/30',
                  !isCompleted && !isCurrent && !isNextPhase && 'bg-surface-2 text-text-muted',
                  isClickable && 'cursor-pointer hover:scale-110'
                )}
              >
                {isCompleted && !isCurrent ? (
                  <CheckIcon className="w-5 h-5" />
                ) : (
                  index + 1
                )}
                {isCurrent && (
                  <motion.div
                    className="absolute inset-0 rounded-full bg-accent"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    style={{ opacity: 0.3 }}
                  />
                )}
                {isNextPhase && !isCompleted && (
                  <motion.div
                    className="absolute inset-0 rounded-full bg-accent/50"
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                    style={{ opacity: 0.2 }}
                  />
                )}
              </motion.button>

              {/* Connector line */}
              {index < GAME_PHASES.length - 1 && (
                <div className="flex-1 h-0.5 mx-2">
                  <motion.div
                    className={cn(
                      'h-full rounded-full',
                      index < furthestIndex ? 'bg-success' : 'bg-surface-3'
                    )}
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ delay: index * 0.1 + 0.2, duration: 0.3 }}
                    style={{ transformOrigin: 'left' }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Phase labels */}
      <div className="flex items-start justify-between mt-2">
        {GAME_PHASES.map((phase, index) => {
          const isCurrent = phase === currentPhase;

          return (
            <div
              key={phase}
              className={cn(
                'flex-1 text-center px-1',
                index === 0 && 'text-left',
                index === GAME_PHASES.length - 1 && 'text-right'
              )}
            >
              <span
                className={cn(
                  'text-xs',
                  isCurrent ? 'text-accent font-medium' : 'text-text-muted'
                )}
              >
                {PHASE_LABELS[phase]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CheckIcon({ className }: { className?: string }) {
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
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
}

// Mini phase badge for headers
interface PhaseBadgeProps {
  phase: GamePhase;
  className?: string;
}

export function PhaseBadge({ phase, className }: PhaseBadgeProps) {
  const index = GAME_PHASES.indexOf(phase);

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full',
        'bg-accent/10 text-accent text-sm font-medium',
        className
      )}
    >
      <span className="w-5 h-5 rounded-full bg-accent text-white text-xs flex items-center justify-center">
        {index + 1}
      </span>
      {PHASE_LABELS[phase]}
    </span>
  );
}
