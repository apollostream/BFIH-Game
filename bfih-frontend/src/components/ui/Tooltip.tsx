import { useState, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils';
import { tooltipVariants } from '../../utils/animations';

type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  position?: TooltipPosition;
  delay?: number;
  className?: string;
  contentClassName?: string;
  disabled?: boolean;
}

const positionStyles: Record<TooltipPosition, string> = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
};

const arrowStyles: Record<TooltipPosition, string> = {
  top: 'top-full left-1/2 -translate-x-1/2 border-t-surface-2 border-x-transparent border-b-transparent',
  bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-surface-2 border-x-transparent border-t-transparent',
  left: 'left-full top-1/2 -translate-y-1/2 border-l-surface-2 border-y-transparent border-r-transparent',
  right: 'right-full top-1/2 -translate-y-1/2 border-r-surface-2 border-y-transparent border-l-transparent',
};

export function Tooltip({
  content,
  children,
  position = 'top',
  delay = 200,
  className,
  contentClassName,
  disabled = false,
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [timeoutId, setTimeoutId] = useState<number | null>(null);

  const showTooltip = () => {
    if (disabled) return;
    const id = window.setTimeout(() => setIsVisible(true), delay);
    setTimeoutId(id);
  };

  const hideTooltip = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      setTimeoutId(null);
    }
    setIsVisible(false);
  };

  return (
    <div
      className={cn('relative inline-flex', className)}
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            variants={tooltipVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className={cn(
              'absolute z-50 pointer-events-none',
              positionStyles[position]
            )}
          >
            <div
              className={cn(
                'px-3 py-2 rounded-lg',
                'bg-surface-2 text-text-primary text-sm',
                'border border-border shadow-elevated',
                'max-w-xs',
                contentClassName
              )}
            >
              {content}
            </div>
            {/* Arrow */}
            <div
              className={cn(
                'absolute w-0 h-0 border-4',
                arrowStyles[position]
              )}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Info tooltip with question mark icon
interface InfoTooltipProps extends Omit<TooltipProps, 'children'> {
  size?: 'sm' | 'md';
}

export function InfoTooltip({ size = 'sm', ...props }: InfoTooltipProps) {
  const sizeClasses = size === 'sm' ? 'w-4 h-4 text-xs' : 'w-5 h-5 text-sm';

  return (
    <Tooltip {...props}>
      <span
        className={cn(
          'inline-flex items-center justify-center',
          'rounded-full bg-surface-3 text-text-muted',
          'hover:bg-surface-4 hover:text-text-secondary',
          'cursor-help transition-colors',
          sizeClasses
        )}
      >
        ?
      </span>
    </Tooltip>
  );
}

// Bayesian concept tooltip
interface BayesianTooltipProps extends Omit<TooltipProps, 'content'> {
  concept: 'prior' | 'posterior' | 'likelihood' | 'woe' | 'lr' | 'paradigm' | 'hypothesis';
}

const bayesianConcepts: Record<string, { title: string; description: string }> = {
  prior: {
    title: 'Prior Probability',
    description: 'The probability of a hypothesis before considering the evidence. Represents your initial belief.',
  },
  posterior: {
    title: 'Posterior Probability',
    description: 'The updated probability of a hypothesis after considering the evidence. Calculated using Bayes\' theorem.',
  },
  likelihood: {
    title: 'Likelihood',
    description: 'P(E|H) - The probability of observing the evidence if the hypothesis is true.',
  },
  woe: {
    title: 'Weight of Evidence',
    description: 'A measure in decibans (db) of how much evidence shifts belief. +10 db = strong support, -10 db = strong refutation.',
  },
  lr: {
    title: 'Likelihood Ratio',
    description: 'The ratio of P(E|H) to P(E|not H). Values > 1 support the hypothesis, < 1 refute it.',
  },
  paradigm: {
    title: 'Paradigm',
    description: 'An epistemic stance or worldview that shapes how evidence is interpreted and weighted.',
  },
  hypothesis: {
    title: 'Hypothesis',
    description: 'A potential explanation for the scenario. Hypotheses are mutually exclusive and collectively exhaustive (MECE).',
  },
};

export function BayesianTooltip({ concept, children, ...props }: BayesianTooltipProps) {
  const info = bayesianConcepts[concept];

  return (
    <Tooltip
      content={
        <div>
          <div className="font-semibold text-accent mb-1">{info.title}</div>
          <div className="text-text-secondary">{info.description}</div>
        </div>
      }
      {...props}
    >
      {children}
    </Tooltip>
  );
}
