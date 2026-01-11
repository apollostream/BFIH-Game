import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils';

interface ConfettiPiece {
  id: number;
  x: number;
  delay: number;
  duration: number;
  color: string;
  size: number;
  rotation: number;
}

const CONFETTI_COLORS = [
  '#FFD700', // Gold
  '#FF6B6B', // Coral
  '#4ECDC4', // Teal
  '#A855F7', // Purple
  '#3B82F6', // Blue
  '#22C55E', // Green
  '#F59E0B', // Amber
  '#EC4899', // Pink
];

function Confetti({ show }: { show: boolean }) {
  const [pieces, setPieces] = useState<ConfettiPiece[]>([]);

  useEffect(() => {
    if (show) {
      const newPieces: ConfettiPiece[] = [];
      for (let i = 0; i < 50; i++) {
        newPieces.push({
          id: i,
          x: Math.random() * 100,
          delay: Math.random() * 0.5,
          duration: 2 + Math.random() * 2,
          color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
          size: 8 + Math.random() * 8,
          rotation: Math.random() * 360,
        });
      }
      setPieces(newPieces);
    }
  }, [show]);

  if (!show) return null;

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-50">
      {pieces.map((piece) => (
        <motion.div
          key={piece.id}
          initial={{
            x: `${piece.x}vw`,
            y: '-10vh',
            rotate: piece.rotation,
            opacity: 1,
          }}
          animate={{
            y: '110vh',
            rotate: piece.rotation + 720,
            opacity: [1, 1, 0],
          }}
          transition={{
            duration: piece.duration,
            delay: piece.delay,
            ease: 'linear',
          }}
          style={{
            position: 'absolute',
            width: piece.size,
            height: piece.size,
            backgroundColor: piece.color,
            borderRadius: Math.random() > 0.5 ? '50%' : '2px',
          }}
        />
      ))}
    </div>
  );
}

interface VictoryOverlayProps {
  show: boolean;
  playerRank: number;
  totalCompetitors: number;
  playerPayoff: number;
  winnerName?: string;
  onClose?: () => void;
  className?: string;
}

export function VictoryOverlay({
  show,
  playerRank,
  totalCompetitors,
  playerPayoff,
  winnerName,
  onClose,
  className,
}: VictoryOverlayProps) {
  const isWinner = playerRank === 1;
  const isPodium = playerRank <= 3;

  let title: string;
  let subtitle: string;
  let emoji: string;
  let bgGradient: string;

  if (playerRank === 1) {
    title = 'CHAMPION!';
    subtitle = 'You outpredicted all paradigm personas!';
    emoji = '🏆';
    bgGradient = 'from-yellow-500/30 via-amber-500/20 to-yellow-500/30';
  } else if (playerRank === 2) {
    title = 'Great Job!';
    subtitle = `You finished 2nd out of ${totalCompetitors} competitors`;
    emoji = '🥈';
    bgGradient = 'from-gray-400/30 to-slate-400/20';
  } else if (playerRank === 3) {
    title = 'Nice Work!';
    subtitle = `You made the podium! 3rd out of ${totalCompetitors}`;
    emoji = '🥉';
    bgGradient = 'from-orange-600/30 to-amber-700/20';
  } else if (playerRank <= Math.ceil(totalCompetitors / 2)) {
    title = 'Not Bad!';
    subtitle = `You beat ${totalCompetitors - playerRank} paradigm${totalCompetitors - playerRank !== 1 ? 's' : ''}`;
    emoji = '💪';
    bgGradient = 'from-blue-500/20 to-indigo-500/20';
  } else {
    title = 'Keep Learning!';
    subtitle = winnerName
      ? `${winnerName} had better predictions this time`
      : 'Study the paradigms to improve your strategy';
    emoji = '📚';
    bgGradient = 'from-surface-2 to-surface-3';
  }

  return (
    <AnimatePresence>
      {show && (
        <>
          {/* Confetti for winners */}
          {isWinner && <Confetti show={show} />}

          {/* Overlay backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Victory card */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 50 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 50 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            className={cn(
              'fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50',
              'w-full max-w-md mx-4',
              className
            )}
          >
            <div
              className={cn(
                'p-8 rounded-2xl border border-border',
                'bg-gradient-to-br',
                bgGradient,
                'backdrop-blur-xl shadow-2xl',
                'text-center'
              )}
            >
              {/* Emoji */}
              <motion.div
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{
                  type: 'spring',
                  stiffness: 200,
                  delay: 0.2,
                }}
                className="text-7xl mb-4"
              >
                {emoji}
              </motion.div>

              {/* Title */}
              <motion.h1
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className={cn(
                  'text-4xl font-bold mb-2',
                  isWinner ? 'text-yellow-400' : isPodium ? 'text-accent' : 'text-text-primary'
                )}
              >
                {title}
              </motion.h1>

              {/* Subtitle */}
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="text-text-secondary mb-6"
              >
                {subtitle}
              </motion.p>

              {/* Payoff */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.5, type: 'spring' }}
                className={cn(
                  'inline-flex items-center gap-2 px-6 py-3 rounded-full',
                  'text-2xl font-bold',
                  playerPayoff >= 0
                    ? 'bg-success/20 text-success'
                    : 'bg-error/20 text-error'
                )}
              >
                {playerPayoff >= 0 ? '+' : ''}
                {playerPayoff.toFixed(0)}
                <span className="text-sm font-normal opacity-80">credits</span>
              </motion.div>

              {/* Rank badge */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6 }}
                className="mt-6 text-text-muted"
              >
                Rank: #{playerRank} of {totalCompetitors}
              </motion.div>

              {/* Close button */}
              {onClose && (
                <motion.button
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.7 }}
                  onClick={onClose}
                  className={cn(
                    'mt-6 px-8 py-3 rounded-xl',
                    'bg-accent hover:bg-accent-hover',
                    'text-white font-semibold',
                    'transition-colors'
                  )}
                >
                  View Leaderboard
                </motion.button>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
