// Formatting utilities

// Probability bounds to avoid extremes (0 or 1) which break Bayesian math
// Per Cromwell's Rule: always leave room for uncertainty
export const PROB_MIN = 0.001;
export const PROB_MAX = 0.999;

/**
 * Clamp a probability to avoid extreme values (0 or 1).
 * Extreme values break Bayesian calculations:
 * - log(0) = -infinity
 * - Division by zero in odds calculations
 * - No evidence can update a prior of 0 or 1 (violates Cromwell's Rule)
 */
export function clampProbability(p: number): number {
  if (p <= 0) return PROB_MIN;
  if (p >= 1) return PROB_MAX;
  if (p < PROB_MIN) return PROB_MIN;
  if (p > PROB_MAX) return PROB_MAX;
  return p;
}

// Format number as percentage
export function formatPercent(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

// Format probability (0-1) as display string
export function formatProbability(value: number): string {
  if (value === 0) return '0%';
  if (value === 1) return '100%';
  if (value < 0.01) return '<1%';
  if (value > 0.99) return '>99%';
  return `${(value * 100).toFixed(1)}%`;
}

// Format Weight of Evidence in decibans
export function formatWoE(woe: number): string {
  if (!isFinite(woe)) return '---';
  const sign = woe > 0 ? '+' : '';
  return `${sign}${woe.toFixed(1)} db`;
}

// Format likelihood ratio
export function formatLR(lr: number): string {
  if (!isFinite(lr) || lr <= 0) return '---';
  if (lr >= 100) return `${lr.toFixed(0)}:1`;
  if (lr >= 10) return `${lr.toFixed(1)}:1`;
  if (lr >= 1) return `${lr.toFixed(2)}:1`;
  // For LR < 1, show as 1:X
  const inverse = 1 / lr;
  if (inverse >= 10) return `1:${inverse.toFixed(1)}`;
  return `1:${inverse.toFixed(2)}`;
}

// Format currency/credits
export function formatCredits(amount: number): string {
  return `${amount.toFixed(0)} credits`;
}

// Format date
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

// Format datetime
export function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Format duration in seconds
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs.toFixed(0)}s`;
}

// Truncate text with ellipsis
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

// Format hypothesis ID for display (H1 -> H₁)
export function formatHypothesisId(id: string): string {
  return id.replace(/(\d+)/g, (match) => {
    const subscripts = '₀₁₂₃₄₅₆₇₈₉';
    return match.split('').map(d => subscripts[parseInt(d)]).join('');
  });
}

// Format paradigm ID for display (K1 -> K₁)
export function formatParadigmId(id: string): string {
  return id.replace(/(\d+)/g, (match) => {
    const subscripts = '₀₁₂₃₄₅₆₇₈₉';
    return match.split('').map(d => subscripts[parseInt(d)]).join('');
  });
}

// Get ordinal suffix (1st, 2nd, 3rd, etc.)
export function getOrdinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

// Format evidence type for display
export function formatEvidenceType(type: string): string {
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Calculate payoff based on function type
// For 'odds_against': Horse race style where odds are set by priors
//   Payoff = bet * (1 + odds-against) = bet / prior  (if correct)
//   Low prior = high payout (longshot), High prior = low payout (favorite)
export function calculatePayoff(
  bet: number,
  posterior: number,
  isCorrect: boolean,
  payoffFunction: 'odds_against' | 'proportional_posterior' | 'log_score' | 'quadratic_score',
  prior?: number
): number {
  switch (payoffFunction) {
    case 'odds_against':
      // Horse race style: net profit = (bet / prior) - bet if correct, -bet if wrong
      // Odds-against = (1 - prior) / prior, so 1 + odds-against = 1/prior
      // Example: prior=0.2, bet=10 → total return=50, net profit=+40
      // If wrong: you lose your bet entirely (-bet)
      if (!prior || prior <= 0) return isCorrect ? 0 : -bet;
      return isCorrect ? (bet / prior) - bet : -bet;
    case 'proportional_posterior':
      return isCorrect ? bet * (1 + posterior) : 0;
    case 'log_score':
      return isCorrect ? bet * (1 + Math.log2(posterior + 0.01)) : 0;
    case 'quadratic_score':
      const score = isCorrect ? 2 * posterior - posterior ** 2 : -(posterior ** 2);
      return bet * (1 + score);
    default:
      return isCorrect ? bet : 0;
  }
}
