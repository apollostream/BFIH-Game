import { type HTMLAttributes, type ReactNode } from 'react';
import { cn } from '../../utils';

export type BadgeVariant = 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'info' | 'paradigm' | 'domain';
type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: BadgeSize;
  color?: string; // Custom color override
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-surface-3 text-text-secondary',
  primary: 'bg-accent/20 text-accent',
  secondary: 'bg-surface-2 text-text-secondary border border-border',
  success: 'bg-success/20 text-success',
  warning: 'bg-warning/20 text-warning',
  danger: 'bg-error/20 text-error',
  info: 'bg-info/20 text-info',
  paradigm: 'bg-paradigm-k1/20 text-paradigm-k1',
  domain: 'bg-surface-3 text-text-primary',
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'px-1.5 py-0.5 text-xs gap-1',
  md: 'px-2 py-1 text-sm gap-1.5',
  lg: 'px-3 py-1.5 text-base gap-2',
};

export function Badge({
  variant = 'default',
  size = 'md',
  color,
  leftIcon,
  rightIcon,
  dot = false,
  className,
  children,
  style,
  ...props
}: BadgeProps) {
  const customStyles = color
    ? {
        backgroundColor: `${color}20`,
        color: color,
        ...style,
      }
    : style;

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center',
        'font-medium rounded-full',
        'whitespace-nowrap',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      style={customStyles}
      {...props}
    >
      {dot && (
        <span
          className="w-1.5 h-1.5 rounded-full bg-current"
          style={color ? { backgroundColor: color } : undefined}
        />
      )}
      {leftIcon}
      {children}
      {rightIcon}
    </span>
  );
}

// Specialized badge variants
interface ParadigmBadgeProps extends Omit<BadgeProps, 'variant'> {
  paradigmId: string;
}

const paradigmColors: Record<string, string> = {
  K1: '#8B5CF6',
  K2: '#10B981',
  K3: '#F59E0B',
  K4: '#EF4444',
};

export function ParadigmBadge({ paradigmId, ...props }: ParadigmBadgeProps) {
  return (
    <Badge
      color={paradigmColors[paradigmId] || '#6B7280'}
      {...props}
    />
  );
}

interface DomainBadgeProps extends Omit<BadgeProps, 'variant'> {
  domain: string;
}

const domainColors: Record<string, string> = {
  Economic: '#22C55E',
  Cultural: '#EC4899',
  Psychological: '#A855F7',
  Institutional: '#3B82F6',
  Historical: '#EAB308',
  Theological: '#8B5CF6',
  Biological: '#14B8A6',
  Technological: '#F97316',
};

export function DomainBadge({ domain, children, ...props }: DomainBadgeProps) {
  return (
    <Badge
      color={domainColors[domain] || '#6B7280'}
      {...props}
    >
      {children || domain}
    </Badge>
  );
}

// Evidence type badge
interface EvidenceTypeBadgeProps extends Omit<BadgeProps, 'variant'> {
  evidenceType: string;
}

const evidenceTypeIcons: Record<string, string> = {
  quantitative: '📊',
  qualitative: '📝',
  expert_testimony: '👤',
  historical_analogy: '📜',
  policy: '📋',
  institutional: '🏛️',
};

export function EvidenceTypeBadge({ evidenceType, children, ...props }: EvidenceTypeBadgeProps) {
  const icon = evidenceTypeIcons[evidenceType] || '📄';
  const label = evidenceType.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');

  return (
    <Badge variant="default" size="sm" {...props}>
      <span className="mr-1">{icon}</span>
      {children || label}
    </Badge>
  );
}
