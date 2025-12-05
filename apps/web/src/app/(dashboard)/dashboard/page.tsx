'use client';

import { useMemo } from 'react';
import { useAuth } from '@/lib/auth/auth-context';
import {
  usePortfolioSummary,
  usePositions,
  usePriceStream,
} from '@/lib/api/hooks';
import { WelcomeModal } from '@/components/onboarding/welcome-modal';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LoadingState, Skeleton } from '@/components/ui/loading';
import { ErrorState, EmptyState } from '@/components/ui/error';
import { PositionList } from '@/components/portfolio';
import { AllocationChart } from '@/components/portfolio/charts';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  Plus,
  Search,
  Settings,
  Wifi,
  WifiOff,
} from 'lucide-react';
import Link from 'next/link';
import { formatCurrency, formatPercent, cn } from '@/lib/utils';

// Market indices (could be fetched from API in future)
const marketOverview = [
  { name: 'S&P 500', value: 5234.18, change: 0.82 },
  { name: 'NASDAQ', value: 16543.25, change: 1.15 },
  { name: 'DOW', value: 39150.33, change: 0.45 },
];

export default function DashboardPage() {
  const { user } = useAuth();

  // Fetch portfolio data
  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
    refetch: refetchSummary,
  } = usePortfolioSummary();

  const {
    data: positions,
    isLoading: positionsLoading,
    isError: positionsError,
    refetch: refetchPositions,
  } = usePositions();

  // Get tickers for SSE subscription
  const tickers = useMemo(
    () => positions?.map((p) => p.ticker) ?? [],
    [positions]
  );

  // Subscribe to live price updates
  const { status: sseStatus, isConnected } = usePriceStream(tickers, {
    enabled: tickers.length > 0,
  });

  // Top performers (sorted by gain)
  const topPositions = useMemo(() => {
    if (!positions) return [];
    return [...positions]
      .sort((a, b) => (b.market_value ?? b.cost_basis) - (a.market_value ?? a.cost_basis))
      .slice(0, 4);
  }, [positions]);

  const isLoading = summaryLoading || positionsLoading;
  const hasError = summaryError || positionsError;

  if (hasError) {
    return (
      <ErrorState
        title="Failed to load dashboard"
        message="We couldn't load your portfolio data. Please try again."
        onRetry={() => {
          refetchSummary();
          refetchPositions();
        }}
      />
    );
  }

  return (
    <>
      {/* Welcome Modal for new users */}
      <WelcomeModal />
      
      <div className="space-y-8">
        {/* Welcome Section */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">
              Welcome back{user?.name ? `, ${user.name.split(' ')[0]}` : user?.email ? `, ${user.email.split('@')[0]}` : ''}
          </h1>
          <p className="text-slate-400 mt-1">
            Here&apos;s what&apos;s happening with your portfolio today.
          </p>
        </div>
        {/* SSE Status Indicator */}
        <div className="flex items-center space-x-2">
          {isConnected ? (
            <Wifi className="h-4 w-4 text-emerald-400" />
          ) : (
            <WifiOff className="h-4 w-4 text-slate-500" />
          )}
          <span className="text-xs text-slate-500">
            {isConnected ? 'Live' : 'Offline'}
          </span>
        </div>
      </div>

      {/* Portfolio Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Portfolio Value"
          value={summary ? formatCurrency(summary.total_value) : undefined}
          isLoading={isLoading}
          icon={<DollarSign className="h-5 w-5" />}
        />
        <SummaryCard
          title="Day Change"
          value={summary ? formatCurrency(summary.day_change) : undefined}
          change={summary?.day_change_percent}
          isLoading={isLoading}
          icon={
            (summary?.day_change ?? 0) >= 0 ? (
              <TrendingUp className="h-5 w-5" />
            ) : (
              <TrendingDown className="h-5 w-5" />
            )
          }
        />
        <SummaryCard
          title="Total Gain"
          value={summary ? formatCurrency(summary.total_gain) : undefined}
          change={summary?.total_gain_percent}
          isLoading={isLoading}
          icon={<BarChart3 className="h-5 w-5" />}
        />
        <SummaryCard
          title="Positions"
          value={summary?.positions_count?.toString() ?? positions?.length?.toString()}
          isLoading={isLoading}
          icon={<BarChart3 className="h-5 w-5" />}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Top Positions */}
        <Card className="lg:col-span-2 bg-slate-900/50 border-slate-800">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-white">Top Positions</CardTitle>
              <CardDescription className="text-slate-400">
                Your largest holdings by value
              </CardDescription>
            </div>
            <Link href="/portfolio">
              <Button variant="outline" size="sm" className="border-slate-700 text-slate-300">
                View All
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : topPositions.length > 0 ? (
              <>
                <PositionList
                  positions={topPositions}
                  showActions={false}
                  liveTickers={isConnected ? tickers : []}
                />
                <div className="mt-4">
                  <Link href="/portfolio">
                    <Button className="w-full bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 border border-emerald-600/30">
                      <Plus className="h-4 w-4 mr-2" />
                      Add Position
                    </Button>
                  </Link>
                </div>
              </>
            ) : (
              <EmptyState
                icon={<Plus className="h-8 w-8 text-slate-500" />}
                title="No positions yet"
                description="Start building your portfolio by adding your first position."
                action={{
                  label: 'Add Position',
                  onClick: () => {
                    window.location.href = '/portfolio';
                  },
                }}
              />
            )}
          </CardContent>
        </Card>

        {/* Allocation Chart */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Allocation</CardTitle>
            <CardDescription className="text-slate-400">
              Portfolio breakdown
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center h-[250px]">
                <Skeleton className="h-32 w-32 rounded-full" />
              </div>
            ) : positions && positions.length > 0 ? (
              <AllocationChart positions={positions} height={250} />
            ) : (
              <div className="flex items-center justify-center h-[250px]">
                <p className="text-slate-500 text-sm">Add positions to see allocation</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Market Overview */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white">Market Overview</CardTitle>
          <CardDescription className="text-slate-400">
            Major indices today
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {marketOverview.map((index) => (
              <div
                key={index.name}
                className="flex items-center justify-between p-4 rounded-lg bg-slate-800/50"
              >
                <div>
                  <p className="text-white font-medium">{index.name}</p>
                  <p className="text-sm text-slate-400">
                    {index.value.toLocaleString()}
                  </p>
                </div>
                <div
                  className={cn(
                    'flex items-center px-2 py-1 rounded',
                    index.change >= 0
                      ? 'bg-emerald-600/20 text-emerald-400'
                      : 'bg-red-600/20 text-red-400'
                  )}
                >
                  {index.change >= 0 ? (
                    <ArrowUpRight className="h-4 w-4 mr-1" />
                  ) : (
                    <ArrowDownRight className="h-4 w-4 mr-1" />
                  )}
                  {formatPercent(index.change)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white">Quick Actions</CardTitle>
          <CardDescription className="text-slate-400">
            Common tasks at your fingertips
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <QuickActionButton
              href="/portfolio"
              icon={<Plus className="h-5 w-5" />}
              title="Add Position"
              description="Track a new stock"
            />
            <QuickActionButton
              href="/screener"
              icon={<Search className="h-5 w-5" />}
              title="Stock Screener"
              description="Find opportunities"
            />
            <QuickActionButton
              href="/portfolio"
              icon={<BarChart3 className="h-5 w-5" />}
              title="View Analytics"
              description="Portfolio insights"
            />
            <QuickActionButton
              href="/settings"
              icon={<Settings className="h-5 w-5" />}
              title="Settings"
              description="Manage account"
            />
          </div>
        </CardContent>
      </Card>
      </div>
    </>
  );
}

function SummaryCard({
  title,
  value,
  change,
  icon,
  isLoading,
}: {
  title: string;
  value?: string;
  change?: number;
  icon: React.ReactNode;
  isLoading?: boolean;
}) {
  return (
    <Card className="bg-slate-900/50 border-slate-800">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="p-2 rounded-lg bg-emerald-600/20 text-emerald-400">
            {icon}
          </div>
          {change !== undefined && !isLoading && (
            <span
              className={cn(
                'text-sm',
                change >= 0 ? 'text-emerald-400' : 'text-red-400'
              )}
            >
              {formatPercent(change)}
            </span>
          )}
        </div>
        <div className="mt-4">
          <p className="text-sm text-slate-400">{title}</p>
          {isLoading ? (
            <Skeleton className="h-8 w-24 mt-1" />
          ) : (
            <p className="text-2xl font-bold text-white">{value ?? '—'}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function QuickActionButton({
  href,
  icon,
  title,
  description,
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="flex items-center space-x-4 p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors group"
    >
      <div className="p-2 rounded-lg bg-emerald-600/20 text-emerald-400 group-hover:bg-emerald-600/30 transition-colors">
        {icon}
      </div>
      <div>
        <p className="text-white font-medium">{title}</p>
        <p className="text-sm text-slate-400">{description}</p>
      </div>
    </Link>
  );
}
