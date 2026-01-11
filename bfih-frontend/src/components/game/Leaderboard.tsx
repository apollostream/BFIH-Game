import { motion } from 'framer-motion';
import { cn } from '../../utils';
import type { LeaderboardEntry } from '../../types';

interface LeaderboardProps {
  entries: LeaderboardEntry[];
  className?: string;
}

const RANK_STYLES: Record<number, { medal: string; bgClass: string; textClass: string }> = {
  1: { medal: '🥇', bgClass: 'bg-gradient-to-r from-yellow-500/20 to-amber-500/20', textClass: 'text-yellow-400' },
  2: { medal: '🥈', bgClass: 'bg-gradient-to-r from-gray-400/20 to-slate-400/20', textClass: 'text-gray-300' },
  3: { medal: '🥉', bgClass: 'bg-gradient-to-r from-orange-600/20 to-amber-700/20', textClass: 'text-orange-400' },
};

export function Leaderboard({ entries, className }: LeaderboardProps) {
  return (
    <div className={cn('space-y-2', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 text-sm text-text-muted">
        <span className="w-12">Rank</span>
        <span className="flex-1">Competitor</span>
        <span className="w-24 text-right">Score</span>
      </div>

      {/* Entries */}
      {entries.map((entry, index) => {
        const rankStyle = RANK_STYLES[entry.rank] || { medal: '', bgClass: '', textClass: 'text-text-secondary' };
        const isPositive = entry.payoff >= 0;

        return (
          <motion.div
            key={entry.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1, duration: 0.3 }}
            className={cn(
              'flex items-center gap-3 px-4 py-3 rounded-xl',
              'border transition-all duration-300',
              entry.isPlayer
                ? 'border-accent bg-accent/10 ring-2 ring-accent/30'
                : 'border-border bg-surface-2/50',
              rankStyle.bgClass
            )}
          >
            {/* Rank */}
            <div className={cn('w-12 text-center font-bold text-xl', rankStyle.textClass)}>
              {rankStyle.medal || `#${entry.rank}`}
            </div>

            {/* Icon & Name */}
            <div className="flex-1 flex items-center gap-3">
              <span className="text-2xl">{entry.icon}</span>
              <div>
                <div className={cn(
                  'font-semibold',
                  entry.isPlayer ? 'text-accent' : 'text-text-primary'
                )}>
                  {entry.name}
                  {entry.isPlayer && (
                    <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-accent/20 text-accent">
                      YOU
                    </span>
                  )}
                </div>
                <div className="text-xs text-text-muted">{entry.description}</div>
              </div>
            </div>

            {/* Score */}
            <motion.div
              initial={{ scale: 0.5 }}
              animate={{ scale: 1 }}
              transition={{ delay: index * 0.1 + 0.2, type: 'spring', stiffness: 200 }}
              className={cn(
                'w-24 text-right font-bold text-lg',
                isPositive ? 'text-success' : 'text-error'
              )}
            >
              {isPositive ? '+' : ''}{entry.payoff.toFixed(0)}
              <span className="text-xs text-text-muted ml-1">cr</span>
            </motion.div>
          </motion.div>
        );
      })}
    </div>
  );
}

// Compact version for sidebar or preview
interface LeaderboardCompactProps {
  entries: LeaderboardEntry[];
  maxDisplay?: number;
  className?: string;
}

export function LeaderboardCompact({ entries, maxDisplay = 5, className }: LeaderboardCompactProps) {
  const displayEntries = entries.slice(0, maxDisplay);

  return (
    <div className={cn('space-y-1', className)}>
      {displayEntries.map((entry) => {
        const isPositive = entry.payoff >= 0;
        return (
          <div
            key={entry.id}
            className={cn(
              'flex items-center gap-2 px-2 py-1.5 rounded-lg text-sm',
              entry.isPlayer ? 'bg-accent/10 border border-accent/30' : 'bg-surface-2/50'
            )}
          >
            <span className="w-6 text-center">
              {entry.rank <= 3 ? RANK_STYLES[entry.rank]?.medal : `#${entry.rank}`}
            </span>
            <span>{entry.icon}</span>
            <span className={cn('flex-1 truncate', entry.isPlayer && 'font-semibold text-accent')}>
              {entry.isPlayer ? 'You' : entry.name}
            </span>
            <span className={cn('font-medium', isPositive ? 'text-success' : 'text-error')}>
              {isPositive ? '+' : ''}{entry.payoff.toFixed(0)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// Victory message based on player rank
interface VictoryMessageProps {
  playerRank: number;
  totalCompetitors: number;
  winnerName?: string;
}

export function VictoryMessage({ playerRank, totalCompetitors, winnerName }: VictoryMessageProps) {
  let message: string;
  let subMessage: string;
  let bgClass: string;

  if (playerRank === 1) {
    message = "CHAMPION!";
    subMessage = "You outpredicted all paradigm personas!";
    bgClass = "bg-gradient-to-r from-yellow-500/20 via-amber-500/20 to-yellow-500/20";
  } else if (playerRank === 2) {
    message = "Great Job!";
    subMessage = `You finished 2nd out of ${totalCompetitors} competitors`;
    bgClass = "bg-gradient-to-r from-gray-400/20 to-slate-400/20";
  } else if (playerRank === 3) {
    message = "Nice Work!";
    subMessage = `You made the podium! 3rd out of ${totalCompetitors}`;
    bgClass = "bg-gradient-to-r from-orange-600/20 to-amber-700/20";
  } else if (playerRank <= Math.ceil(totalCompetitors / 2)) {
    message = "Not Bad!";
    subMessage = `You beat ${totalCompetitors - playerRank} paradigm${totalCompetitors - playerRank !== 1 ? 's' : ''}`;
    bgClass = "bg-surface-2";
  } else {
    message = "Keep Learning!";
    subMessage = winnerName
      ? `${winnerName} had better predictions this time`
      : "Study the paradigms to improve your strategy";
    bgClass = "bg-surface-2";
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, type: 'spring' }}
      className={cn(
        'text-center p-6 rounded-2xl border border-border',
        bgClass
      )}
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
        className="text-4xl mb-2"
      >
        {playerRank === 1 ? '🏆' : playerRank === 2 ? '🥈' : playerRank === 3 ? '🥉' : '🎮'}
      </motion.div>
      <h2 className={cn(
        'text-3xl font-bold mb-2',
        playerRank === 1 ? 'text-yellow-400' : 'text-text-primary'
      )}>
        {message}
      </h2>
      <p className="text-text-secondary">{subMessage}</p>
    </motion.div>
  );
}
