import { motion } from 'framer-motion';
import { cn } from '../../utils';
import { getParadigmColor, formatParadigmId } from '../../utils';
import type { Paradigm } from '../../types';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

export interface ParadigmCardProps {
  paradigm: Paradigm;
  isSelected?: boolean;
  selected?: boolean; // Alias for isSelected
  isActive?: boolean;
  onClick?: () => void;
  showDetails?: boolean;
  showPriors?: boolean;
  priors?: Record<string, number>;
  className?: string;
}

export function ParadigmCard({
  paradigm,
  isSelected: isSelectedProp = false,
  selected = false,
  isActive = false,
  onClick,
  showDetails = true,
  showPriors = false,
  priors,
  className,
}: ParadigmCardProps) {
  const isSelected = isSelectedProp || selected;
  const color = getParadigmColor(paradigm.id);

  return (
    <motion.div
      whileHover={onClick ? { scale: 1.02 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
    >
      <Card
        variant={isSelected ? 'elevated' : 'default'}
        hoverable={!!onClick}
        className={cn(
          'relative overflow-hidden transition-all duration-300',
          isSelected && 'ring-2',
          isActive && 'ring-1 ring-opacity-50',
          onClick && 'cursor-pointer',
          className
        )}
        style={{
          borderColor: isSelected || isActive ? color : undefined,
          // @ts-ignore
          '--ring-color': color,
        }}
        onClick={onClick}
      >
        {/* Color accent bar */}
        <div
          className="absolute top-0 left-0 right-0 h-1"
          style={{ backgroundColor: color }}
        />

        <div className="pt-2">
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm"
                style={{ backgroundColor: color }}
              >
                {formatParadigmId(paradigm.id)}
              </div>
              <div>
                <h3 className="font-semibold text-text-primary">
                  {paradigm.name}
                </h3>
                {paradigm.inverse_paradigm_id && (
                  <span className="text-xs text-text-muted">
                    Inverse: {formatParadigmId(paradigm.inverse_paradigm_id)}
                  </span>
                )}
              </div>
            </div>
            {isSelected && (
              <Badge variant="success" size="sm">
                Selected
              </Badge>
            )}
          </div>

          {/* Description */}
          <p className="text-sm text-text-secondary mb-3">
            {paradigm.description}
          </p>

          {/* Characteristics */}
          {showDetails && paradigm.characteristics && (
            <div className="space-y-2 text-xs">
              {paradigm.characteristics.prefers_evidence_types?.length > 0 && (
                <div>
                  <span className="text-text-muted">Prefers: </span>
                  <span className="text-text-secondary">
                    {paradigm.characteristics.prefers_evidence_types.slice(0, 3).join(', ')}
                  </span>
                </div>
              )}
              {paradigm.characteristics.skeptical_of?.length > 0 && (
                <div>
                  <span className="text-text-muted">Skeptical of: </span>
                  <span className="text-text-secondary">
                    {paradigm.characteristics.skeptical_of.slice(0, 3).join(', ')}
                  </span>
                </div>
              )}
              {paradigm.characteristics.causal_preference && (
                <div>
                  <span className="text-text-muted">Causal: </span>
                  <span className="text-text-secondary">
                    {paradigm.characteristics.causal_preference}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Priors display */}
          {showPriors && priors && (
            <div className="mt-3 pt-3 border-t border-border">
              <div className="text-xs text-text-muted mb-2">Prior Probabilities</div>
              <div className="space-y-1">
                {Object.entries(priors)
                  .sort(([, a], [, b]) => b - a)
                  .slice(0, 3)
                  .map(([hypothesisId, prob]) => (
                    <div key={hypothesisId} className="flex items-center gap-2">
                      <span className="text-xs text-text-secondary w-8">
                        {hypothesisId}
                      </span>
                      <div className="flex-1 h-1.5 bg-surface-2 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full rounded-full"
                          style={{ backgroundColor: color }}
                          initial={{ width: 0 }}
                          animate={{ width: `${prob * 100}%` }}
                          transition={{ duration: 0.5, delay: 0.1 }}
                        />
                      </div>
                      <span className="text-xs text-text-primary w-10 text-right">
                        {(prob * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      </Card>
    </motion.div>
  );
}

// Compact paradigm selector
interface ParadigmSelectorProps {
  paradigms: Paradigm[];
  selectedId: string;
  onChange: (paradigmId: string) => void;
  className?: string;
}

export function ParadigmSelector({
  paradigms,
  selectedId,
  onChange,
  className,
}: ParadigmSelectorProps) {
  return (
    <div className={cn('flex gap-2', className)}>
      {paradigms.map((paradigm) => {
        const isSelected = paradigm.id === selectedId;
        const color = getParadigmColor(paradigm.id);

        return (
          <motion.button
            key={paradigm.id}
            onClick={() => onChange(paradigm.id)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg',
              'border transition-all duration-200',
              isSelected
                ? 'border-current bg-opacity-10'
                : 'border-border bg-surface-1 hover:bg-surface-2'
            )}
            style={{
              color: isSelected ? color : undefined,
              backgroundColor: isSelected ? `${color}15` : undefined,
              borderColor: isSelected ? color : undefined,
            }}
          >
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className={cn(
              'text-sm font-medium',
              isSelected ? 'text-current' : 'text-text-secondary'
            )}>
              {formatParadigmId(paradigm.id)}
            </span>
          </motion.button>
        );
      })}
    </div>
  );
}
