'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/loading';
import { cn } from '@/lib/utils';
import {
  useSectorExposure,
  useSectorComparison,
  useSectorRebalance,
  getSectorStatusColor,
  getSectorStatusBadge,
  getRebalanceActionColor,
  SECTOR_COLORS,
  type SectorExposureItem,
  type SectorRebalanceSuggestion,
} from '@/lib/api/hooks/use-risk';
import {
  PieChart as PieChartIcon,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';

// ============================================
// Types
// ============================================

interface SectorExposureProps {
  positions: { ticker: string; market_value: number; sector?: string }[];
  sectorMap?: Record<string, string>;
  className?: string;
}

// ============================================
// Sector Pie Chart
// ============================================

export function SectorPieChart({
  positions,
  sectorMap,
  className,
}: SectorExposureProps) {
  const { data, isLoading } = useSectorExposure(positions, sectorMap, {
    enabled: positions.length > 0,
  });

  if (positions.length === 0) {
    return (
      <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
        <CardContent className="py-8 text-center">
          <PieChartIcon className="h-12 w-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">Add positions to see sector allocation</p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return <SectorChartSkeleton className={className} />;
  }

  if (!data) return null;

  // Filter sectors with actual allocation
  const activeSectors = data.sectors.filter(s => s.weight > 0);
  
  // Calculate pie chart segments
  const total = data.total_weight;
  let currentAngle = 0;
  const segments = activeSectors.map(s => {
    const angle = (s.weight / total) * 360;
    const segment = {
      ...s,
      startAngle: currentAngle,
      endAngle: currentAngle + angle,
      color: SECTOR_COLORS[s.sector] || '#64748b',
    };
    currentAngle += angle;
    return segment;
  });

  return (
    <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
          <PieChartIcon className="h-4 w-4 text-purple-400" />
          Sector Allocation
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-start gap-6">
          {/* Pie Chart */}
          <div className="relative w-32 h-32 flex-shrink-0">
            <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
              {segments.map((seg, i) => (
                <PieSegment
                  key={seg.sector}
                  startAngle={seg.startAngle}
                  endAngle={seg.endAngle}
                  color={seg.color}
                />
              ))}
              {/* Center hole */}
              <circle cx="50" cy="50" r="25" fill="rgb(30 41 59)" />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <p className="text-lg font-bold text-white">{data.covered_sectors}</p>
                <p className="text-[10px] text-slate-500">sectors</p>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="flex-1 space-y-1.5 max-h-32 overflow-y-auto">
            {segments.map(seg => (
              <div key={seg.sector} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2.5 h-2.5 rounded-sm"
                    style={{ backgroundColor: seg.color }}
                  />
                  <span className="text-slate-300 truncate max-w-[100px]">{seg.sector}</span>
                </div>
                <span className="text-slate-400 font-mono">{seg.weight.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function PieSegment({
  startAngle,
  endAngle,
  color,
}: {
  startAngle: number;
  endAngle: number;
  color: string;
}) {
  // Calculate SVG arc path
  const radius = 45;
  const centerX = 50;
  const centerY = 50;

  const startRad = (startAngle * Math.PI) / 180;
  const endRad = (endAngle * Math.PI) / 180;

  const x1 = centerX + radius * Math.cos(startRad);
  const y1 = centerY + radius * Math.sin(startRad);
  const x2 = centerX + radius * Math.cos(endRad);
  const y2 = centerY + radius * Math.sin(endRad);

  const largeArc = endAngle - startAngle > 180 ? 1 : 0;

  const pathData = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;

  return (
    <path
      d={pathData}
      fill={color}
      className="hover:opacity-80 transition-opacity cursor-pointer"
    />
  );
}

// ============================================
// Sector Comparison Bar Chart
// ============================================

export function SectorComparisonChart({
  positions,
  sectorMap,
  className,
}: SectorExposureProps) {
  const { data, isLoading } = useSectorComparison(positions, sectorMap, {
    enabled: positions.length > 0,
  });

  if (positions.length === 0 || isLoading || !data) {
    return null;
  }

  return (
    <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-blue-400" />
          Portfolio vs S&P 500
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {data.map(sector => {
          const maxWeight = Math.max(sector.portfolio_weight, sector.benchmark_weight, 35);
          const portfolioWidth = (sector.portfolio_weight / maxWeight) * 100;
          const benchmarkWidth = (sector.benchmark_weight / maxWeight) * 100;
          const deviation = sector.portfolio_weight - sector.benchmark_weight;
          
          return (
            <div key={sector.sector} className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400 truncate max-w-[140px]">
                  {sector.sector}
                </span>
                <span className={cn(
                  'text-xs font-mono',
                  deviation > 5 ? 'text-amber-400' :
                  deviation < -5 ? 'text-blue-400' : 'text-slate-400'
                )}>
                  {deviation > 0 ? '+' : ''}{deviation.toFixed(1)}%
                </span>
              </div>
              <div className="relative h-3 bg-slate-700/50 rounded">
                {/* Benchmark bar */}
                <div
                  className="absolute top-0 left-0 h-full bg-slate-600/50 rounded"
                  style={{ width: `${benchmarkWidth}%` }}
                />
                {/* Portfolio bar */}
                <div
                  className="absolute top-0 left-0 h-full rounded transition-all"
                  style={{
                    width: `${portfolioWidth}%`,
                    backgroundColor: SECTOR_COLORS[sector.sector] || '#64748b',
                  }}
                />
              </div>
            </div>
          );
        })}
        <div className="flex items-center justify-center gap-4 pt-2 text-xs text-slate-500">
          <div className="flex items-center gap-1">
            <div className="w-3 h-2 rounded bg-purple-500" />
            <span>Portfolio</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-2 rounded bg-slate-600" />
            <span>S&P 500</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================
// Sector Exposure Table
// ============================================

export function SectorExposureTable({
  positions,
  sectorMap,
  className,
}: SectorExposureProps) {
  const { data, isLoading } = useSectorExposure(positions, sectorMap, {
    enabled: positions.length > 0,
  });

  if (positions.length === 0 || isLoading || !data) {
    return null;
  }

  return (
    <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
            <PieChartIcon className="h-4 w-4 text-purple-400" />
            Sector Exposure
          </CardTitle>
          <div className="flex items-center gap-2">
            {data.overweight_count > 0 && (
              <Badge variant="outline" className="text-xs bg-amber-500/10 text-amber-400 border-amber-500/30">
                {data.overweight_count} overweight
              </Badge>
            )}
            {data.underweight_count > 0 && (
              <Badge variant="outline" className="text-xs bg-blue-500/10 text-blue-400 border-blue-500/30">
                {data.underweight_count} underweight
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-2 text-slate-500 font-normal">Sector</th>
                <th className="text-right py-2 text-slate-500 font-normal">Weight</th>
                <th className="text-right py-2 text-slate-500 font-normal">Benchmark</th>
                <th className="text-right py-2 text-slate-500 font-normal">Deviation</th>
                <th className="text-center py-2 text-slate-500 font-normal">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.sectors.filter(s => s.weight > 0 || s.benchmark_weight > 3).map(sector => (
                <tr key={sector.sector} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                  <td className="py-2 text-white">{sector.sector}</td>
                  <td className="py-2 text-right font-mono text-slate-300">
                    {sector.weight.toFixed(1)}%
                  </td>
                  <td className="py-2 text-right font-mono text-slate-500">
                    {sector.benchmark_weight.toFixed(1)}%
                  </td>
                  <td className="py-2 text-right">
                    <DeviationDisplay deviation={sector.deviation} />
                  </td>
                  <td className="py-2 text-center">
                    <Badge
                      variant="outline"
                      className={cn('text-xs', getSectorStatusBadge(sector.status))}
                    >
                      {sector.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function DeviationDisplay({ deviation }: { deviation: number }) {
  if (Math.abs(deviation) < 2) {
    return (
      <span className="flex items-center justify-end gap-1 text-slate-400">
        <Minus className="h-3 w-3" />
        <span className="font-mono">—</span>
      </span>
    );
  }

  const isPositive = deviation > 0;
  const color = isPositive ? 'text-amber-400' : 'text-blue-400';
  const Icon = isPositive ? ArrowUpRight : ArrowDownRight;

  return (
    <span className={cn('flex items-center justify-end gap-1 font-mono', color)}>
      <Icon className="h-3 w-3" />
      {isPositive ? '+' : ''}{deviation.toFixed(1)}%
    </span>
  );
}

// ============================================
// Rebalancing Suggestions
// ============================================

export function SectorRebalanceCard({
  positions,
  sectorMap,
  className,
}: SectorExposureProps) {
  const [profile, setProfile] = useState<'balanced' | 'aggressive' | 'defensive'>('balanced');
  
  const { data, isLoading } = useSectorRebalance(positions, profile, sectorMap, {
    enabled: positions.length > 0,
  });

  if (positions.length === 0) {
    return null;
  }

  const profiles = [
    { value: 'balanced', label: 'Balanced' },
    { value: 'aggressive', label: 'Aggressive' },
    { value: 'defensive', label: 'Defensive' },
  ] as const;

  return (
    <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-green-400" />
            Rebalancing Suggestions
          </CardTitle>
          <div className="flex items-center gap-1">
            {profiles.map(p => (
              <Button
                key={p.value}
                variant={profile === p.value ? 'default' : 'outline'}
                size="sm"
                className={cn(
                  'h-6 px-2 text-xs',
                  profile === p.value ? 'bg-purple-600 hover:bg-purple-500' : 'border-slate-600'
                )}
                onClick={() => setProfile(p.value)}
              >
                {p.label}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : data ? (
          <div className="space-y-2">
            {data.filter(s => s.action !== 'hold').slice(0, 5).map(suggestion => (
              <RebalanceSuggestionRow key={suggestion.sector} suggestion={suggestion} />
            ))}
            {data.filter(s => s.action !== 'hold').length === 0 && (
              <p className="text-center text-slate-500 py-4">
                Portfolio is well-balanced for this profile
              </p>
            )}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function RebalanceSuggestionRow({
  suggestion,
}: {
  suggestion: SectorRebalanceSuggestion;
}) {
  const ActionIcon = suggestion.action === 'buy' ? TrendingUp : TrendingDown;
  
  return (
    <div className="flex items-center justify-between p-2 rounded bg-slate-900/50">
      <div className="flex items-center gap-3">
        <div className={cn(
          'w-8 h-8 rounded flex items-center justify-center',
          suggestion.action === 'buy' ? 'bg-emerald-500/20' : 'bg-red-500/20'
        )}>
          <ActionIcon className={cn(
            'h-4 w-4',
            getRebalanceActionColor(suggestion.action)
          )} />
        </div>
        <div>
          <p className="text-sm text-white">{suggestion.sector}</p>
          <p className="text-xs text-slate-500">
            {suggestion.current_weight.toFixed(1)}% → {suggestion.target_weight.toFixed(1)}%
          </p>
        </div>
      </div>
      <div className="text-right">
        <p className={cn('text-sm font-mono', getRebalanceActionColor(suggestion.action))}>
          {suggestion.action === 'buy' ? '+' : ''}{suggestion.change_needed.toFixed(1)}%
        </p>
        <Badge
          variant="outline"
          className={cn(
            'text-xs',
            suggestion.priority === 'high' ? 'bg-red-500/10 text-red-400 border-red-500/30' :
            suggestion.priority === 'medium' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
            'bg-slate-500/10 text-slate-400 border-slate-500/30'
          )}
        >
          {suggestion.priority}
        </Badge>
      </div>
    </div>
  );
}

// ============================================
// Loading Skeleton
// ============================================

function SectorChartSkeleton({ className }: { className?: string }) {
  return (
    <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent>
        <div className="flex items-start gap-6">
          <Skeleton className="w-32 h-32 rounded-full" />
          <div className="flex-1 space-y-2">
            {[1, 2, 3, 4, 5].map(i => (
              <Skeleton key={i} className="h-4 w-full" />
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

