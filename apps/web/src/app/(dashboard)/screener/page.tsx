'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import {
  useMaverickStocks,
  useMaverickBearStocks,
  useBreakoutStocks,
  useFilteredScreening,
} from '@/lib/api/hooks';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LoadingState, Skeleton } from '@/components/ui/loading';
import { ErrorState, EmptyState } from '@/components/ui/error';
import {
  Search,
  TrendingUp,
  TrendingDown,
  Zap,
  Filter,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ExternalLink,
  ChevronDown,
} from 'lucide-react';
import { formatCurrency, formatPercent, formatCompactNumber, cn } from '@/lib/utils';
import type { ScreeningResult, ScreeningFilters } from '@/lib/api/types';

type Strategy = 'maverick' | 'maverick-bear' | 'breakouts';
type SortField = 'ticker' | 'price' | 'change_percent' | 'score' | 'volume';
type SortDirection = 'asc' | 'desc';

const STRATEGIES = [
  {
    id: 'maverick' as Strategy,
    name: 'Maverick Picks',
    description: 'High momentum bullish opportunities',
    icon: Zap,
    color: 'emerald',
  },
  {
    id: 'maverick-bear' as Strategy,
    name: 'Bearish Signals',
    description: 'Weakness and short opportunities',
    icon: TrendingDown,
    color: 'red',
  },
  {
    id: 'breakouts' as Strategy,
    name: 'Breakouts',
    description: 'Breaking key resistance levels',
    icon: TrendingUp,
    color: 'blue',
  },
];

