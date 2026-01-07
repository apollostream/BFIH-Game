import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import { motion } from 'framer-motion';
import { cn } from '../../utils';
import { formatPercent, formatHypothesisId, getHypothesisColor } from '../../utils';
import type { Hypothesis, PosteriorsByParadigm } from '../../types';
import { ParadigmSelector } from '../game/ParadigmCard';

interface HypothesisBarChartProps {
  hypotheses: Hypothesis[];
  posteriors: PosteriorsByParadigm;
  priors?: Record<string, number>;
  activeParadigm: string;
  onParadigmChange?: (paradigmId: string) => void;
  showPriors?: boolean;
  highlightHypothesis?: string;
  className?: string;
}

export function HypothesisBarChart({
  hypotheses,
  posteriors,
  priors,
  activeParadigm,
  onParadigmChange,
  showPriors = false,
  highlightHypothesis,
  className,
}: HypothesisBarChartProps) {
  const paradigmPosteriors = posteriors[activeParadigm] || {};

  const data = useMemo(() => {
    return hypotheses
      .map((h) => ({
        id: h.id,
        name: h.name,
        displayId: formatHypothesisId(h.id),
        posterior: paradigmPosteriors[h.id] || 0,
        prior: priors?.[h.id] || 0,
        color: getHypothesisColor(h.id, h.associated_paradigms),
        isHighlighted: h.id === highlightHypothesis,
      }))
      .sort((a, b) => b.posterior - a.posterior);
  }, [hypotheses, paradigmPosteriors, priors, highlightHypothesis]);

  const paradigmIds = Object.keys(posteriors);

  return (
    <div className={cn('p-4 rounded-xl bg-surface-1 border border-border', className)}>
      {/* Header with paradigm selector */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary">
          Posterior Probabilities
        </h3>
        {onParadigmChange && paradigmIds.length > 1 && (
          <ParadigmSelector
            paradigms={paradigmIds.map((id) => ({ id, name: id } as any))}
            selectedId={activeParadigm}
            onChange={onParadigmChange}
          />
        )}
      </div>

      {/* Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
          >
            <XAxis
              type="number"
              domain={[0, 1]}
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
              stroke="var(--color-text-muted)"
              fontSize={12}
            />
            <YAxis
              type="category"
              dataKey="displayId"
              stroke="var(--color-text-muted)"
              fontSize={12}
              width={40}
            />
            <Tooltip
              content={<CustomTooltip showPrior={showPriors} />}
              cursor={{ fill: 'rgba(255,255,255,0.05)' }}
            />

            {/* Prior bars (if showing) */}
            {showPriors && (
              <Bar
                dataKey="prior"
                fill="var(--color-surface-3)"
                radius={[0, 4, 4, 0]}
                barSize={12}
              />
            )}

            {/* Posterior bars */}
            <Bar
              dataKey="posterior"
              radius={[0, 4, 4, 0]}
              barSize={showPriors ? 12 : 20}
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color}
                  opacity={entry.isHighlighted ? 1 : 0.8}
                  stroke={entry.isHighlighted ? 'white' : 'none'}
                  strokeWidth={entry.isHighlighted ? 2 : 0}
                />
              ))}
            </Bar>

            {/* Reference line at 0.5 */}
            <ReferenceLine
              x={0.5}
              stroke="var(--color-text-muted)"
              strokeDasharray="3 3"
              opacity={0.3}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      {showPriors && (
        <div className="flex items-center justify-center gap-6 mt-4 text-xs text-text-secondary">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-surface-3" />
            <span>Prior</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-accent" />
            <span>Posterior</span>
          </div>
        </div>
      )}
    </div>
  );
}

// Custom tooltip
interface TooltipPayload {
  id: string;
  name: string;
  posterior: number;
  prior: number;
  color: string;
}

function CustomTooltip({
  active,
  payload,
  showPrior,
}: {
  active?: boolean;
  payload?: Array<{ payload: TooltipPayload }>;
  showPrior?: boolean;
}) {
  if (!active || !payload?.length) return null;

  const data = payload[0].payload;

  return (
    <div className="px-3 py-2 rounded-lg bg-surface-2 border border-border shadow-lg">
      <div className="flex items-center gap-2 mb-1">
        <div
          className="w-3 h-3 rounded"
          style={{ backgroundColor: data.color }}
        />
        <span className="font-medium text-text-primary">{data.name}</span>
      </div>
      <div className="text-sm text-text-secondary">
        Posterior: <span className="text-text-primary font-medium">{formatPercent(data.posterior)}</span>
      </div>
      {showPrior && (
        <div className="text-sm text-text-secondary">
          Prior: <span className="text-text-muted">{formatPercent(data.prior)}</span>
        </div>
      )}
    </div>
  );
}

// Compact version for sidebar
interface MiniBarChartProps {
  hypotheses: Hypothesis[];
  posteriors: Record<string, number>;
  className?: string;
}

export function MiniHypothesisBarChart({
  hypotheses,
  posteriors,
  className,
}: MiniBarChartProps) {
  const sorted = [...hypotheses].sort(
    (a, b) => (posteriors[b.id] || 0) - (posteriors[a.id] || 0)
  );

  return (
    <div className={cn('space-y-2', className)}>
      {sorted.slice(0, 5).map((h) => {
        const value = posteriors[h.id] || 0;
        const color = getHypothesisColor(h.id, h.associated_paradigms);

        return (
          <div key={h.id} className="flex items-center gap-2">
            <span className="text-xs text-text-muted w-8">
              {formatHypothesisId(h.id)}
            </span>
            <div className="flex-1 h-2 bg-surface-2 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: color }}
                initial={{ width: 0 }}
                animate={{ width: `${value * 100}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
            <span className="text-xs font-medium text-text-primary w-10 text-right">
              {formatPercent(value)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
