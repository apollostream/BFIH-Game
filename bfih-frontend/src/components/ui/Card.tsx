import { forwardRef, type HTMLAttributes, type ReactNode } from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';
import { cn } from '../../utils';
import { cardVariants } from '../../utils/animations';

type CardVariant = 'default' | 'elevated' | 'glass' | 'bordered' | 'paradigm';

interface CardProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
  variant?: CardVariant;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  animate?: boolean;
  children?: ReactNode;
}

const variantStyles: Record<CardVariant, string> = {
  default: 'bg-surface-1 border border-border',
  elevated: 'bg-surface-1/95 border border-border shadow-elevated backdrop-blur-sm',
  glass: 'glass',
  bordered: 'bg-transparent border-2 border-border',
  paradigm: 'bg-gradient-to-br from-surface-1 to-surface-2 border border-border shadow-md',
};

const paddingStyles: Record<string, string> = {
  none: 'p-0',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'default',
      padding = 'md',
      hoverable = false,
      animate = true,
      className,
      children,
      ...props
    },
    ref
  ) => {
    const MotionComponent = animate ? motion.div : 'div';

    return (
      <MotionComponent
        ref={ref}
        variants={animate ? cardVariants : undefined}
        initial={animate ? 'initial' : undefined}
        animate={animate ? 'animate' : undefined}
        whileHover={hoverable ? { y: -4, boxShadow: 'var(--shadow-lg)' } : undefined}
        className={cn(
          'rounded-2xl',
          'transition-all duration-300',
          variantStyles[variant],
          paddingStyles[padding],
          hoverable && 'cursor-pointer',
          className
        )}
        {...(props as any)}
      >
        {children}
      </MotionComponent>
    );
  }
);

Card.displayName = 'Card';

// Card subcomponents
interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
}

export function CardHeader({
  title,
  subtitle,
  action,
  className,
  children,
  ...props
}: CardHeaderProps) {
  return (
    <div
      className={cn('flex items-start justify-between gap-4 mb-6', className)}
      {...props}
    >
      <div>
        {title && (
          <h3 className="text-xl font-semibold text-text-primary">{title}</h3>
        )}
        {subtitle && (
          <p className="text-sm text-text-secondary mt-1">{subtitle}</p>
        )}
        {children}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  );
}

export function CardContent({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('', className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'flex items-center justify-end gap-4 mt-6 pt-6 border-t border-border',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
