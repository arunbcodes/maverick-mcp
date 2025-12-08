'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/loading';
import { cn } from '@/lib/utils';
import {
  useCorrelationMatrix,
  useCalculateCorrelationMatrix,
  getCorrelationBgColor,
  getCorrelationTextColor,
  type CorrelationMatrix,
} from '@/lib/api/hooks/use-risk';
import { RefreshCw, AlertTriangle, TrendingUp, Grid3X3 } from 'lucide-react';

interface CorrelationHeatmapProps {
  tickers: string[];
  periodDays?: number;
  className?: string;
  showStats?: boolean;
}

/**
 * Interactive correlation heatmap component
 */
export function CorrelationHeatmap({
  tickers,
  periodDays = 90,
  className,
  showStats = true,
}: CorrelationHeatmapProps) {
  const [selectedPeriod, setSelectedPeriod] = useState(periodDays);
  const [hoveredCell, setHoveredCell] = useState<{ i: number; j: number } | null>(null);

  const { data: matrix, isLoading, error, refetch } = useCorrelationMatrix(
    tickers,
    selectedPeriod,
    { enabled: tickers.length >= 2 }
  );

  const periods = [
    { value: 30, label: '30D' },
    { value: 90, label: '90D' },
    { value: 180, label: '6M' },
    { value: 252, label: '1Y' },
  ];

  if (tickers.length < 2) {
    return (
      <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
        <CardContent className="py-8 text-center">
          <Grid3X3 className="h-12 w-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">Add at least 2 positions to see correlations</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
        <CardContent className="py-8 text-center">
          <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-3" />
          <p className="text-red-400">Failed to calculate correlations</p>
          <Button variant="outline" size="sm" className="mt-4" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
          <Grid3X3 className="h-4 w-4 text-purple-400" />
          Correlation Matrix
        </CardTitle>
        <div className="flex items-center gap-2">
          {periods.map((p) => (
            <Button
              key={p.value}
              variant={selectedPeriod === p.value ? 'default' : 'outline'}
              size="sm"
              className={cn(
                'h-7 px-2 text-xs',
                selectedPeriod === p.value
                  ? 'bg-purple-600 hover:bg-purple-500'
                  : 'border-slate-600'
              )}
              onClick={() => setSelectedPeriod(p.value)}
            >
              {p.label}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <HeatmapSkeleton size={tickers.length} />
        ) : matrix ? (
          <>
            <HeatmapGrid
              matrix={matrix}
              hoveredCell={hoveredCell}
              onCellHover={setHoveredCell}
            />
            {showStats && <HeatmapStats matrix={matrix} />}
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}

/**
 * Heatmap grid component
 */
function HeatmapGrid({
  matrix,
  hoveredCell,
  onCellHover,
}: {
  matrix: CorrelationMatrix;
  hoveredCell: { i: number; j: number } | null;
  onCellHover: (cell: { i: number; j: number } | null) => void;
}) {
  const { tickers, matrix: values } = matrix;
  const n = tickers.length;

  // Calculate cell size based on number of tickers
  const cellSize = n <= 5 ? 'w-14 h-14' : n <= 8 ? 'w-12 h-12' : 'w-10 h-10';
  const fontSize = n <= 5 ? 'text-sm' : 'text-xs';
  const tickerFontSize = n <= 5 ? 'text-xs' : 'text-[10px]';

  return (
    <div className="overflow-x-auto">
      <div className="inline-block">
        {/* Header row with tickers */}
        <div className="flex">
          <div className={cn(cellSize)} /> {/* Empty corner */}
          {tickers.map((ticker) => (
            <div
              key={ticker}
              className={cn(
                cellSize,
                'flex items-end justify-center pb-1',
                tickerFontSize,
                'text-slate-400 font-medium'
              )}
            >
              <span className="-rotate-45 origin-center">{ticker}</span>
            </div>
          ))}
        </div>

        {/* Matrix rows */}
        {tickers.map((rowTicker, i) => (
          <div key={rowTicker} className="flex">
            {/* Row label */}
            <div
              className={cn(
                cellSize,
                'flex items-center justify-end pr-2',
                tickerFontSize,
                'text-slate-400 font-medium'
              )}
            >
              {rowTicker}
            </div>
            {/* Cells */}
            {tickers.map((colTicker, j) => {
              const correlation = values[i][j];
              const isHovered = hoveredCell?.i === i && hoveredCell?.j === j;
              const isDiagonal = i === j;

              return (
                <div
                  key={`${rowTicker}-${colTicker}`}
                  className={cn(
                    cellSize,
                    'flex items-center justify-center border border-slate-700/50 transition-all cursor-pointer',
                    isHovered && 'ring-2 ring-white/50 z-10',
                    isDiagonal && 'bg-slate-700/30'
                  )}
                  style={{
                    backgroundColor: isDiagonal
                      ? undefined
                      : getCorrelationBgColor(correlation),
                  }}
                  onMouseEnter={() => onCellHover({ i, j })}
                  onMouseLeave={() => onCellHover(null)}
                >
                  <span
                    className={cn(
                      fontSize,
                      'font-mono',
                      isDiagonal ? 'text-slate-500' : getCorrelationTextColor(correlation)
                    )}
                  >
                    {correlation.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {/* Tooltip */}
      {hoveredCell && (
        <HeatmapTooltip
          ticker1={tickers[hoveredCell.i]}
          ticker2={tickers[hoveredCell.j]}
          correlation={values[hoveredCell.i][hoveredCell.j]}
        />
      )}
    </div>
  );
}

/**
 * Tooltip for hovered cell
 */
function HeatmapTooltip({
  ticker1,
  ticker2,
  correlation,
}: {
  ticker1: string;
  ticker2: string;
  correlation: number;
}) {
  const interpretation = useMemo(() => {
    const absCorr = Math.abs(correlation);
    const direction = correlation > 0 ? 'positively' : 'negatively';

    if (ticker1 === ticker2) return 'Same stock (always 1.0)';
    if (absCorr >= 0.8) return `Very strongly ${direction} correlated`;
    if (absCorr >= 0.6) return `Strongly ${direction} correlated`;
    if (absCorr >= 0.4) return `Moderately ${direction} correlated`;
    if (absCorr >= 0.2) return `Weakly ${direction} correlated`;
    return 'Very low correlation';
  }, [ticker1, ticker2, correlation]);

  const riskLevel = useMemo(() => {
    if (ticker1 === ticker2) return null;
    const absCorr = Math.abs(correlation);
    if (absCorr >= 0.7) return { level: 'High', color: 'text-red-400' };
    if (absCorr >= 0.5) return { level: 'Medium', color: 'text-yellow-400' };
    return { level: 'Low', color: 'text-emerald-400' };
  }, [ticker1, ticker2, correlation]);

  return (
    <div className="mt-4 p-3 rounded-lg bg-slate-900/80 border border-slate-700">
      <div className="flex items-center justify-between mb-2">
        <span className="text-white font-medium">
          {ticker1} ↔ {ticker2}
        </span>
        <span className={cn('font-mono text-lg', getCorrelationTextColor(correlation))}>
          {correlation.toFixed(4)}
        </span>
      </div>
      <p className="text-sm text-slate-400">{interpretation}</p>
      {riskLevel && (
        <p className="text-xs mt-1">
          Concentration Risk:{' '}
          <span className={riskLevel.color}>{riskLevel.level}</span>
        </p>
      )}
    </div>
  );
}

/**
 * Statistics summary
 */
function HeatmapStats({ matrix }: { matrix: CorrelationMatrix }) {
  const { stats } = matrix;

  return (
    <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
      <StatCard
        label="Avg Correlation"
        value={stats.avg_correlation.toFixed(2)}
        color={getCorrelationTextColor(stats.avg_correlation)}
      />
      <StatCard
        label="Max Correlation"
        value={stats.max_correlation.toFixed(2)}
        color={getCorrelationTextColor(stats.max_correlation)}
      />
      <StatCard
        label="High Pairs"
        value={stats.high_correlation_count.toString()}
        color={stats.high_correlation_count > 0 ? 'text-red-400' : 'text-emerald-400'}
        subtitle="|corr| > 0.7"
      />
      <StatCard
        label="Low Pairs"
        value={stats.low_correlation_count.toString()}
        color="text-emerald-400"
        subtitle="|corr| < 0.3"
      />
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
  subtitle,
}: {
  label: string;
  value: string;
  color: string;
  subtitle?: string;
}) {
  return (
    <div className="p-2 rounded bg-slate-900/50 text-center">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={cn('text-lg font-mono font-bold', color)}>{value}</p>
      {subtitle && <p className="text-[10px] text-slate-600">{subtitle}</p>}
    </div>
  );
}

/**
 * Loading skeleton
 */
function HeatmapSkeleton({ size }: { size: number }) {
  const cellSize = 'w-12 h-12';

  return (
    <div className="space-y-1">
      {Array.from({ length: size + 1 }).map((_, i) => (
        <div key={i} className="flex gap-1">
          {Array.from({ length: size + 1 }).map((_, j) => (
            <Skeleton key={j} className={cellSize} />
          ))}
        </div>
      ))}
    </div>
  );
}

/**
 * Mini correlation heatmap for dashboard
 */
export function MiniCorrelationHeatmap({
  tickers,
  className,
}: {
  tickers: string[];
  className?: string;
}) {
  const { data: matrix, isLoading } = useCorrelationMatrix(tickers, 90, {
    enabled: tickers.length >= 2,
  });

  if (tickers.length < 2 || isLoading || !matrix) {
    return (
      <div className={cn('h-20 bg-slate-800/30 rounded flex items-center justify-center', className)}>
        {isLoading ? (
          <div className="animate-pulse text-slate-600">Loading...</div>
        ) : (
          <span className="text-xs text-slate-500">Need 2+ positions</span>
        )}
      </div>
    );
  }

  // Just show average and high count
  const { stats } = matrix;

  return (
    <div className={cn('flex items-center gap-4', className)}>
      <div className="text-center">
        <p className="text-[10px] text-slate-500">Avg</p>
        <p className={cn('text-sm font-mono', getCorrelationTextColor(stats.avg_correlation))}>
          {stats.avg_correlation.toFixed(2)}
        </p>
      </div>
      {stats.high_correlation_count > 0 && (
        <div className="flex items-center gap-1 text-red-400">
          <AlertTriangle className="h-3 w-3" />
          <span className="text-xs">{stats.high_correlation_count} high</span>
        </div>
      )}
    </div>
  );
}

