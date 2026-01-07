import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils';
import type { EvidenceItem, EvidenceCluster, Hypothesis } from '../../types';
import { Card } from '../ui/Card';
import { Badge, EvidenceTypeBadge } from '../ui/Badge';
import { evidenceRevealVariants } from '../../utils/animations';

interface EvidenceCardProps {
  evidence: EvidenceItem;
  isRevealed?: boolean;
  onReveal?: () => void;
  className?: string;
}

export function EvidenceCard({
  evidence,
  isRevealed = true,
  onReveal,
  className,
}: EvidenceCardProps) {
  if (!isRevealed) {
    return (
      <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={onReveal}
        className={cn(
          'p-6 rounded-xl cursor-pointer',
          'bg-surface-2 border border-border',
          'flex items-center justify-center',
          'hover:bg-surface-3 transition-colors',
          className
        )}
      >
        <div className="text-center">
          <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-3">
            <QuestionIcon className="w-6 h-6 text-accent" />
          </div>
          <p className="text-text-secondary">Click to reveal evidence</p>
          <p className="text-xs text-text-muted mt-1">{evidence.evidence_id}</p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      variants={evidenceRevealVariants}
      initial="initial"
      animate="animate"
    >
      <Card className={cn('relative', className)}>
        {/* Evidence ID badge */}
        <div className="absolute -top-3 left-4">
          <Badge variant="primary" size="sm">
            {evidence.evidence_id}
          </Badge>
        </div>

        <div className="pt-2">
          {/* Header with type */}
          <div className="flex items-start justify-between mb-3">
            <EvidenceTypeBadge evidenceType={evidence.evidence_type} />
            <a
              href={evidence.source_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-xs text-accent hover:underline flex items-center gap-1"
            >
              Source
              <ExternalLinkIcon className="w-3 h-3" />
            </a>
          </div>

          {/* Description */}
          <p className="text-sm text-text-primary mb-3">
            {evidence.description}
          </p>

          {/* Hypothesis support/refute */}
          <div className="flex flex-wrap gap-2 mb-3">
            {evidence.supports_hypotheses.map((hId) => (
              <Badge key={hId} variant="success" size="sm" dot>
                Supports {hId}
              </Badge>
            ))}
            {evidence.refutes_hypotheses.map((hId) => (
              <Badge key={hId} variant="danger" size="sm" dot>
                Refutes {hId}
              </Badge>
            ))}
          </div>

          {/* Citation */}
          <div className="text-xs text-text-muted border-t border-border pt-3">
            <p className="font-medium mb-1">Citation:</p>
            <p className="italic">{evidence.citation_apa}</p>
            <p className="mt-1">Accessed: {evidence.date_accessed}</p>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

// Evidence cluster component
export interface EvidenceClusterCardProps {
  cluster: EvidenceCluster;
  evidenceItems?: EvidenceItem[];
  hypotheses?: Hypothesis[]; // Used for likelihood display
  isExpanded?: boolean;
  revealed?: boolean; // Alias for isExpanded
  onClick?: () => void;
  onToggle?: () => void;
  className?: string;
}

export function EvidenceClusterCard({
  cluster,
  evidenceItems = [],
  hypotheses: _hypotheses = [],
  isExpanded: isExpandedProp = false,
  revealed,
  onClick,
  onToggle,
  className,
}: EvidenceClusterCardProps) {
  void _hypotheses; // Reserved for future likelihood display enhancements
  const isExpanded = revealed ?? isExpandedProp;
  const handleClick = onClick || onToggle;
  const clusterEvidence = cluster.items || evidenceItems.filter(
    (e) => cluster.evidence_ids?.includes(e.evidence_id)
  );

  return (
    <Card className={cn('overflow-hidden', className)}>
      {/* Cluster header */}
      <button
        onClick={handleClick}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-surface-2 transition-colors"
      >
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="default">{cluster.cluster_id}</Badge>
            <h3 className="font-semibold text-text-primary">
              {cluster.cluster_name}
            </h3>
          </div>
          <p className="text-sm text-text-secondary line-clamp-1">
            {cluster.description}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="info" size="sm">
            {clusterEvidence.length} items
          </Badge>
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDownIcon className="w-5 h-5 text-text-muted" />
          </motion.div>
        </div>
      </button>

      {/* Expanded content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="p-4 pt-0 space-y-3 border-t border-border">
              {/* Conditional independence note */}
              <div className="p-3 rounded-lg bg-surface-2 text-xs text-text-secondary">
                <span className="font-medium text-text-primary">
                  Conditional Independence:
                </span>{' '}
                {cluster.conditional_independence_justification}
              </div>

              {/* Evidence items */}
              <div className="space-y-3">
                {clusterEvidence.map((evidence) => (
                  <EvidenceCard
                    key={evidence.evidence_id}
                    evidence={evidence}
                  />
                ))}
              </div>

              {/* Likelihoods */}
              {cluster.likelihoods && (
                <div className="pt-3 border-t border-border">
                  <h4 className="text-sm font-medium text-text-primary mb-2">
                    Cluster Likelihoods
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(cluster.likelihoods).map(([hId, data]) => (
                      <div key={hId} className="flex items-center gap-3">
                        <span className="text-sm text-text-secondary w-8">
                          {hId}
                        </span>
                        <div className="flex-1 h-2 bg-surface-2 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-accent rounded-full"
                            style={{ width: `${data.probability * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-text-primary w-12 text-right">
                          {(data.probability * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

// Icons
function QuestionIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

function ExternalLinkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
      />
    </svg>
  );
}

function ChevronDownIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
}
