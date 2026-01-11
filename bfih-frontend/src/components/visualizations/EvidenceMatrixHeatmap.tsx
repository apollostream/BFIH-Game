import { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils';
import {
  formatHypothesisId,
  getWoEHeatmapColor,
  formatWoE,
  calculateWoE,
  clampProbability,
} from '../../utils';
import type { Hypothesis, EvidenceCluster, Paradigm, PriorWithJustification } from '../../types';
import { ParadigmSelector } from '../game/ParadigmCard';
import { Tooltip } from '../ui/Tooltip';

// Type for priors - can be number or object with probability
type PriorValue = number | PriorWithJustification;
type PriorsByParadigm = Record<string, Record<string, PriorValue>>;

interface EvidenceMatrixHeatmapProps {
  hypotheses: Hypothesis[];
  clusters: EvidenceCluster[];
  paradigms: Paradigm[];
  activeParadigm: string;
  priorsByParadigm?: PriorsByParadigm;  // Paradigm-specific priors for correct WoE calculation
  onParadigmChange?: (paradigmId: string) => void;
  onCellClick?: (hypothesisId: string, clusterId: string) => void;
  className?: string;
}

export function EvidenceMatrixHeatmap({
  hypotheses,
  clusters,
  paradigms,
  activeParadigm,
  priorsByParadigm,
  onParadigmChange,
  onCellClick,
  className,
}: EvidenceMatrixHeatmapProps) {
  const [hoveredCell, setHoveredCell] = useState<{
    hypothesisId: string;
    clusterId: string;
  } | null>(null);

  // Helper to extract prior value (handles both number and {probability: number} formats)
  // Clamps to avoid extremes (0 or 1) which break Bayesian math
  const getPriorValue = (prior: PriorValue | undefined): number => {
    let raw: number;
    if (prior === undefined) {
      raw = 1.0 / hypotheses.length;
    } else if (typeof prior === 'number') {
      raw = prior;
    } else {
      raw = prior.probability ?? 1.0 / hypotheses.length;
    }
    return clampProbability(raw);
  };

  // Helper to get likelihoods for a cluster, supporting both formats
  const getClusterLikelihoods = (cluster: EvidenceCluster, paradigmId: string) => {
    // Try paradigm-specific likelihoods first (backend format)
    if (cluster.likelihoods_by_paradigm?.[paradigmId]) {
      return cluster.likelihoods_by_paradigm[paradigmId];
    }
    // Fall back to flat likelihoods
    return cluster.likelihoods || {};
  };

  // Build matrix data - now paradigm-aware with correct Bayesian calculation
  const matrixData = useMemo(() => {
    // Get priors for the active paradigm
    const paradigmPriors = priorsByParadigm?.[activeParadigm] || {};
    const hypIds = hypotheses.map(h => h.id);

    return hypotheses.map((hypothesis) => {
      const row: Record<string, { woe: number; likelihood: number; pENotH: number; lr: number; justification?: string }> = {};

      clusters.forEach((cluster) => {
        // Check for pre-computed metrics first (from backend)
        const precomputedMetrics = cluster.bayesian_metrics_by_paradigm?.[activeParadigm]?.[hypothesis.id]
          || cluster.bayesian_metrics?.[hypothesis.id];

        if (precomputedMetrics) {
          // Use pre-computed values from backend
          row[cluster.cluster_id] = {
            woe: precomputedMetrics.woe,
            likelihood: precomputedMetrics.p_e_h,
            pENotH: precomputedMetrics.p_e_not_h,
            lr: precomputedMetrics.lr,
            justification: undefined,
          };
        } else {
          // Compute using correct Bayesian formula
          // All probabilities are clamped to avoid extremes (0 or 1)
          const clusterLikelihoods = getClusterLikelihoods(cluster, activeParadigm);
          const likelihoodData = clusterLikelihoods[hypothesis.id];
          const pEH = clampProbability(likelihoodData?.probability ?? 0.5);
          const priorI = getPriorValue(paradigmPriors[hypothesis.id]);
          const complementPrior = 1.0 - priorI;

          // P(E|¬H_i) = Σ P(E|H_j) × P(H_j) / (1 - P(H_i)) for j ≠ i
          let pENotH = 0.5;  // Default if calculation fails
          if (complementPrior > 0.001) {
            pENotH = hypIds
              .filter(hj => hj !== hypothesis.id)
              .reduce((sum, hj) => {
                const pEHj = clampProbability(clusterLikelihoods[hj]?.probability ?? 0.5);
                const priorJ = getPriorValue(paradigmPriors[hj]);
                return sum + pEHj * (priorJ / complementPrior);
              }, 0);
          }

          // Likelihood ratio and WoE
          const lr = pEH / Math.max(pENotH, 0.001);
          const woe = calculateWoE(lr);

          row[cluster.cluster_id] = {
            woe: isFinite(woe) ? woe : 0,
            likelihood: pEH,
            pENotH,
            lr,
            justification: likelihoodData?.justification,
          };
        }
      });

      return {
        hypothesisId: hypothesis.id,
        hypothesis,
        data: row,
      };
    });
  }, [hypotheses, clusters, activeParadigm, priorsByParadigm]);

  // Calculate max absolute WoE for scaling (reserved for future dynamic scaling)
  const _maxWoE = useMemo(() => {
    let max = 5;
    matrixData.forEach((row) => {
      Object.values(row.data).forEach((cell) => {
        max = Math.max(max, Math.abs(cell.woe));
      });
    });
    return max;
  }, [matrixData]);
  void _maxWoE;

  return (
    <div className={cn('p-4 rounded-xl bg-surface-1 border border-border', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-text-primary">
            Evidence Matrix
          </h3>
          <p className="text-sm text-text-secondary">
            Weight of Evidence (WoE) in decibans
          </p>
        </div>
        {onParadigmChange && paradigms.length > 1 && (
          <ParadigmSelector
            paradigms={paradigms}
            selectedId={activeParadigm}
            onChange={onParadigmChange}
          />
        )}
      </div>

      {/* Matrix */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          {/* Header row with cluster IDs */}
          <thead>
            <tr>
              <th className="p-2 text-left text-sm text-text-muted">Hypothesis</th>
              {clusters.map((cluster) => (
                <th
                  key={cluster.cluster_id}
                  className="p-2 text-center text-sm text-text-muted"
                >
                  <Tooltip content={cluster.cluster_name} position="top">
                    <span className="cursor-help">{cluster.cluster_id}</span>
                  </Tooltip>
                </th>
              ))}
              <th className="p-2 text-center text-sm text-text-muted">Net</th>
            </tr>
          </thead>

          <tbody>
            {matrixData.map((row, rowIndex) => {
              const netWoE = Object.values(row.data).reduce(
                (sum, cell) => sum + cell.woe,
                0
              );

              return (
                <motion.tr
                  key={row.hypothesisId}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: rowIndex * 0.05 }}
                >
                  {/* Hypothesis ID */}
                  <td className="p-2">
                    <span className="font-medium text-text-primary">
                      {formatHypothesisId(row.hypothesisId)}
                    </span>
                  </td>

                  {/* WoE cells */}
                  {clusters.map((cluster) => {
                    const cellData = row.data[cluster.cluster_id];
                    const isHovered =
                      hoveredCell?.hypothesisId === row.hypothesisId &&
                      hoveredCell?.clusterId === cluster.cluster_id;

                    // Guard against missing cell data
                    if (!cellData) {
                      return (
                        <td key={cluster.cluster_id} className="p-1">
                          <div className="w-12 h-12 rounded-lg bg-surface-2 flex items-center justify-center text-xs text-text-muted">
                            --
                          </div>
                        </td>
                      );
                    }

                    return (
                      <td key={cluster.cluster_id} className="p-1">
                        <Tooltip
                          content={
                            <div>
                              <div className="font-medium mb-1">
                                {row.hypothesis.name} × {cluster.cluster_name}
                              </div>
                              <div>P(E|H): {(cellData.likelihood * 100).toFixed(1)}%</div>
                              <div>P(E|¬H): {(cellData.pENotH * 100).toFixed(1)}%</div>
                              <div>LR: {cellData.lr.toFixed(3)}</div>
                              <div>WoE: {formatWoE(cellData.woe)}</div>
                              {cellData.justification && (
                                <div className="mt-2 text-text-secondary text-xs">
                                  {cellData.justification}
                                </div>
                              )}
                            </div>
                          }
                          position="top"
                        >
                          <motion.div
                            onHoverStart={() =>
                              setHoveredCell({
                                hypothesisId: row.hypothesisId,
                                clusterId: cluster.cluster_id,
                              })
                            }
                            onHoverEnd={() => setHoveredCell(null)}
                            onClick={() =>
                              onCellClick?.(row.hypothesisId, cluster.cluster_id)
                            }
                            whileHover={{ scale: 1.1 }}
                            className={cn(
                              'w-12 h-12 rounded-lg flex items-center justify-center',
                              'text-xs font-medium cursor-pointer',
                              'transition-shadow',
                              isHovered && 'ring-2 ring-white/50 shadow-lg'
                            )}
                            style={{
                              backgroundColor: getWoEHeatmapColor(cellData.woe),
                              color:
                                Math.abs(cellData.woe) > 3 ? 'white' : 'var(--color-text-primary)',
                            }}
                          >
                            {cellData.woe > 0 ? '+' : ''}
                            {cellData.woe.toFixed(1)}
                          </motion.div>
                        </Tooltip>
                      </td>
                    );
                  })}

                  {/* Net WoE */}
                  <td className="p-1">
                    <div
                      className={cn(
                        'w-14 h-12 rounded-lg flex items-center justify-center',
                        'text-sm font-bold',
                        'border-2'
                      )}
                      style={{
                        backgroundColor: `${getWoEHeatmapColor(netWoE)}30`,
                        borderColor: getWoEHeatmapColor(netWoE),
                        color: getWoEHeatmapColor(netWoE),
                      }}
                    >
                      {netWoE > 0 ? '+' : ''}
                      {netWoE.toFixed(1)}
                    </div>
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-1 mt-4 pt-4 border-t border-border">
        <span className="text-xs text-text-muted mr-2">Strong refute</span>
        {[-10, -5, 0, 5, 10].map((woe) => (
          <div
            key={woe}
            className="w-8 h-4 rounded"
            style={{ backgroundColor: getWoEHeatmapColor(woe) }}
          />
        ))}
        <span className="text-xs text-text-muted ml-2">Strong support</span>
      </div>
    </div>
  );
}

// Compact row version for evidence round
interface EvidenceWoERowProps {
  hypothesis: Hypothesis;
  likelihoods: Record<string, { probability: number; justification?: string }>;
  className?: string;
}

export function EvidenceWoERow({
  hypothesis,
  likelihoods,
  className,
}: EvidenceWoERowProps) {
  const likelihood = likelihoods[hypothesis.id]?.probability || 0.5;
  // Simplified WoE calculation
  const avgLikelihood = Object.values(likelihoods)
    .reduce((sum, l) => sum + l.probability, 0) / Object.keys(likelihoods).length;
  const lr = likelihood / Math.max(avgLikelihood, 0.01);
  const woe = calculateWoE(lr);

  return (
    <div
      className={cn(
        'flex items-center gap-3 p-2 rounded-lg',
        'bg-surface-2',
        className
      )}
    >
      <span className="text-sm font-medium text-text-primary w-8">
        {formatHypothesisId(hypothesis.id)}
      </span>
      <div className="flex-1">
        <div className="h-2 bg-surface-1 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${likelihood * 100}%`,
              backgroundColor: getWoEHeatmapColor(woe),
            }}
          />
        </div>
      </div>
      <div
        className="px-2 py-1 rounded text-xs font-medium"
        style={{
          backgroundColor: `${getWoEHeatmapColor(woe)}30`,
          color: getWoEHeatmapColor(woe),
        }}
      >
        {formatWoE(woe)}
      </div>
    </div>
  );
}
