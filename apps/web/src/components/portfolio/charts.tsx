'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  Legend,
} from 'recharts';
import { formatCurrency, formatPercent, cn } from '@/lib/utils';
import type { Position, ChartDataPoint, PerformanceDataPoint } from '@/lib/api/types';

// Color palette for charts
const COLORS = [
  '#22c55e', // emerald-500
  '#3b82f6', // blue-500
  '#f59e0b', // amber-500
  '#ec4899', // pink-500
  '#8b5cf6', // violet-500
  '#14b8a6', // teal-500
  '#f97316', // orange-500
  '#06b6d4', // cyan-500
];

// Legacy interface for backward compatibility
interface LegacyChartProps {
  data: ChartDataPoint[];
  benchmark?: ChartDataPoint[];
  height?: number;
}

// New interface for API data
interface PerformanceChartProps {
  data: PerformanceDataPoint[];
  showBenchmark?: boolean;
  height?: number;
  showReturns?: boolean; // Show cumulative returns instead of absolute values
}

export function PortfolioPerformanceChart({
  data,
  showBenchmark = true,
  height = 300,
  showReturns = false,
}: PerformanceChartProps) {
  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-slate-800/30 rounded-lg"
        style={{ height }}
      >
        <p className="text-slate-500">No performance data available</p>
      </div>
    );
  }

  // Determine if overall trend is positive
  const firstValue = data[0]?.portfolio_value ?? 0;
  const lastValue = data[data.length - 1]?.portfolio_value ?? 0;
  const isPositive = lastValue >= firstValue;
  const primaryColor = isPositive ? '#22c55e' : '#ef4444';

  // Prepare chart data
  const chartData = data.map((d) => ({
    date: d.date,
    portfolio: showReturns ? d.cumulative_return : d.portfolio_value,
    benchmark: showReturns ? d.benchmark_return : d.benchmark_value,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={primaryColor} stopOpacity={0.3} />
            <stop offset="95%" stopColor={primaryColor} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="benchmarkGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6b7280" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#6b7280" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="date"
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6b7280', fontSize: 12 }}
          tickFormatter={(value) => {
            const date = new Date(value);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          }}
        />
        <YAxis
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6b7280', fontSize: 12 }}
          tickFormatter={(value) =>
            showReturns
              ? `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`
              : `$${(value / 1000).toFixed(0)}k`
          }
          domain={['auto', 'auto']}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
          }}
          labelStyle={{ color: '#94a3b8' }}
          formatter={(value, name) => {
            if (value === null || value === undefined) return ['-', name];
            const numValue = typeof value === 'number' ? value : 0;
            const formattedValue = showReturns
              ? `${numValue >= 0 ? '+' : ''}${numValue.toFixed(2)}%`
              : formatCurrency(numValue);
            const label = name === 'portfolio' ? 'Portfolio' : 'S&P 500';
            return [formattedValue, label];
          }}
          labelFormatter={(label) =>
            new Date(label).toLocaleDateString('en-US', {
              month: 'long',
              day: 'numeric',
              year: 'numeric',
            })
          }
        />
        <Area
          type="monotone"
          dataKey="portfolio"
          stroke={primaryColor}
          strokeWidth={2}
          fill="url(#portfolioGradient)"
          name="portfolio"
        />
        {showBenchmark && (
          <Area
            type="monotone"
            dataKey="benchmark"
            stroke="#6b7280"
            strokeWidth={1}
            strokeDasharray="4 4"
            fill="url(#benchmarkGradient)"
            name="benchmark"
          />
        )}
      </AreaChart>
    </ResponsiveContainer>
  );
}

// Legacy component for backward compatibility with old data format
export function LegacyPerformanceChart({
  data,
  benchmark,
  height = 300,
}: LegacyChartProps) {
  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-slate-800/30 rounded-lg"
        style={{ height }}
      >
        <p className="text-slate-500">No performance data available</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="legacyPortfolioGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="date"
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6b7280', fontSize: 12 }}
          tickFormatter={(value) => {
            const date = new Date(value);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          }}
        />
        <YAxis
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6b7280', fontSize: 12 }}
          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
          domain={['auto', 'auto']}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
          }}
          labelStyle={{ color: '#94a3b8' }}
          formatter={(value: number) => [formatCurrency(value), 'Portfolio']}
          labelFormatter={(label) =>
            new Date(label).toLocaleDateString('en-US', {
              month: 'long',
              day: 'numeric',
              year: 'numeric',
            })
          }
        />
        <Area
          type="monotone"
          dataKey="value"
          stroke="#22c55e"
          strokeWidth={2}
          fill="url(#legacyPortfolioGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface AllocationChartProps {
  positions: Position[];
  height?: number;
  showLegend?: boolean;
}

export function AllocationChart({
  positions,
  height = 250,
  showLegend = true,
}: AllocationChartProps) {
  if (!positions || positions.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-slate-800/30 rounded-lg"
        style={{ height }}
      >
        <p className="text-slate-500">No positions to display</p>
      </div>
    );
  }

  // Calculate total value and allocation
  const totalValue = positions.reduce(
    (sum, p) => sum + (p.market_value ?? p.cost_basis),
    0
  );

  const chartData = positions
    .map((p, index) => ({
      name: p.ticker,
      value: p.market_value ?? p.cost_basis,
      percentage: ((p.market_value ?? p.cost_basis) / totalValue) * 100,
      color: COLORS[index % COLORS.length],
    }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="flex items-center" style={{ height }}>
      <ResponsiveContainer width={showLegend ? '50%' : '100%'} height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
            }}
            formatter={(value: number, name: string) => [
              formatCurrency(value),
              name,
            ]}
          />
        </PieChart>
      </ResponsiveContainer>

      {showLegend && (
        <div className="flex-1 space-y-2 pl-4">
          {chartData.slice(0, 6).map((entry) => (
            <div key={entry.name} className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-white">{entry.name}</span>
              </div>
              <span className="text-sm text-slate-400">
                {entry.percentage.toFixed(1)}%
              </span>
            </div>
          ))}
          {chartData.length > 6 && (
            <p className="text-xs text-slate-500">
              +{chartData.length - 6} more
            </p>
          )}
        </div>
      )}
    </div>
  );
}

interface MiniSparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
}

export function MiniSparkline({
  data,
  width = 80,
  height = 30,
  color,
}: MiniSparklineProps) {
  if (!data || data.length < 2) return null;

  const isPositive = data[data.length - 1] >= data[0];
  const strokeColor = color ?? (isPositive ? '#22c55e' : '#ef4444');

  const chartData = data.map((value, index) => ({ index, value }));

  return (
    <ResponsiveContainer width={width} height={height}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={strokeColor}
          strokeWidth={1.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

interface GainLossBarProps {
  value: number;
  max: number;
  className?: string;
}

export function GainLossBar({ value, max, className }: GainLossBarProps) {
  const percentage = Math.min(Math.abs(value) / max * 100, 100);
  const isPositive = value >= 0;

  return (
    <div className={cn('flex items-center space-x-2', className)}>
      <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-300',
            isPositive ? 'bg-emerald-500' : 'bg-red-500'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span
        className={cn(
          'text-sm font-medium w-16 text-right',
          isPositive ? 'text-emerald-400' : 'text-red-400'
        )}
      >
        {formatPercent(value)}
      </span>
    </div>
  );
}

