import { useMemo, useState } from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { motion } from 'framer-motion';
import { cn } from '../../utils';
import { formatHypothesisId, getParadigmColor } from '../../utils';
import type { Hypothesis, Paradigm, PosteriorsByParadigm } from '../../types';

interface BeliefSpaceRadarProps {
  hypotheses: Hypothesis[];
  paradigms: Paradigm[];
  posteriors: PosteriorsByParadigm;
  priors?: PosteriorsByParadigm;
  showPriors?: boolean;
  enabledParadigms?: string[];
  onToggleParadigm?: (paradigmId: string) => void;
  className?: string;
}

export function BeliefSpaceRadar({
  hypotheses,
  paradigms,
  posteriors,
  priors,
  showPriors = false,
  enabledParadigms,
  onToggleParadigm,
  className,
}: BeliefSpaceRadarProps) {
  const [activeParadigms, setActiveParadigms] = useState<string[]>(
    enabledParadigms || paradigms.map((p) => p.id)
  );

  const toggleParadigm = (paradigmId: string) => {
    if (onToggleParadigm) {
      onToggleParadigm(paradigmId);
    } else {
      setActiveParadigms((prev) =>
        prev.includes(paradigmId)
          ? prev.filter((id) => id !== paradigmId)
          : [...prev, paradigmId]
      );
    }
  };

  const data = useMemo(() => {
    return hypotheses.map((h) => {
      const point: Record<string, string | number> = {
        hypothesis: formatHypothesisId(h.id),
        fullName: h.name,
      };

      paradigms.forEach((p) => {
        point[`${p.id}_posterior`] = posteriors[p.id]?.[h.id] || 0;
        if (showPriors && priors) {
          point[`${p.id}_prior`] = priors[p.id]?.[h.id] || 0;
        }
      });

      return point;
    });
  }, [hypotheses, paradigms, posteriors, priors, showPriors]);

  const effectiveParadigms = enabledParadigms || activeParadigms;

  return (
    <div className={cn('p-4 rounded-xl bg-surface-1 border border-border', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary">
          Belief Space
        </h3>
        {showPriors && (
          <div className="flex items-center gap-4 text-xs text-text-secondary">
            <div className="flex items-center gap-1">
              <div className="w-6 h-0.5 bg-current opacity-30" />
              <span>Prior</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-6 h-0.5 bg-current" />
              <span>Posterior</span>
            </div>
          </div>
        )}
      </div>

      {/* Paradigm toggles */}
      <div className="flex flex-wrap gap-2 mb-4">
        {paradigms.map((p) => {
          const isActive = effectiveParadigms.includes(p.id);
          const color = getParadigmColor(p.id);

          return (
            <motion.button
              key={p.id}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => toggleParadigm(p.id)}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm',
                'border transition-all duration-200',
                isActive
                  ? 'border-current'
                  : 'border-border bg-surface-2 opacity-50'
              )}
              style={{
                color: isActive ? color : undefined,
                backgroundColor: isActive ? `${color}15` : undefined,
                borderColor: isActive ? color : undefined,
              }}
            >
              <div
                className={cn(
                  'w-2 h-2 rounded-full',
                  !isActive && 'bg-text-muted'
                )}
                style={{ backgroundColor: isActive ? color : undefined }}
              />
              {p.name}
            </motion.button>
          );
        })}
      </div>

      {/* Radar chart */}
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
            <PolarGrid
              stroke="var(--color-border)"
              strokeDasharray="3 3"
            />
            <PolarAngleAxis
              dataKey="hypothesis"
              tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 1]}
              tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }}
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            />

            {/* Prior polygons (dashed, lighter) */}
            {showPriors &&
              paradigms.map((p) => {
                if (!effectiveParadigms.includes(p.id)) return null;
                const color = getParadigmColor(p.id);

                return (
                  <Radar
                    key={`${p.id}_prior`}
                    name={`${p.name} (Prior)`}
                    dataKey={`${p.id}_prior`}
                    stroke={color}
                    fill={color}
                    fillOpacity={0.1}
                    strokeOpacity={0.3}
                    strokeDasharray="4 4"
                  />
                );
              })}

            {/* Posterior polygons */}
            {paradigms.map((p) => {
              if (!effectiveParadigms.includes(p.id)) return null;
              const color = getParadigmColor(p.id);

              return (
                <Radar
                  key={`${p.id}_posterior`}
                  name={p.name}
                  dataKey={`${p.id}_posterior`}
                  stroke={color}
                  fill={color}
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              );
            })}

            <Tooltip content={<RadarTooltip />} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Custom tooltip
function RadarTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string; dataKey: string; payload: Record<string, unknown> }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  // Get the full hypothesis name from the data payload
  const fullName = payload[0]?.payload?.fullName as string | undefined;

  // Filter to only show posteriors (not priors) to avoid duplicate entries
  const posteriorEntries = payload.filter(entry => !entry.dataKey.endsWith('_prior'));

  return (
    <div className="px-3 py-2 rounded-lg bg-surface-2 border border-border shadow-lg">
      <div className="font-medium text-text-primary mb-1">{label}</div>
      {fullName && (
        <div className="text-xs text-text-secondary mb-2">{fullName}</div>
      )}
      <div className="space-y-1">
        {posteriorEntries.map((entry, index) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-text-secondary">
              {entry.name}:
            </span>
            <span className="text-text-primary font-medium">
              {(entry.value * 100).toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Compact mini radar for cards
interface MiniRadarProps {
  hypotheses: Hypothesis[];
  posteriors: Record<string, number>;
  color?: string;
  size?: number;
  className?: string;
}

export function MiniBeliefRadar({
  hypotheses,
  posteriors,
  color = 'var(--color-accent)',
  size = 100,
  className,
}: MiniRadarProps) {
  const data = hypotheses.map((h) => ({
    hypothesis: h.id,
    value: posteriors[h.id] || 0,
  }));

  return (
    <div className={cn('', className)} style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
          <PolarGrid stroke="var(--color-border)" strokeDasharray="2 2" />
          <PolarAngleAxis
            dataKey="hypothesis"
            tick={{ fill: 'var(--color-text-muted)', fontSize: 8 }}
          />
          <Radar
            dataKey="value"
            stroke={color}
            fill={color}
            fillOpacity={0.3}
            strokeWidth={1.5}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
