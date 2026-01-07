import { motion } from 'framer-motion';
import { cn } from '../../utils';
import { formatHypothesisId, getHypothesisColor } from '../../utils';
import type { Hypothesis } from '../../types';
import { Slider } from '../ui/Slider';
import { Badge } from '../ui/Badge';

export interface BettingSliderProps {
  hypothesis: Hypothesis;
  currentBet: number;
  maxBet: number;
  minBet?: number;
  onChange?: (value: number) => void;
  onBetChange?: (value: number) => void; // Alias for onChange
  disabled?: boolean;
  showProbability?: boolean;
  probability?: number;
  prior?: number; // Alias for probability
  className?: string;
}

export function BettingSlider({
  hypothesis,
  currentBet,
  maxBet,
  minBet = 0,
  onChange: onChangeProp,
  onBetChange,
  disabled = false,
  showProbability = false,
  probability: probabilityProp,
  prior,
  className,
}: BettingSliderProps) {
  const onChange = onChangeProp || onBetChange || (() => {});
  const probability = probabilityProp ?? prior;
  const color = getHypothesisColor(hypothesis.id, hypothesis.associated_paradigms);

  return (
    <div
      className={cn(
        'p-4 rounded-xl',
        'bg-surface-1 border border-border',
        disabled && 'opacity-50',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm"
            style={{ backgroundColor: color }}
          >
            {formatHypothesisId(hypothesis.id)}
          </div>
          <div>
            <h4 className="font-medium text-text-primary line-clamp-1">
              {hypothesis.name}
            </h4>
            {showProbability && probability !== undefined && (
              <span className="text-sm text-text-secondary">
                P = {(probability * 100).toFixed(1)}%
              </span>
            )}
          </div>
        </div>
        <motion.div
          key={currentBet}
          initial={{ scale: 1 }}
          animate={{ scale: [1, 1.1, 1] }}
          className="text-right"
        >
          <div className="text-xl font-bold text-text-primary">
            {currentBet}
          </div>
          <div className="text-xs text-text-muted">credits</div>
        </motion.div>
      </div>

      {/* Slider */}
      <Slider
        value={currentBet}
        min={minBet}
        max={maxBet}
        step={1}
        onChange={onChange}
        color={color}
        showValue={false}
        disabled={disabled}
        formatValue={(v) => `${v} credits`}
      />

      {/* Quick bet buttons */}
      {!disabled && (
        <div className="flex gap-2 mt-3">
          <QuickBetButton
            label="0"
            onClick={() => onChange(0)}
            active={currentBet === 0}
          />
          <QuickBetButton
            label="25%"
            onClick={() => onChange(Math.floor(maxBet * 0.25))}
            active={currentBet === Math.floor(maxBet * 0.25)}
          />
          <QuickBetButton
            label="50%"
            onClick={() => onChange(Math.floor(maxBet * 0.5))}
            active={currentBet === Math.floor(maxBet * 0.5)}
          />
          <QuickBetButton
            label="Max"
            onClick={() => onChange(maxBet)}
            active={currentBet === maxBet}
          />
        </div>
      )}
    </div>
  );
}

interface QuickBetButtonProps {
  label: string;
  onClick: () => void;
  active?: boolean;
}

function QuickBetButton({ label, onClick, active }: QuickBetButtonProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={cn(
        'flex-1 py-1.5 rounded-lg text-xs font-medium transition-colors',
        active
          ? 'bg-accent text-white'
          : 'bg-surface-2 text-text-secondary hover:bg-surface-3'
      )}
    >
      {label}
    </motion.button>
  );
}

// Budget bar component
export interface BudgetBarProps {
  totalBudget?: number;
  budget?: number; // Alias for totalBudget
  usedBudget?: number;
  spent?: number; // Alias for usedBudget
  className?: string;
}

export function BudgetBar({
  totalBudget: totalBudgetProp,
  budget,
  usedBudget: usedBudgetProp,
  spent,
  className
}: BudgetBarProps) {
  const totalBudget = totalBudgetProp ?? budget ?? 100;
  const usedBudget = usedBudgetProp ?? spent ?? 0;
  const remaining = totalBudget - usedBudget;
  const usedPercentage = (usedBudget / totalBudget) * 100;
  const isLow = remaining < totalBudget * 0.2;

  return (
    <div className={cn('p-4 rounded-xl bg-surface-1 border border-border', className)}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-text-secondary">Budget</span>
        <div className="flex items-center gap-2">
          <motion.span
            key={remaining}
            initial={{ scale: 1 }}
            animate={{ scale: [1, 1.1, 1] }}
            className={cn(
              'text-lg font-bold',
              isLow ? 'text-warning' : 'text-text-primary'
            )}
          >
            {remaining}
          </motion.span>
          <span className="text-text-muted">/ {totalBudget}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-3 bg-surface-2 rounded-full overflow-hidden">
        <motion.div
          className={cn(
            'h-full rounded-full',
            isLow ? 'bg-warning' : 'bg-success'
          )}
          initial={{ width: 0 }}
          animate={{ width: `${100 - usedPercentage}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      {/* Breakdown */}
      <div className="flex justify-between mt-2 text-xs">
        <span className="text-text-muted">
          Used: <span className="text-text-secondary">{usedBudget} credits</span>
        </span>
        <span className="text-text-muted">
          Available: <span className={isLow ? 'text-warning' : 'text-success'}>{remaining} credits</span>
        </span>
      </div>
    </div>
  );
}

// Bet summary component
export interface BetSummaryProps {
  bets: Record<string, number>;
  hypotheses: Hypothesis[];
  totalBudget?: number;
  budget?: number; // Alias for totalBudget
  className?: string;
}

export function BetSummary({
  bets,
  hypotheses,
  totalBudget: totalBudgetProp,
  budget,
  className
}: BetSummaryProps) {
  const totalBudget = totalBudgetProp ?? budget ?? 100;
  const totalBet = Object.values(bets).reduce((sum, bet) => sum + bet, 0);
  const activeBets = Object.entries(bets).filter(([_, amount]) => amount > 0);

  return (
    <div className={cn('p-4 rounded-xl bg-surface-1 border border-border', className)}>
      <h4 className="text-sm font-medium text-text-primary mb-3">Your Bets</h4>

      {activeBets.length === 0 ? (
        <p className="text-sm text-text-muted text-center py-4">
          No bets placed yet
        </p>
      ) : (
        <div className="space-y-2">
          {activeBets.map(([hypothesisId, amount]) => {
            const hypothesis = hypotheses.find((h) => h.id === hypothesisId);
            if (!hypothesis) return null;

            const color = getHypothesisColor(hypothesisId, hypothesis.associated_paradigms);
            const percentage = (amount / totalBudget) * 100;

            return (
              <div key={hypothesisId} className="flex items-center gap-2">
                <div
                  className="w-6 h-6 rounded flex items-center justify-center text-white text-xs font-bold"
                  style={{ backgroundColor: color }}
                >
                  {formatHypothesisId(hypothesisId)}
                </div>
                <div className="flex-1 h-2 bg-surface-2 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${percentage}%`, backgroundColor: color }}
                  />
                </div>
                <span className="text-sm font-medium text-text-primary w-16 text-right">
                  {amount} ({percentage.toFixed(0)}%)
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Total */}
      <div className="flex justify-between items-center mt-4 pt-3 border-t border-border">
        <span className="text-sm text-text-secondary">Total Bet</span>
        <Badge variant={totalBet > 0 ? 'primary' : 'default'}>
          {totalBet} / {totalBudget} credits
        </Badge>
      </div>
    </div>
  );
}
