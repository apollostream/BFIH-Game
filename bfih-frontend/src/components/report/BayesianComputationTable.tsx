// Bayesian Computation Table - displays LR and WoE metrics per cluster/hypothesis

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { cn, formatPercent } from '../../utils';
import type { EvidenceCluster, Hypothesis, ClusterLikelihood } from '../../types';

interface BayesianComputationTableProps {
  clusters: EvidenceCluster[];
  hypotheses: Hypothesis[];
  activeParadigm: string;
  priors: Record<string, number>;
  posteriors: Record<string, number>;
  className?: string;
}

// Calculate Weight of Evidence in decibans: 10 * log10(LR)
function calculateWoE(likelihood: number, prior: number): number {
  if (prior <= 0 || prior >= 1 || likelihood <= 0) return 0;
  const lr = likelihood / prior;
  if (lr <= 0) return 0;
  return 10 * Math.log10(lr);
}

// Get color class based on WoE value
function getWoEColorClass(woe: number): string {
  if (woe >= 5) return 'text-orange-400';
  if (woe >= 2) return 'text-orange-300';
  if (woe <= -5) return 'text-blue-400';
  if (woe <= -2) return 'text-blue-300';
  return 'text-gray-400';
}

// Get background color class based on likelihood
function getLikelihoodBgClass(prob: number): string {
  if (prob >= 0.7) return 'bg-emerald-500/20 border-emerald-500/30';
  if (prob >= 0.5) return 'bg-emerald-500/10 border-emerald-500/20';
  if (prob <= 0.3) return 'bg-red-500/20 border-red-500/30';
  if (prob <= 0.5) return 'bg-red-500/10 border-red-500/20';
  return 'bg-surface-2 border-border';
}