export default function ScreenerPage() {
  const [activeStrategy, setActiveStrategy] = useState<Strategy>('maverick');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<SortField>('score');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<ScreeningFilters>({});

  // Fetch data based on strategy
  const maverickQuery = useMaverickStocks(50, { enabled: activeStrategy === 'maverick' });
  const bearQuery = useMaverickBearStocks(50, { enabled: activeStrategy === 'maverick-bear' });
  const breakoutQuery = useBreakoutStocks(50, { enabled: activeStrategy === 'breakouts' });

  // Get current query based on strategy
  const currentQuery = useMemo(() => {
    switch (activeStrategy) {
      case 'maverick':
        return maverickQuery;
      case 'maverick-bear':
        return bearQuery;
      case 'breakouts':
        return breakoutQuery;
    }
  }, [activeStrategy, maverickQuery, bearQuery, breakoutQuery]);

  const { data: screeningData, isLoading, isError, refetch } = currentQuery;

  // Filter and sort results
  const filteredResults = useMemo(() => {
    if (!screeningData?.results) return [];

    let results = [...screeningData.results];

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      results = results.filter(
        (r) =>
          r.ticker.toLowerCase().includes(query) ||
          r.name.toLowerCase().includes(query)
      );
    }

    // Apply filters
    if (filters.min_price) {
      results = results.filter((r) => r.price >= filters.min_price!);
    }
    if (filters.max_price) {
      results = results.filter((r) => r.price <= filters.max_price!);
    }
    if (filters.min_volume) {
      results = results.filter((r) => r.volume >= filters.min_volume!);
    }
    if (filters.min_momentum_score) {
      results = results.filter((r) => r.score >= filters.min_momentum_score!);
    }

    // Sort
    results.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'ticker':
          comparison = a.ticker.localeCompare(b.ticker);
          break;
        case 'price':
          comparison = a.price - b.price;
          break;
        case 'change_percent':
          comparison = a.change_percent - b.change_percent;
          break;
        case 'score':
          comparison = a.score - b.score;
          break;
        case 'volume':
          comparison = a.volume - b.volume;
          break;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return results;
  }, [screeningData, searchQuery, filters, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const activeStrategyInfo = STRATEGIES.find((s) => s.id === activeStrategy)!;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Stock Screener</h1>
        <p className="text-slate-400 mt-1">
          Find stocks matching Maverick&apos;s AI-powered screening criteria
        </p>
      </div>

      {/* Strategy Tabs */}
      <div className="flex flex-wrap gap-3">
        {STRATEGIES.map((strategy) => {
          const isActive = activeStrategy === strategy.id;
          const Icon = strategy.icon;
          return (
            <button
              key={strategy.id}
              onClick={() => setActiveStrategy(strategy.id)}
              className={cn(
                'flex items-center space-x-3 px-4 py-3 rounded-lg border transition-all',
                isActive
                  ? 'bg-slate-800 border-emerald-600/50 text-white'
                  : 'bg-slate-900/50 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
              )}
            >
              <div
                className={cn(
                  'p-2 rounded-lg',
                  isActive ? 'bg-emerald-600/20' : 'bg-slate-800'
                )}
              >
                <Icon
                  className={cn(
                    'h-5 w-5',
                    isActive ? 'text-emerald-400' : 'text-slate-500'
                  )}
                />
              </div>
              <div className="text-left">
                <p className="font-medium">{strategy.name}</p>
                <p className="text-xs text-slate-500">{strategy.description}</p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Search & Filters */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <Input
                placeholder="Search by ticker or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-slate-800 border-slate-700 text-white"
              />
            </div>
            {/* Filter Toggle */}
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className={cn(
                'border-slate-700',
                showFilters ? 'text-emerald-400 border-emerald-600/50' : 'text-slate-300'
              )}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filters
              <ChevronDown
                className={cn(
                  'h-4 w-4 ml-2 transition-transform',
                  showFilters && 'rotate-180'
                )}
              />
            </Button>
          </div>

          {/* Filter Controls */}
          {showFilters && (
            <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-xs text-slate-400 mb-1 block">
                  Min Price
                </label>
                <Input
                  type="number"
                  placeholder="$0"
                  value={filters.min_price ?? ''}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      min_price: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">
                  Max Price
                </label>
                <Input
                  type="number"
                  placeholder="$999"
                  value={filters.max_price ?? ''}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      max_price: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">
                  Min Volume
                </label>
                <Input
                  type="number"
                  placeholder="100K"
                  value={filters.min_volume ?? ''}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      min_volume: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 mb-1 block">
                  Min Score
                </label>
                <Input
                  type="number"
                  placeholder="0-100"
                  min={0}
                  max={100}
                  value={filters.min_momentum_score ?? ''}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      min_momentum_score: e.target.value
                        ? Number(e.target.value)
                        : undefined,
                    })
                  }
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-white flex items-center space-x-2">
              <activeStrategyInfo.icon className="h-5 w-5 text-emerald-400" />
              <span>{activeStrategyInfo.name}</span>
            </CardTitle>
            <CardDescription className="text-slate-400">
              {isLoading
                ? 'Loading...'
                : `${filteredResults.length} stocks found`}
            </CardDescription>
          </div>
          {screeningData?.timestamp && (
            <p className="text-xs text-slate-500">
              Updated: {new Date(screeningData.timestamp).toLocaleTimeString()}
            </p>
          )}
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : isError ? (
            <ErrorState
              title="Failed to load results"
              message="We couldn't load screening results. Please try again."
              onRetry={() => refetch()}
            />
          ) : filteredResults.length === 0 ? (
            <EmptyState
              icon={<Search className="h-8 w-8 text-slate-500" />}
              title="No stocks found"
              description={
                searchQuery
                  ? 'Try adjusting your search or filters'
                  : 'No stocks match the current criteria'
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-800">
                    <SortableHeader
                      field="ticker"
                      label="Ticker"
                      currentSort={sortField}
                      direction={sortDirection}
                      onSort={handleSort}
                    />
                    <SortableHeader
                      field="price"
                      label="Price"
                      currentSort={sortField}
                      direction={sortDirection}
                      onSort={handleSort}
                      className="text-right"
                    />
                    <SortableHeader
                      field="change_percent"
                      label="Change"
                      currentSort={sortField}
                      direction={sortDirection}
                      onSort={handleSort}
                      className="text-right"
                    />
                    <SortableHeader
                      field="volume"
                      label="Volume"
                      currentSort={sortField}
                      direction={sortDirection}
                      onSort={handleSort}
                      className="text-right hidden md:table-cell"
                    />
                    <SortableHeader
                      field="score"
                      label="Score"
                      currentSort={sortField}
                      direction={sortDirection}
                      onSort={handleSort}
                      className="text-right"
                    />
                    <th className="py-3 px-2 text-right text-xs font-medium text-slate-500 uppercase">
                      Signals
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredResults.map((result) => (
                    <ScreenerRow key={result.ticker} result={result} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function SortableHeader({
  field,
  label,
  currentSort,
  direction,
  onSort,
  className,
}: {
  field: SortField;
  label: string;
  currentSort: SortField;
  direction: SortDirection;
  onSort: (field: SortField) => void;
  className?: string;
}) {
  const isActive = currentSort === field;
  return (
    <th
      className={cn(
        'py-3 px-2 text-xs font-medium text-slate-500 uppercase cursor-pointer hover:text-white transition-colors',
        className
      )}
      onClick={() => onSort(field)}
    >
      <div className="flex items-center justify-end space-x-1">
        <span>{label}</span>
        {isActive ? (
          direction === 'asc' ? (
            <ArrowUp className="h-3 w-3" />
          ) : (
            <ArrowDown className="h-3 w-3" />
          )
        ) : (
          <ArrowUpDown className="h-3 w-3 opacity-50" />
        )}
      </div>
    </th>
  );
}

function ScreenerRow({ result }: { result: ScreeningResult }) {
  const isPositive = result.change_percent >= 0;

  return (
    <tr className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
      {/* Ticker */}
      <td className="py-3 px-2">
        <Link
          href={`/stocks/${result.ticker}`}
          className="flex items-center space-x-3 group"
        >
          <div className="w-8 h-8 rounded-lg bg-emerald-600/20 flex items-center justify-center group-hover:bg-emerald-600/30 transition-colors">
            <span className="text-emerald-400 font-semibold text-xs">
              {result.ticker.slice(0, 2)}
            </span>
          </div>
          <div>
            <p className="text-white font-medium group-hover:text-emerald-400 transition-colors">
              {result.ticker}
            </p>
            <p className="text-xs text-slate-500 truncate max-w-[150px]">
              {result.name}
            </p>
          </div>
        </Link>
      </td>
      {/* Price */}
      <td className="py-3 px-2 text-right text-white">
        {formatCurrency(result.price)}
      </td>
      {/* Change */}
      <td className="py-3 px-2 text-right">
        <span
          className={cn(
            'inline-flex items-center',
            isPositive ? 'text-emerald-400' : 'text-red-400'
          )}
        >
          {isPositive ? (
            <ArrowUp className="h-3 w-3 mr-1" />
          ) : (
            <ArrowDown className="h-3 w-3 mr-1" />
          )}
          {formatPercent(result.change_percent)}
        </span>
      </td>
      {/* Volume */}
      <td className="py-3 px-2 text-right text-slate-400 hidden md:table-cell">
        {formatCompactNumber(result.volume)}
      </td>
      {/* Score */}
      <td className="py-3 px-2 text-right">
        <ScoreBadge score={result.score} />
      </td>
      {/* Signals */}
      <td className="py-3 px-2 text-right">
        <div className="flex flex-wrap justify-end gap-1">
          {result.signals.slice(0, 2).map((signal, i) => (
            <span
              key={i}
              className="px-2 py-0.5 text-xs rounded-full bg-slate-800 text-slate-400"
            >
              {signal}
            </span>
          ))}
          {result.signals.length > 2 && (
            <span className="px-2 py-0.5 text-xs rounded-full bg-slate-800 text-slate-500">
              +{result.signals.length - 2}
            </span>
          )}
        </div>
      </td>
    </tr>
  );
}

function ScoreBadge({ score }: { score: number }) {
  let bgColor = 'bg-slate-800';
  let textColor = 'text-slate-400';

  if (score >= 80) {
    bgColor = 'bg-emerald-600/20';
    textColor = 'text-emerald-400';
  } else if (score >= 60) {
    bgColor = 'bg-blue-600/20';
    textColor = 'text-blue-400';
  } else if (score >= 40) {
    bgColor = 'bg-amber-600/20';
    textColor = 'text-amber-400';
  }

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center w-10 py-1 text-xs font-medium rounded',
        bgColor,
        textColor
      )}
    >
      {score}
    </span>
  );
}
