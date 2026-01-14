// Color utilities for paradigms, domains, and WoE scale

import type { Domain, WoELevel } from '../types';

// Paradigm colors
export const PARADIGM_COLORS: Record<string, string> = {
  K1: '#8B5CF6', // Purple - Techno-Economic
  K2: '#10B981', // Emerald - Human-Centric
  K3: '#F59E0B', // Amber - Regulatory-Safety
  K4: '#EF4444', // Red - Market-Driven
};

export const PARADIGM_COLORS_MUTED: Record<string, string> = {
  K1: '#8B5CF680',
  K2: '#10B98180',
  K3: '#F59E0B80',
  K4: '#EF444480',
};

// Domain colors
export const DOMAIN_COLORS: Record<Domain, string> = {
  Economic: '#22C55E',
  Cultural: '#EC4899',
  Psychological: '#A855F7',
  Institutional: '#3B82F6',
  Historical: '#EAB308',
  Theological: '#8B5CF6',
  Biological: '#14B8A6',
  Technological: '#F97316',
  Constitutional_Legal: '#6366F1',
  Democratic: '#0EA5E9',
};

// Weight of Evidence colors
export const WOE_COLORS: Record<WoELevel, string> = {
  strong_support: '#F97316',  // Orange
  weak_support: '#FB923C',    // Light orange
  neutral: '#6B7280',         // Gray
  weak_refute: '#60A5FA',     // Light blue
  strong_refute: '#3B82F6',   // Blue
};

// Calculate Weight of Evidence from likelihood ratio
export function calculateWoE(lr: number): number {
  if (!isFinite(lr) || lr <= 0) return 0;
  return 10 * Math.log10(lr);
}

// Get color for WoE value
export function getWoEColor(woe: number): string {
  if (woe >= 5) return WOE_COLORS.strong_support;
  if (woe > 0) return WOE_COLORS.weak_support;
  if (woe > -0.5 && woe < 0.5) return WOE_COLORS.neutral;
  if (woe > -5) return WOE_COLORS.weak_refute;
  return WOE_COLORS.strong_refute;
}

// Get interpolated color for WoE heatmap
export function getWoEHeatmapColor(woe: number): string {
  // Clamp WoE to -10 to +10 range
  const clamped = Math.max(-10, Math.min(10, woe));

  if (clamped >= 0) {
    // Neutral to orange (support)
    const t = clamped / 10;
    return interpolateColor('#6B7280', '#F97316', t);
  } else {
    // Neutral to blue (refute)
    const t = Math.abs(clamped) / 10;
    return interpolateColor('#6B7280', '#3B82F6', t);
  }
}

// Linear color interpolation
function interpolateColor(color1: string, color2: string, t: number): string {
  const r1 = parseInt(color1.slice(1, 3), 16);
  const g1 = parseInt(color1.slice(3, 5), 16);
  const b1 = parseInt(color1.slice(5, 7), 16);

  const r2 = parseInt(color2.slice(1, 3), 16);
  const g2 = parseInt(color2.slice(3, 5), 16);
  const b2 = parseInt(color2.slice(5, 7), 16);

  const r = Math.round(r1 + (r2 - r1) * t);
  const g = Math.round(g1 + (g2 - g1) * t);
  const b = Math.round(b1 + (b2 - b1) * t);

  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

// Get paradigm color with fallback
export function getParadigmColor(paradigmId: string): string {
  return PARADIGM_COLORS[paradigmId] || '#6B7280';
}

// Get domain color with fallback
export function getDomainColor(domain: Domain): string {
  return DOMAIN_COLORS[domain] || '#6B7280';
}

// Hypothesis colors (derived from associated paradigm)
export function getHypothesisColor(hypothesisId: string, associatedParadigms?: string[]): string {
  if (hypothesisId === 'H0') return '#6B7280'; // Catch-all is gray
  if (associatedParadigms && associatedParadigms.length > 0) {
    return PARADIGM_COLORS[associatedParadigms[0]] || '#6B7280';
  }
  return '#6B7280';
}

// Generate gradient string for multi-paradigm hypothesis
export function getMultiParadigmGradient(paradigmIds?: string[]): string {
  if (!paradigmIds || paradigmIds.length === 0) return PARADIGM_COLORS.K1;
  if (paradigmIds.length === 1) return PARADIGM_COLORS[paradigmIds[0]] || '#6B7280';

  const colors = paradigmIds.map(id => PARADIGM_COLORS[id] || '#6B7280');
  const stops = colors.map((color, i) => {
    const percent = (i / (colors.length - 1)) * 100;
    return `${color} ${percent}%`;
  });

  return `linear-gradient(135deg, ${stops.join(', ')})`;
}
