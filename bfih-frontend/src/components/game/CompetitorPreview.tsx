import { motion } from 'framer-motion';
import { cn } from '../../utils';
import { Card } from '../ui/Card';
import type { Paradigm } from '../../types';
import { getPersonaForParadigm } from '../../types';

interface CompetitorPreviewProps {
  paradigms: Paradigm[];
  excludeParadigmId?: string | null; // Player's home paradigm to exclude
  className?: string;
}

export function CompetitorPreview({
  paradigms,
  excludeParadigmId,
  className,
}: CompetitorPreviewProps) {
  // Filter out the player's home paradigm if specified
  const opponents = paradigms.filter((p) => p.id !== excludeParadigmId);

  return (
    <Card className={cn('p-4', className)}>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-2xl">VS</span>
        <div>
          <h3 className="font-semibold text-text-primary">Your Opponents</h3>
          <p className="text-xs text-text-muted">
            {opponents.length} AI paradigm personas
          </p>
        </div>
      </div>

      <div className="space-y-2">
        {opponents.map((paradigm, index) => {
          const persona = getPersonaForParadigm(paradigm.id, paradigm.name);

          return (
            <motion.div
              key={paradigm.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center gap-3 p-2 rounded-lg bg-surface-2/50"
            >
              <span className="text-xl">{persona.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-text-primary text-sm truncate">
                  {persona.name}
                </div>
                <div className="text-xs text-text-muted truncate">
                  {persona.description}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="mt-4 pt-3 border-t border-border">
        <p className="text-xs text-text-secondary text-center">
          Each persona bets according to their paradigm's prior beliefs
        </p>
      </div>
    </Card>
  );
}

// Compact version for smaller spaces
interface CompetitorAvatarsProps {
  paradigms: Paradigm[];
  excludeParadigmId?: string | null;
  className?: string;
}

export function CompetitorAvatars({
  paradigms,
  excludeParadigmId,
  className,
}: CompetitorAvatarsProps) {
  const opponents = paradigms.filter((p) => p.id !== excludeParadigmId);

  return (
    <div className={cn('flex items-center', className)}>
      <span className="text-2xl mr-2">🎮</span>
      <span className="text-sm text-text-muted mx-2">vs</span>
      <div className="flex -space-x-2">
        {opponents.slice(0, 5).map((paradigm, index) => {
          const persona = getPersonaForParadigm(paradigm.id, paradigm.name);
          return (
            <motion.div
              key={paradigm.id}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: index * 0.1, type: 'spring' }}
              className="w-8 h-8 rounded-full bg-surface-2 border-2 border-surface-1 flex items-center justify-center text-sm"
              title={persona.name}
            >
              {persona.icon}
            </motion.div>
          );
        })}
        {opponents.length > 5 && (
          <div className="w-8 h-8 rounded-full bg-surface-3 border-2 border-surface-1 flex items-center justify-center text-xs text-text-muted">
            +{opponents.length - 5}
          </div>
        )}
      </div>
    </div>
  );
}
