'use client';

import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/loading';
import { cn } from '@/lib/utils';
import {
  useDiversificationScore,
  getDiversificationLevelColor,
  getDiversificationBadgeColor,
  getScoreColor,
  type DiversificationScore,
  type DiversificationLevel,
} from '@/lib/api/hooks/use-risk';
import {
  PieChart,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Target,
  Layers,
  Lightbulb,
} from 'lucide-react';

interface DiversificationCardProps {
  positions: { ticker: string; market_value: number; sector?: string }[];
  avgCorrelation?: number;
  sectorMap?: Record<string, string>;
  className?: string;
  compact?: boolean;
}

/**
 * Diversification score card component
 */
export function DiversificationCard({
  positions,
  avgCorrelation,
  sectorMap,
  className,
  compact = false,
}: DiversificationCardProps) {
  const { data: result, isLoading } = useDiversificationScore(
    positions,
    sectorMap,
    avgCorrelation,
    { enabled: positions.length > 0 }
  );

  if (positions.length === 0) {
    return (
      <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
        <CardContent className="py-8 text-center">
          <PieChart className="h-12 w-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">Add positions to see diversification score</p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return <DiversificationSkeleton compact={compact} className={className} />;
  }

  if (!result) return null;

  const score = result;

  return compact ? (
    <CompactCard score={score} className={className} />
  ) : (
    <FullCard score={score} className={className} />
  );
}

/**
 * Compact version for dashboard widgets
 */
function CompactCard({
  score,
  className,
}: {
  score: DiversificationScore;
  className?: string;
}) {
  return (
    <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
      <CardContent className="py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ScoreGauge score={score.score} size="sm" />
            <div>
              <p className="text-xs text-slate-500">Diversification</p>
              <Badge
                variant="outline"
                className={cn('text-xs', getDiversificationBadgeColor(score.level))}
              >
                {formatLevel(score.level)}
              </Badge>
            </div>
          </div>
          {score.overconcentrated_count > 0 && (
            <div className="flex items-center gap-1 text-amber-400">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-xs">{score.overconcentrated_count}</span>
            </div>
          )}
        </div>
        {score.recommendations.length > 0 && (
          <p className="text-xs text-slate-500 mt-2 line-clamp-1">
            {score.recommendations[0]}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Full version with all details
 */
function FullCard({
  score,
  className,
}: {
  score: DiversificationScore;
  className?: string;
}) {
  return (
    <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-white flex items-center justify-between">
          <span className="flex items-center gap-2">
            <PieChart className="h-4 w-4 text-purple-400" />
            Diversification Score
          </span>
          <Badge
            variant="outline"
            className={cn('text-xs', getDiversificationBadgeColor(score.level))}
          >
            {formatLevel(score.level)}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Main Score */}
        <div className="flex items-center gap-6">
          <ScoreGauge score={score.score} size="lg" />
          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Positions</span>
              <span className="text-white">{score.position_count}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Effective Positions</span>
              <span className="text-white">{score.effective_positions.toFixed(1)}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Sectors</span>
              <span className="text-white">{score.sector_count}/11</span>
            </div>
          </div>
        </div>

        {/* Breakdown */}
        <ScoreBreakdown breakdown={score.breakdown} />

        {/* Largest Position */}
        {score.largest_position && (
          <div className="p-3 rounded-lg bg-slate-900/50">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-500">Largest Position</span>
              {score.largest_position.is_overconcentrated && (
                <AlertTriangle className="h-3 w-3 text-amber-400" />
              )}
            </div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-white font-medium">{score.largest_position.ticker}</span>
              <span
                className={cn(
                  'font-mono',
                  score.largest_position.is_overconcentrated
                    ? 'text-amber-400'
                    : 'text-slate-300'
                )}
              >
                {score.largest_position.weight.toFixed(1)}%
              </span>
            </div>
          </div>
        )}

        {/* Recommendations */}
        {score.recommendations.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-slate-500 flex items-center gap-1">
              <Lightbulb className="h-3 w-3" />
              Recommendations
            </p>
            <ul className="space-y-1">
              {score.recommendations.slice(0, 3).map((rec, i) => (
                <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                  <span className="text-purple-400 mt-0.5">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Score gauge visualization
 */
function ScoreGauge({
  score,
  size = 'md',
}: {
  score: number;
  size?: 'sm' | 'md' | 'lg';
}) {
  const sizeClasses = {
    sm: 'w-12 h-12',
    md: 'w-16 h-16',
    lg: 'w-20 h-20',
  };

  const textClasses = {
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-2xl',
  };

  const strokeWidth = size === 'lg' ? 4 : 3;
  const radius = size === 'lg' ? 36 : size === 'md' ? 28 : 20;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;

  return (
    <div className={cn('relative', sizeClasses[size])}>
      <svg className="w-full h-full transform -rotate-90" viewBox={`0 0 ${(radius + strokeWidth) * 2} ${(radius + strokeWidth) * 2}`}>
        {/* Background circle */}
        <circle
          cx={radius + strokeWidth}
          cy={radius + strokeWidth}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-slate-700"
        />
        {/* Progress circle */}
        <circle
          cx={radius + strokeWidth}
          cy={radius + strokeWidth}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          className={getScoreColor(score)}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className={cn('font-bold font-mono', textClasses[size], getScoreColor(score))}>
          {Math.round(score)}
        </span>
      </div>
    </div>
  );
}

/**
 * Score breakdown bars
 */
function ScoreBreakdown({
  breakdown,
}: {
  breakdown: DiversificationScore['breakdown'];
}) {
  const components = [
    { key: 'position', label: 'Position Balance', score: breakdown.position_score, icon: Layers },
    { key: 'sector', label: 'Sector Spread', score: breakdown.sector_score, icon: PieChart },
    { key: 'correlation', label: 'Correlation', score: breakdown.correlation_score, icon: TrendingUp },
    { key: 'concentration', label: 'Concentration', score: breakdown.concentration_score, icon: Target },
  ];

  return (
    <div className="space-y-2">
      <p className="text-xs text-slate-500">Score Components</p>
      {components.map(({ key, label, score, icon: Icon }) => (
        <div key={key} className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Icon className="h-3 w-3" />
              {label}
            </span>
            <span className={cn('text-xs font-mono', getScoreColor(score))}>
              {Math.round(score)}
            </span>
          </div>
          <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full transition-all',
                score >= 80 ? 'bg-emerald-500' :
                score >= 60 ? 'bg-green-500' :
                score >= 40 ? 'bg-yellow-500' :
                score >= 20 ? 'bg-orange-500' : 'bg-red-500'
              )}
              style={{ width: `${score}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Loading skeleton
 */
function DiversificationSkeleton({
  compact,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  if (compact) {
    return (
      <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
        <CardContent className="py-4">
          <div className="flex items-center gap-3">
            <Skeleton className="w-12 h-12 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-5 w-16" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-40" />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-6">
          <Skeleton className="w-20 h-20 rounded-full" />
          <div className="flex-1 space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        </div>
        <div className="space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-4 w-full" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Format level for display
 */
function formatLevel(level: DiversificationLevel): string {
  return level.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

/**
 * Mini diversification indicator for other components
 */
export function MiniDiversificationScore({
  score,
  level,
  className,
}: {
  score: number;
  level: DiversificationLevel;
  className?: string;
}) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className={cn('text-lg font-bold font-mono', getScoreColor(score))}>
        {Math.round(score)}
      </div>
      <div className="flex flex-col">
        <span className="text-[10px] text-slate-500">Diversification</span>
        <span className={cn('text-xs', getDiversificationLevelColor(level))}>
          {formatLevel(level)}
        </span>
      </div>
    </div>
  );
}

