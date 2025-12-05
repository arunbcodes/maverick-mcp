'use client';

import { cn } from '@/lib/utils';

interface RiskMeterProps {
  score: number; // 1-10 scale
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

/**
 * Visual risk indicator showing risk level from 1-10
 */
export function RiskMeter({
  score,
  size = 'md',
  showLabel = true,
  className,
}: RiskMeterProps) {
  // Clamp score between 1 and 10
  const normalizedScore = Math.min(10, Math.max(1, Math.round(score)));
  
  const riskLevel = getRiskLevel(normalizedScore);
  const config = RISK_CONFIGS[riskLevel];

  const sizeStyles = {
    sm: {
      container: 'h-1.5',
      text: 'text-xs',
    },
    md: {
      container: 'h-2',
      text: 'text-sm',
    },
    lg: {
      container: 'h-3',
      text: 'text-base',
    },
  };

  return (
    <div className={cn('space-y-1', className)}>
      {showLabel && (
        <div className="flex justify-between items-center">
          <span className={cn('font-medium', sizeStyles[size].text, config.textColor)}>
            {config.label}
          </span>
          <span className={cn('text-slate-500', sizeStyles[size].text)}>
            {normalizedScore}/10
          </span>
        </div>
      )}
      <div className={cn('w-full bg-slate-700 rounded-full overflow-hidden', sizeStyles[size].container)}>
        <div
          className={cn('h-full rounded-full transition-all duration-300', config.barColor)}
          style={{ width: `${normalizedScore * 10}%` }}
        />
      </div>
    </div>
  );
}

type RiskLevel = 'low' | 'moderate' | 'high' | 'very_high';

interface RiskConfig {
  label: string;
  textColor: string;
  barColor: string;
  description: string;
}

const RISK_CONFIGS: Record<RiskLevel, RiskConfig> = {
  low: {
    label: 'Low Risk',
    textColor: 'text-emerald-400',
    barColor: 'bg-emerald-500',
    description: 'Stable, lower volatility',
  },
  moderate: {
    label: 'Moderate Risk',
    textColor: 'text-blue-400',
    barColor: 'bg-blue-500',
    description: 'Balanced risk profile',
  },
  high: {
    label: 'High Risk',
    textColor: 'text-amber-400',
    barColor: 'bg-amber-500',
    description: 'Higher volatility',
  },
  very_high: {
    label: 'Very High Risk',
    textColor: 'text-red-400',
    barColor: 'bg-red-500',
    description: 'Significant volatility',
  },
};

function getRiskLevel(score: number): RiskLevel {
  if (score <= 3) return 'low';
  if (score <= 5) return 'moderate';
  if (score <= 7) return 'high';
  return 'very_high';
}

/**
 * Compact inline risk badge
 */
export function RiskBadge({
  score,
  className,
}: {
  score: number;
  className?: string;
}) {
  const normalizedScore = Math.min(10, Math.max(1, Math.round(score)));
  const riskLevel = getRiskLevel(normalizedScore);
  const config = RISK_CONFIGS[riskLevel];

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium',
        config.barColor.replace('bg-', 'bg-').replace('500', '500/20'),
        config.textColor,
        className
      )}
    >
      {normalizedScore}
    </span>
  );
}

/**
 * Get risk configuration by score
 */
export function getRiskConfig(score: number): RiskConfig {
  return RISK_CONFIGS[getRiskLevel(score)];
}

