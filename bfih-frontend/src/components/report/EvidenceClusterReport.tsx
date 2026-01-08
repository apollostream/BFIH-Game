// Evidence Cluster Report - displays evidence items per cluster

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { cn } from '../../utils';
import type { EvidenceCluster, EvidenceItem } from '../../types';

interface EvidenceClusterReportProps {
  clusters: EvidenceCluster[];
  evidenceItems: EvidenceItem[];
  className?: string;
}

export function EvidenceClusterReport({
  clusters,
  evidenceItems,
  className,
}: EvidenceClusterReportProps) {
  // Build a map of evidence items by ID for quick lookup
  const evidenceMap = useMemo(() => {
    const map: Record<string, EvidenceItem> = {};
    for (const item of evidenceItems) {
      map[item.evidence_id] = item;
    }
    return map;
  }, [evidenceItems]);

  if (!clusters.length) {
    return (
      <Card className={cn('p-6', className)}>
        <p className="text-text-secondary text-center">
          No evidence clusters available
        </p>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      <div>
        <h2 className="text-xl font-semibold text-text-primary">
          Evidence Clusters
        </h2>
        <p className="text-text-secondary text-sm mt-1">
          Evidence items grouped by thematic relevance for Bayesian updating.
        </p>
      </div>

      {clusters.map((cluster, clusterIndex) => (
        <ClusterCard
          key={cluster.cluster_id}
          cluster={cluster}
          clusterIndex={clusterIndex}
          evidenceMap={evidenceMap}
        />
      ))}
    </div>
  );
}

interface ClusterCardProps {
  cluster: EvidenceCluster;
  clusterIndex: number;
  evidenceMap: Record<string, EvidenceItem>;
}

function ClusterCard({
  cluster,
  clusterIndex,
  evidenceMap,
}: ClusterCardProps) {
  // Get evidence items for this cluster
  const clusterItems = useMemo(() => {
    // First try direct items on the cluster
    if (cluster.items?.length) {
      return cluster.items;
    }
    // Otherwise look up by evidence_ids
    if (cluster.evidence_ids?.length) {
      return cluster.evidence_ids
        .map((id) => evidenceMap[id])
        .filter(Boolean);
    }
    return [];
  }, [cluster, evidenceMap]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: clusterIndex * 0.1 }}
    >
      <Card className="p-5">
        {/* Cluster Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-text-primary flex items-center gap-2">
              <Badge variant="secondary" className="text-xs">
                C{clusterIndex + 1}
              </Badge>
              {cluster.cluster_name}
            </h3>
            {cluster.description && (
              <p className="text-text-secondary text-sm mt-1">
                {cluster.description}
              </p>
            )}
          </div>
          <Badge>
            {clusterItems.length} item{clusterItems.length !== 1 ? 's' : ''}
          </Badge>
        </div>

        {/* Evidence Items List */}
        {clusterItems.length > 0 ? (
          <div className="space-y-3">
            {clusterItems.map((item) => (
              <div
                key={item.evidence_id}
                className="p-3 bg-surface-1 rounded-lg border border-border"
              >
                <div className="flex items-start gap-3">
                  <Badge variant="secondary" className="shrink-0 text-xs">
                    {item.evidence_id}
                  </Badge>
                  <div className="flex-1 min-w-0">
                    <p className="text-text-primary text-sm">
                      {item.description || item.content}
                    </p>
                    {item.citation_apa && (
                      <p className="text-text-muted text-xs mt-1 italic">
                        {item.citation_apa}
                      </p>
                    )}
                    {item.source_url && !item.citation_apa && (
                      <a
                        href={item.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-accent text-xs mt-1 hover:underline block truncate"
                      >
                        {item.source_name || item.source_url}
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-text-muted text-sm italic">
            Evidence items: {cluster.evidence_ids?.join(', ') || 'None specified'}
          </p>
        )}

        {cluster.conditional_independence_justification && (
          <p className="text-text-muted text-xs mt-4 pt-3 border-t border-border italic">
            Independence justification: {cluster.conditional_independence_justification}
          </p>
        )}
      </Card>
    </motion.div>
  );
}
