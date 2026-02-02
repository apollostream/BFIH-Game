// Component for making predictions about evidence clusters

import { motion } from 'framer-motion';
import { Card } from '../ui/Card';
import { cn } from '../../utils';
import type { Hypothesis, PredictionConfidence, ClusterPrediction } from '../../types';

interface PredictionCardProps {
  clusterId: string;
  clusterName: string;
  clusterDescription?: string;
  hypotheses: Hypothesis[];
  prediction: ClusterPrediction | null;
  onPredictionChange: (
    clusterId: string,
    hypothesisId: string | null,
    confidence: PredictionConfidence
  ) => void;
  disabled?: boolean;
  className?: string;
}

const confidenceOptions: { value: PredictionConfidence; label: string }[] = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
];

export function PredictionCard({
  clusterId,
  clusterName,
  clusterDescription,
  hypotheses,
  prediction,
  onPredictionChange,
  disabled = false,
  className,
}: PredictionCardProps) {
  const selectedHypothesis = prediction?.predictedSupports ?? null;
  const confidence = prediction?.confidence ?? 'medium';

  const handleHypothesisSelect = (hypothesisId: string | null) => {
    if (disabled) return;
    onPredictionChange(clusterId, hypothesisId, confidence);
  };

  const handleConfidenceChange = (newConfidence: PredictionConfidence) => {
    if (disabled) return;
    onPredictionChange(clusterId, selectedHypothesis, newConfidence);
  };

  return (
    <Card
      variant="bordered"
      className={cn(
        'transition-all duration-200',
        disabled && 'opacity-60',
        className
      )}
    >
      {/* Cluster Header */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-text-primary">
          {clusterName}
        </h3>
        {clusterDescription && (
          <p className="text-sm text-text-muted mt-1 line-clamp-2">
            {clusterDescription}
          </p>
        )}
      </div>

      {/* Prediction Question */}
      <div className="mb-4">
        <p className="text-sm font-medium text-text-secondary mb-3">
          This evidence will most support:
        </p>

        {/* Hypothesis Options */}
        <div className="space-y-2">
          {hypotheses.map((hypothesis) => (
            <motion.label
              key={hypothesis.id}
              whileHover={!disabled ? { scale: 1.01 } : undefined}
              whileTap={!disabled ? { scale: 0.99 } : undefined}
              className={cn(
                'flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all',
                'border-2',
                selectedHypothesis === hypothesis.id
                  ? 'border-accent bg-accent/10'
                  : 'border-transparent bg-surface-2 hover:bg-surface-2/80',
                disabled && 'cursor-not-allowed'
              )}
            >
              <input
                type="radio"
                name={`prediction-${clusterId}`}
                value={hypothesis.id}
                checked={selectedHypothesis === hypothesis.id}
                onChange={() => handleHypothesisSelect(hypothesis.id)}
                disabled={disabled}
                className="sr-only"
              />
              <div
                className={cn(
                  'w-4 h-4 rounded-full border-2 flex items-center justify-center',
                  selectedHypothesis === hypothesis.id
                    ? 'border-accent'
                    : 'border-text-muted'
                )}
              >
                {selectedHypothesis === hypothesis.id && (
                  <div className="w-2 h-2 rounded-full bg-accent" />
                )}
              </div>
              <div className="flex-1">
                <span className="text-sm font-medium text-text-primary">
                  {hypothesis.id}
                </span>
                <span className="text-sm text-text-secondary ml-2">
                  {hypothesis.name}
                </span>
              </div>
            </motion.label>
          ))}

          {/* None/Mixed Option */}
          <motion.label
            whileHover={!disabled ? { scale: 1.01 } : undefined}
            whileTap={!disabled ? { scale: 0.99 } : undefined}
            className={cn(
              'flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all',
              'border-2',
              selectedHypothesis === null && prediction !== null
                ? 'border-accent bg-accent/10'
                : 'border-transparent bg-surface-2 hover:bg-surface-2/80',
              disabled && 'cursor-not-allowed'
            )}
          >
            <input
              type="radio"
              name={`prediction-${clusterId}`}
              value="none"
              checked={selectedHypothesis === null && prediction !== null}
              onChange={() => handleHypothesisSelect(null)}
              disabled={disabled}
              className="sr-only"
            />
            <div
              className={cn(
                'w-4 h-4 rounded-full border-2 flex items-center justify-center',
                selectedHypothesis === null && prediction !== null
                  ? 'border-accent'
                  : 'border-text-muted'
              )}
            >
              {selectedHypothesis === null && prediction !== null && (
                <div className="w-2 h-2 rounded-full bg-accent" />
              )}
            </div>
            <span className="text-sm text-text-secondary">
              None / Mixed evidence
            </span>
          </motion.label>
        </div>
      </div>

      {/* Confidence Selector */}
      {prediction !== null && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="pt-4 border-t border-border"
        >
          <p className="text-sm font-medium text-text-secondary mb-2">
            Confidence level:
          </p>
          <div className="flex gap-2">
            {confidenceOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => handleConfidenceChange(option.value)}
                disabled={disabled}
                className={cn(
                  'flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all',
                  confidence === option.value
                    ? option.value === 'high'
                      ? 'bg-paradigm-k1 text-white'
                      : option.value === 'medium'
                      ? 'bg-accent text-white'
                      : 'bg-surface-3 text-text-primary'
                    : 'bg-surface-2 text-text-secondary hover:bg-surface-3',
                  disabled && 'cursor-not-allowed opacity-60'
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
          {confidence === 'high' && (
            <p className="text-xs text-paradigm-k1 mt-2">
              High confidence: +25 pts if correct, -5 pts if wrong
            </p>
          )}
        </motion.div>
      )}
    </Card>
  );
}

// Result display component for after evidence is revealed
interface PredictionResultCardProps {
  clusterName: string;
  predicted: string | null;
  actual: string | null;
  correct: boolean;
  confidence: PredictionConfidence;
  points: number;
  hypotheses: Hypothesis[];
  className?: string;
}

export function PredictionResultCard({
  clusterName,
  predicted,
  actual,
  correct,
  confidence,
  points,
  hypotheses,
  className,
}: PredictionResultCardProps) {
  const getHypothesisDisplay = (id: string | null) => {
    if (id === null) return 'None/Mixed';
    const hyp = hypotheses.find((h) => h.id === id);
    return hyp ? `${hyp.id}: ${hyp.name}` : id;
  };

  return (
    <Card
      variant="bordered"
      className={cn(
        'transition-all',
        correct ? 'border-green-500/50 bg-green-500/5' : 'border-red-500/30 bg-red-500/5',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <h4 className="font-medium text-text-primary">{clusterName}</h4>
          <div className="mt-2 space-y-1 text-sm">
            <p className="text-text-secondary">
              Your prediction:{' '}
              <span className="text-text-primary">
                {getHypothesisDisplay(predicted)}
              </span>
              <span className="text-text-muted ml-2">({confidence} confidence)</span>
            </p>
            <p className="text-text-secondary">
              Actual:{' '}
              <span className="text-text-primary">
                {getHypothesisDisplay(actual)}
              </span>
            </p>
          </div>
        </div>
        <div
          className={cn(
            'text-lg font-bold',
            points > 0 ? 'text-green-500' : points < 0 ? 'text-red-500' : 'text-text-muted'
          )}
        >
          {points > 0 ? '+' : ''}{points}
        </div>
      </div>
    </Card>
  );
}
