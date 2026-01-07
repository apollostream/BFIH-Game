import { type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils';
import { pageVariants } from '../../utils/animations';

interface PageContainerProps {
  children: ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  padding?: boolean;
  animate?: boolean;
}

const maxWidthStyles: Record<string, string> = {
  sm: 'max-w-screen-sm',
  md: 'max-w-screen-md',
  lg: 'max-w-screen-lg',
  xl: 'max-w-screen-xl',
  '2xl': 'max-w-screen-2xl',
  full: 'max-w-full',
};

export function PageContainer({
  children,
  className,
  maxWidth = 'xl',
  padding = true,
  animate = true,
}: PageContainerProps) {
  const Container = animate ? motion.main : 'main';
  const animationProps = animate
    ? {
        variants: pageVariants,
        initial: 'initial',
        animate: 'animate',
        exit: 'exit',
      }
    : {};

  return (
    <Container
      className={cn(
        'flex-1 w-full mx-auto',
        maxWidthStyles[maxWidth],
        padding && 'px-4 py-6 sm:px-6 lg:px-8',
        className
      )}
      {...(animationProps as any)}
    >
      {children}
    </Container>
  );
}

// Page header component
interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  breadcrumbs?: Array<{ label: string; href?: string }>;
  className?: string;
}

export function PageHeader({
  title,
  subtitle,
  action,
  breadcrumbs,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn('mb-6', className)}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center gap-2 text-sm text-text-muted mb-2">
          {breadcrumbs.map((crumb, i) => (
            <span key={i} className="flex items-center gap-2">
              {i > 0 && <ChevronRight className="w-4 h-4" />}
              {crumb.href ? (
                <a
                  href={crumb.href}
                  className="hover:text-text-secondary transition-colors"
                >
                  {crumb.label}
                </a>
              ) : (
                <span className="text-text-secondary">{crumb.label}</span>
              )}
            </span>
          ))}
        </nav>
      )}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary">
            {title}
          </h1>
          {subtitle && (
            <p className="text-text-secondary mt-1">{subtitle}</p>
          )}
        </div>
        {action && <div className="flex-shrink-0">{action}</div>}
      </div>
    </div>
  );
}

function ChevronRight({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 5l7 7-7 7"
      />
    </svg>
  );
}

// Two-column layout for game pages
interface GameLayoutProps {
  main: ReactNode;
  sidebar: ReactNode;
  sidebarPosition?: 'left' | 'right';
  className?: string;
}

export function GameLayout({
  main,
  sidebar,
  sidebarPosition = 'right',
  className,
}: GameLayoutProps) {
  return (
    <div
      className={cn(
        'grid gap-6',
        'lg:grid-cols-[1fr_320px]',
        sidebarPosition === 'left' && 'lg:grid-cols-[320px_1fr]',
        className
      )}
    >
      <div className={sidebarPosition === 'left' ? 'lg:order-2' : ''}>
        {main}
      </div>
      <aside className={sidebarPosition === 'left' ? 'lg:order-1' : ''}>
        <div className="sticky top-24 space-y-4">{sidebar}</div>
      </aside>
    </div>
  );
}

// Section component
interface SectionProps {
  title?: string;
  description?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function Section({
  title,
  description,
  children,
  action,
  className,
}: SectionProps) {
  return (
    <section className={cn('mb-8', className)}>
      {(title || action) && (
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            {title && (
              <h2 className="text-lg font-semibold text-text-primary">
                {title}
              </h2>
            )}
            {description && (
              <p className="text-sm text-text-secondary mt-0.5">
                {description}
              </p>
            )}
          </div>
          {action && <div className="flex-shrink-0">{action}</div>}
        </div>
      )}
      {children}
    </section>
  );
}
