// Framer Motion animation variants

import type { Variants, Transition } from 'framer-motion';

// Default transition settings
export const defaultTransition: Transition = {
  duration: 0.3,
  ease: [0.4, 0, 0.2, 1], // ease-out
};

export const springTransition: Transition = {
  type: 'spring',
  stiffness: 300,
  damping: 30,
};

// Page transitions
export const pageVariants: Variants = {
  initial: {
    opacity: 0,
    x: 20
  },
  animate: {
    opacity: 1,
    x: 0,
    transition: defaultTransition
  },
  exit: {
    opacity: 0,
    x: -20,
    transition: { duration: 0.2 }
  },
};

// Card reveal animation
export const cardVariants: Variants = {
  initial: {
    opacity: 0,
    y: 20,
    scale: 0.95
  },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.4,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: { duration: 0.2 }
  },
  hover: {
    y: -4,
    transition: { duration: 0.2 }
  },
};

// Stagger container for lists
export const staggerContainerVariants: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    }
  },
  exit: {
    transition: {
      staggerChildren: 0.05,
      staggerDirection: -1,
    }
  }
};

// Child items for stagger
export const staggerItemVariants: Variants = {
  initial: {
    opacity: 0,
    y: 20
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: defaultTransition
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: { duration: 0.15 }
  }
};

// Fade in/out
export const fadeVariants: Variants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: { duration: 0.3 }
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.2 }
  }
};

// Scale pulse for updates
export const pulseVariants: Variants = {
  initial: { scale: 1 },
  pulse: {
    scale: [1, 1.05, 1],
    transition: { duration: 0.4 }
  }
};

// Evidence reveal
export const evidenceRevealVariants: Variants = {
  initial: {
    opacity: 0,
    height: 0,
    marginBottom: 0
  },
  animate: {
    opacity: 1,
    height: 'auto',
    marginBottom: 16,
    transition: {
      height: { duration: 0.4 },
      opacity: { duration: 0.3, delay: 0.1 }
    }
  },
  exit: {
    opacity: 0,
    height: 0,
    marginBottom: 0,
    transition: { duration: 0.3 }
  }
};

// Posterior update animation
export const posteriorUpdateVariants: Variants = {
  initial: { scale: 1, color: 'inherit' },
  update: {
    scale: [1, 1.15, 1],
    transition: { duration: 0.5 }
  }
};

// Budget bar pulse
export const budgetPulseVariants: Variants = {
  initial: { scale: 1 },
  pulse: {
    scale: [1, 1.02, 1],
    transition: { duration: 0.3, repeat: 2 }
  }
};

// Slide in from side
export const slideInVariants: Variants = {
  initial: { x: '100%', opacity: 0 },
  animate: {
    x: 0,
    opacity: 1,
    transition: springTransition
  },
  exit: {
    x: '100%',
    opacity: 0,
    transition: { duration: 0.2 }
  }
};

// Modal backdrop
export const backdropVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 }
};

// Modal content
export const modalVariants: Variants = {
  initial: {
    opacity: 0,
    scale: 0.95,
    y: 20
  },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: springTransition
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 20,
    transition: { duration: 0.2 }
  }
};

// Progress bar fill
export const progressFillVariants: Variants = {
  initial: { width: 0 },
  animate: (custom: number) => ({
    width: `${custom}%`,
    transition: { duration: 0.8, ease: 'easeOut' }
  })
};

// Tooltip
export const tooltipVariants: Variants = {
  initial: {
    opacity: 0,
    y: 5,
    scale: 0.95
  },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.15 }
  },
  exit: {
    opacity: 0,
    y: 5,
    scale: 0.95,
    transition: { duration: 0.1 }
  }
};

// Glow effect for highlights
export const glowVariants: Variants = {
  initial: {
    boxShadow: '0 0 0 0 rgba(139, 92, 246, 0)'
  },
  glow: {
    boxShadow: [
      '0 0 0 0 rgba(139, 92, 246, 0.4)',
      '0 0 20px 10px rgba(139, 92, 246, 0.2)',
      '0 0 0 0 rgba(139, 92, 246, 0)'
    ],
    transition: { duration: 1.5, repeat: Infinity }
  }
};

// Number counter animation helper
export function createCounterAnimation(from: number, to: number, duration: number = 0.5) {
  return {
    initial: { '--value': from },
    animate: {
      '--value': to,
      transition: { duration, ease: 'easeOut' }
    }
  };
}
