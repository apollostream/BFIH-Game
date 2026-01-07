import { cn } from '../../utils';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animate?: boolean;
}

export function Skeleton({
  className,
  variant = 'text',
  width,
  height,
  animate = true,
}: SkeletonProps) {
  const variantStyles: Record<string, string> = {
    text: 'h-4 rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  return (
    <div
      className={cn(
        'bg-surface-2',
        animate && 'animate-pulse',
        variantStyles[variant],
        className
      )}
      style={{
        width: width ?? (variant === 'text' ? '100%' : undefined),
        height: height ?? (variant === 'circular' ? width : undefined),
      }}
    />
  );
}

// Preset skeleton components
export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          width={i === lines - 1 ? '60%' : '100%'}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('p-4 rounded-xl bg-surface-1 border border-border', className)}>
      <div className="flex items-center gap-3 mb-4">
        <Skeleton variant="circular" width={40} height={40} />
        <div className="flex-1">
          <Skeleton variant="text" width="50%" className="mb-2" />
          <Skeleton variant="text" width="30%" height={12} />
        </div>
      </div>
      <SkeletonText lines={3} />
    </div>
  );
}

export function SkeletonHypothesisCard({ className }: { className?: string }) {
  return (
    <div className={cn('p-4 rounded-xl bg-surface-1 border border-border', className)}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <Skeleton variant="text" width="40%" height={20} className="mb-2" />
          <div className="flex gap-2">
            <Skeleton variant="rectangular" width={60} height={20} />
            <Skeleton variant="rectangular" width={80} height={20} />
          </div>
        </div>
        <Skeleton variant="rectangular" width={50} height={24} />
      </div>
      <SkeletonText lines={2} />
    </div>
  );
}

export function SkeletonEvidenceCard({ className }: { className?: string }) {
  return (
    <div className={cn('p-4 rounded-xl bg-surface-1 border border-border', className)}>
      <div className="flex items-start gap-3 mb-3">
        <Skeleton variant="rectangular" width={32} height={32} />
        <div className="flex-1">
          <Skeleton variant="text" width="70%" className="mb-2" />
          <Skeleton variant="text" width="40%" height={12} />
        </div>
      </div>
      <SkeletonText lines={2} />
      <div className="flex gap-2 mt-3">
        <Skeleton variant="rectangular" width={80} height={24} />
        <Skeleton variant="rectangular" width={100} height={24} />
      </div>
    </div>
  );
}

export function SkeletonChart({ className }: { className?: string }) {
  return (
    <div className={cn('p-4 rounded-xl bg-surface-1 border border-border', className)}>
      <Skeleton variant="text" width="30%" height={20} className="mb-4" />
      <div className="flex items-end gap-2 h-40">
        {[40, 70, 55, 85, 45, 60].map((h, i) => (
          <Skeleton
            key={i}
            variant="rectangular"
            className="flex-1"
            height={`${h}%`}
          />
        ))}
      </div>
    </div>
  );
}

export function SkeletonReport({ className }: { className?: string }) {
  return (
    <div className={cn('space-y-6', className)}>
      {/* Title */}
      <Skeleton variant="text" width="60%" height={32} />

      {/* Meta info */}
      <div className="flex gap-4">
        <Skeleton variant="rectangular" width={100} height={24} />
        <Skeleton variant="rectangular" width={120} height={24} />
        <Skeleton variant="rectangular" width={80} height={24} />
      </div>

      {/* Section 1 */}
      <div>
        <Skeleton variant="text" width="40%" height={24} className="mb-3" />
        <SkeletonText lines={4} />
      </div>

      {/* Section 2 */}
      <div>
        <Skeleton variant="text" width="35%" height={24} className="mb-3" />
        <SkeletonText lines={3} />
      </div>

      {/* Table */}
      <div className="border border-border rounded-lg overflow-hidden">
        <div className="bg-surface-2 p-3 flex gap-4">
          <Skeleton variant="text" width={100} />
          <Skeleton variant="text" width={80} />
          <Skeleton variant="text" width={120} />
        </div>
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-3 flex gap-4 border-t border-border">
            <Skeleton variant="text" width={100} />
            <Skeleton variant="text" width={80} />
            <Skeleton variant="text" width={120} />
          </div>
        ))}
      </div>
    </div>
  );
}