export function BayesianComputationTable({
  clusters,
  hypotheses,
  activeParadigm,
  priors,
  posteriors,
  className,
}: BayesianComputationTableProps) {
  if (!clusters.length || !hypotheses.length) {
    return (
      <Card className={cn('p-6', className)}>
        <p className="text-text-secondary text-center">
          No Bayesian computation data available
        </p>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      <div>
        <h2 className="text-xl font-semibold text-text-primary">
          Bayesian Computation
        </h2>
        <p className="text-text-secondary text-sm mt-1">
          Likelihood ratios (LR) and Weight of Evidence (WoE) in decibans for each cluster-hypothesis pair.
          Positive WoE supports the hypothesis; negative WoE refutes it.
        </p>
      </div>

      {/* Summary Posteriors Table */}
      <Card className="p-5">
        <h3 className="text-lg font-semibold text-text-primary mb-4">
          Final Posteriors Summary
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 pr-4 text-text-muted font-medium">
                  Hypothesis
                </th>
                <th className="text-center py-2 px-3 text-text-muted font-medium">
                  Prior
                </th>
                <th className="text-center py-2 px-3 text-text-muted font-medium">
                  Posterior
                </th>
                <th className="text-center py-2 pl-3 text-text-muted font-medium">
                  Change
                </th>
              </tr>
            </thead>
            <tbody>
              {hypotheses.map((hyp) => {
                const prior = priors[hyp.id] ?? 0;
                const posterior = posteriors[hyp.id] ?? prior;
                const change = posterior - prior;

                return (
                  <tr key={hyp.id} className="border-b border-border/50">
                    <td className="py-2 pr-4">
                      <span className="text-text-primary font-medium">
                        {hyp.id}
                      </span>
                      <span className="text-text-secondary ml-2">
                        {hyp.name.length > 50
                          ? hyp.name.slice(0, 50) + '...'
                          : hyp.name}
                      </span>
                    </td>
                    <td className="text-center py-2 px-3 text-text-secondary">
                      {formatPercent(prior)}
                    </td>
                    <td className="text-center py-2 px-3">
                      <span className="text-text-primary font-medium">
                        {formatPercent(posterior)}
                      </span>
                    </td>
                    <td className="text-center py-2 pl-3">
                      <span
                        className={cn(
                          'font-medium',
                          change > 0.05 ? 'text-emerald-400' :
                          change < -0.05 ? 'text-red-400' :
                          'text-gray-400'
                        )}
                      >
                        {change >= 0 ? '+' : ''}{formatPercent(change)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Per-Cluster Metrics */}
      {clusters.map((cluster, clusterIndex) => (
        <ClusterMetricsCard
          key={cluster.cluster_id}
          cluster={cluster}
          clusterIndex={clusterIndex}
          hypotheses={hypotheses}
          activeParadigm={activeParadigm}
          priors={priors}
        />
      ))}

      {/* Legend */}
      <Card className="p-4">
        <h4 className="text-sm font-medium text-text-muted mb-2">Legend</h4>
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-orange-400 font-medium">+5 db</span>
            <span className="text-text-secondary">Strong support</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-orange-300 font-medium">+2 db</span>
            <span className="text-text-secondary">Weak support</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400 font-medium">0 db</span>
            <span className="text-text-secondary">Neutral</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-blue-300 font-medium">-2 db</span>
            <span className="text-text-secondary">Weak refutation</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-blue-400 font-medium">-5 db</span>
            <span className="text-text-secondary">Strong refutation</span>
          </div>
        </div>
      </Card>
    </div>
  );
}

interface ClusterMetricsCardProps {
  cluster: EvidenceCluster;
  clusterIndex: number;
  hypotheses: Hypothesis[];
  activeParadigm: string;
  priors: Record<string, number>;
}

function ClusterMetricsCard({
  cluster,
  clusterIndex,
  hypotheses,
  activeParadigm,
  priors,
}: ClusterMetricsCardProps) {
  // Get likelihoods for this cluster (paradigm-specific if available)
  const likelihoods = cluster.likelihoods_by_paradigm?.[activeParadigm]
    || cluster.likelihoods
    || {};

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: clusterIndex * 0.1 }}
    >
      <Card className="p-5">
        <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2 mb-4">
          <Badge variant="secondary" className="text-xs">
            C{clusterIndex + 1}
          </Badge>
          {cluster.cluster_name}
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 pr-4 text-text-muted font-medium">
                  Hypothesis
                </th>
                <th className="text-center py-2 px-3 text-text-muted font-medium">
                  P(E|H)
                </th>
                <th className="text-center py-2 px-3 text-text-muted font-medium">
                  Prior
                </th>
                <th className="text-center py-2 px-3 text-text-muted font-medium">
                  LR
                </th>
                <th className="text-center py-2 pl-3 text-text-muted font-medium">
                  WoE (db)
                </th>
              </tr>
            </thead>
            <tbody>
              {hypotheses.map((hyp) => {
                const likelihoodData = likelihoods[hyp.id];
                const prob = typeof likelihoodData === 'number'
                  ? likelihoodData
                  : likelihoodData?.probability ?? 0.5;
                const prior = priors[hyp.id] ?? 0.5;
                const lr = prior > 0 ? prob / prior : 1;
                const woe = calculateWoE(prob, prior);

                return (
                  <tr key={hyp.id} className="border-b border-border/50">
                    <td className="py-2 pr-4">
                      <span className="text-text-primary font-medium">
                        {hyp.id}
                      </span>
                      <span className="text-text-secondary ml-2 text-xs">
                        {hyp.name.length > 30
                          ? hyp.name.slice(0, 30) + '...'
                          : hyp.name}
                      </span>
                    </td>
                    <td className="text-center py-2 px-3">
                      <span
                        className={cn(
                          'inline-block px-2 py-0.5 rounded border text-xs font-medium',
                          getLikelihoodBgClass(prob)
                        )}
                      >
                        {formatPercent(prob)}
                      </span>
                    </td>
                    <td className="text-center py-2 px-3 text-text-secondary">
                      {formatPercent(prior)}
                    </td>
                    <td className="text-center py-2 px-3 text-text-primary font-medium">
                      {lr.toFixed(2)}
                    </td>
                    <td className="text-center py-2 pl-3">
                      <span
                        className={cn(
                          'font-medium',
                          getWoEColorClass(woe)
                        )}
                      >
                        {woe >= 0 ? '+' : ''}{woe.toFixed(1)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
}
