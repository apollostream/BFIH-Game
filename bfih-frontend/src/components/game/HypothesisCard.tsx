import { motion } from 'framer-motion';
import { cn } from '../../utils';
import { formatHypothesisId, formatPercent, getHypothesisColor } from '../../utils';
import type { Hypothesis } from '../../types';
import { Card } from '../ui/Card';
import { Badge, DomainBadge, ParadigmBadge } from '../ui/Badge';
import { BayesianTooltip } from '../ui/Tooltip';

export interface HypothesisCardProps {
  hypothesis: Hypothesis;
  prior?: number;
  posterior?: number;
  bet?: number;
  isWinner?: boolean;
  onClick?: () => void;
  onBetClick?: () => void;
  showBetButton?: boolean;
  showDetails?: boolean;
  compact?: boolean;
  variant?: 'default' | 'compact' | 'detailed'; // Alternative to compact flag
  className?: string;
}

export function HypothesisCard({
  hypothesis,
  prior,
  posterior,
  bet,
  isWinner = false,
  onClick,
  onBetClick,
  showBetButton = false,
  showDetails = true,
  compact: compactProp = false,
  variant = 'default',
  className,
}: HypothesisCardProps) {
  const compact = compactProp || variant === 'compact';
  const color = getHypothesisColor(hypothesis.id, hypothesis.associated_paradigms);
  const probabilityChange = posterior !== undefined && prior !== undefined
    ? posterior - prior
    : null;

  if (compact) {
    return (
      <motion.div
        whileHover={onClick ? { x: 4 } : undefined}
        className={cn(
          'flex items-center gap-3 p-3 rounded-lg',
          'bg-surface-1 border border-border',
          onClick && 'cursor-pointer hover:bg-surface-2',
          isWinner && 'ring-2 ring-success',
          className
        )}
        onClick={onClick}
      >
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm flex-shrink-0"
          style={{ backgroundColor: color }}
        >
          {formatHypothesisId(hypothesis.id)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-text-primary truncate">
            {hypothesis.name}
          </div>
          {posterior !== undefined && (
            <div className="text-sm text-text-secondary">
              {formatPercent(posterior)}
              {probabilityChange !== null && probabilityChange !== 0 && (
                <span className={cn(
                  'ml-1',
                  probabilityChange > 0 ? 'text-success' : 'text-error'
                )}>
                  ({probabilityChange > 0 ? '+' : ''}{formatPercent(probabilityChange)})
                </span>
              )}
            </div>
          )}
        </div>
        {bet !== undefined && bet > 0 && (
          <Badge variant="primary" size="sm">
            {bet} credits
          </Badge>
        )}
        {isWinner && (
          <Badge variant="success" size="sm">
            Winner
          </Badge>
        )}
      </motion.div>
    );
  }

  return (
    <motion.div
      whileHover={onClick ? { scale: 1.01 } : undefined}
      whileTap={onClick ? { scale: 0.99 } : undefined}
    >
      <Card
        variant={isWinner ? 'elevated' : 'default'}
        hoverable={!!onClick}
        className={cn(
          'relative overflow-hidden',
          isWinner && 'ring-2 ring-success',
          onClick && 'cursor-pointer',
          className
        )}
        onClick={onClick}
      >
        {/* Left accent bar */}
        <div
          className="absolute top-0 left-0 bottom-0 w-1"
          style={{ backgroundColor: color }}
        />

        <div className="pl-3">
          {/* Header */}
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-3">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold"
                style={{ backgroundColor: color }}
              >
                {formatHypothesisId(hypothesis.id)}
              </div>
              <div>
                <h3 className="font-semibold text-text-primary">
                  {hypothesis.name}
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  {hypothesis.is_catch_all && (
                    <Badge variant="default" size="sm">
                      Catch-all
                    </Badge>
                  )}
                  {hypothesis.is_ancestral_solution && (
                    <Badge variant="warning" size="sm">
                      Ancestral
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Probability display */}
            {(prior !== undefined || posterior !== undefined) && (
              <div className="text-right">
                {posterior !== undefined && (
                  <BayesianTooltip concept="posterior">
                    <motion.div
                      key={posterior}
                      initial={{ scale: 1 }}
                      animate={{ scale: [1, 1.1, 1] }}
                      className="text-2xl font-bold text-text-primary"
                    >
                      {formatPercent(posterior)}
                    </motion.div>
                  </BayesianTooltip>
                )}
                {prior !== undefined && posterior === undefined && (
                  <BayesianTooltip concept="prior">
                    <div className="text-2xl font-bold text-text-secondary">
                      {formatPercent(prior)}
                    </div>
                  </BayesianTooltip>
                )}
                {probabilityChange !== null && probabilityChange !== 0 && (
                  <div className={cn(
                    'text-sm',
                    probabilityChange > 0 ? 'text-success' : 'text-error'
                  )}>
                    {probabilityChange > 0 ? '+' : ''}{formatPercent(probabilityChange)}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Narrative */}
          {showDetails && (
            <p className="text-sm text-text-secondary mb-3 line-clamp-2">
              {hypothesis.narrative}
            </p>
          )}

          {/* Tags */}
          {showDetails && (
            <div className="flex flex-wrap gap-2 mb-3">
              {hypothesis.domains?.map((domain) => (
                <DomainBadge key={domain} domain={domain} size="sm" />
              ))}
              {hypothesis.associated_paradigms?.map((paradigmId) => (
                <ParadigmBadge key={paradigmId} paradigmId={paradigmId} size="sm">
                  {paradigmId}
                </ParadigmBadge>
              ))}
            </div>
          )}

          {/* Footer with bet info */}
          {(bet !== undefined || showBetButton) && (
            <div className="flex items-center justify-between pt-3 border-t border-border">
              {bet !== undefined && bet > 0 ? (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-text-muted">Your bet:</span>
                  <Badge variant="primary">{bet} credits</Badge>
                </div>
              ) : (
                <span className="text-sm text-text-muted">No bet placed</span>
              )}
              {showBetButton && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onBetClick?.();
                  }}
                  className={cn(
                    'px-3 py-1.5 rounded-lg text-sm font-medium',
                    'bg-accent text-white',
                    'hover:bg-accent-hover transition-colors'
                  )}
                >
                  {bet && bet > 0 ? 'Adjust Bet' : 'Place Bet'}
                </motion.button>
              )}
            </div>
          )}
        </div>
      </Card>
    </motion.div>
  );
}

// Hypothesis ranking list
interface HypothesisRankingProps {
  hypotheses: Hypothesis[];
  posteriors: Record<string, number>;
  onHypothesisClick?: (hypothesisId: string) => void;
  highlightId?: string;
  className?: string;
}

export function HypothesisRanking({
  hypotheses,
  posteriors,
  onHypothesisClick,
  highlightId,
  className,
}: HypothesisRankingProps) {
  const sorted = [...hypotheses].sort(
    (a, b) => (posteriors[b.id] || 0) - (posteriors[a.id] || 0)
  );

  return (
    <div className={cn('space-y-2', className)}>
      {sorted.map((hypothesis, index) => {
        const posterior = posteriors[hypothesis.id] || 0;
        const color = getHypothesisColor(hypothesis.id, hypothesis.associated_paradigms);
        const isHighlighted = hypothesis.id === highlightId;

        return (
          <motion.div
            key={hypothesis.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            onClick={() => onHypothesisClick?.(hypothesis.id)}
            className={cn(
              'flex items-center gap-3 p-2 rounded-lg',
              'bg-surface-1 border border-border',
              onHypothesisClick && 'cursor-pointer hover:bg-surface-2',
              isHighlighted && 'ring-2 ring-accent'
            )}
          >
            <span className="text-lg font-bold text-text-muted w-6">
              {index + 1}
            </span>
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-xs"
              style={{ backgroundColor: color }}
            >
              {formatHypothesisId(hypothesis.id)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-text-primary text-sm truncate">
                {hypothesis.name}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2 bg-surface-2 rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${posterior * 100}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
              <span className="text-sm font-semibold text-text-primary w-12 text-right">
                {formatPercent(posterior)}
              </span>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
