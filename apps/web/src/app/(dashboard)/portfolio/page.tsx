'use client';

import { useState, useMemo } from 'react';
import {
  usePortfolio,
  usePositions,
  useRemovePosition,
  usePriceStream,
} from '@/lib/api/hooks';
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
import { AddPositionModal } from '@/components/portfolio/add-position-modal';
import { AllocationChart, PortfolioPerformanceChart } from '@/components/portfolio/charts';
import {
  Plus,
  TrendingUp,
  TrendingDown,
  DollarSign,
  PieChart,
  Wifi,
  WifiOff,
  AlertTriangle,
} from 'lucide-react';
import { formatCurrency, formatPercent, cn } from '@/lib/utils';
import type { Position } from '@/lib/api/types';

export default function PortfolioPage() {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [positionToDelete, setPositionToDelete] = useState<string | null>(null);

  // Fetch data
  const {
    data: portfolio,
    isLoading: portfolioLoading,
    isError: portfolioError,
    refetch: refetchPortfolio,
  } = usePortfolio();

  const {
    data: positions,
    isLoading: positionsLoading,
  } = usePositions();

  const removePosition = useRemovePosition();

  // Get tickers for SSE subscription
  const tickers = useMemo(
    () => positions?.map((p) => p.ticker) ?? [],
    [positions]
  );

  // Subscribe to live price updates
  const { status: sseStatus, isConnected } = usePriceStream(tickers, {
    enabled: tickers.length > 0,
  });

  const isLoading = portfolioLoading || positionsLoading;

  // Calculate metrics
  const totalValue = portfolio?.total_value ?? 0;
  const totalCost = portfolio?.total_cost ?? 0;
  const totalGain = portfolio?.total_gain ?? 0;
  const totalGainPercent = portfolio?.total_gain_percent ?? 0;
  const dayChange = portfolio?.day_change ?? 0;
  const dayChangePercent = portfolio?.day_change_percent ?? 0;

  // Handle position removal
  const handleRemovePosition = async (positionId: string) => {
    if (!confirm('Are you sure you want to remove this position?')) return;
    
    try {
      await removePosition.mutateAsync(positionId);
    } catch (error) {
      console.error('Failed to remove position:', error);
    }
  };

  // Handle edit (placeholder - could open edit modal)
  const handleEditPosition = (position: Position) => {
    console.log('Edit position:', position);
    // TODO: Open edit modal
  };

  // Mock performance data (would come from API)
  const performanceData = useMemo(() => {
    const data = [];
    const now = new Date();
    let value = totalCost || 100000;
    
    for (let i = 90; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      value = value * (1 + (Math.random() * 0.04 - 0.02));
      data.push({
        date: date.toISOString().split('T')[0],
        value: Math.round(value),
      });
    }
    
    // Ensure last value matches current portfolio value
    if (data.length > 0 && totalValue) {
      data[data.length - 1].value = totalValue;
    }
    
    return data;
  }, [totalCost, totalValue]);

  if (portfolioError) {
    return (
      <ErrorState
        title="Failed to load portfolio"
        message="We couldn't load your portfolio. Please try again."
        onRetry={() => refetchPortfolio()}
      />
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Portfolio</h1>
          <p className="text-slate-400 mt-1">
            Manage and track your investments
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {/* SSE Status */}
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <Wifi className="h-4 w-4 text-emerald-400" />
            ) : (
              <WifiOff className="h-4 w-4 text-slate-500" />
            )}
            <span className="text-xs text-slate-500">
              {isConnected ? 'Live prices' : 'Offline'}
            </span>
          </div>
          <Button
            onClick={() => setIsAddModalOpen(true)}
            className="bg-emerald-600 hover:bg-emerald-500 text-white"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Position
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Total Value"
          value={formatCurrency(totalValue)}
          icon={<DollarSign className="h-5 w-5" />}
          isLoading={isLoading}
        />
        <SummaryCard
          title="Total Cost"
          value={formatCurrency(totalCost)}
          icon={<DollarSign className="h-5 w-5" />}
          isLoading={isLoading}
        />
        <SummaryCard
          title="Total Gain/Loss"
          value={formatCurrency(totalGain)}
          change={totalGainPercent}
          icon={totalGain >= 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
          isLoading={isLoading}
        />
        <SummaryCard
          title="Day Change"
          value={formatCurrency(dayChange)}
          change={dayChangePercent}
          icon={dayChange >= 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
          isLoading={isLoading}
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Performance Chart */}
        <Card className="lg:col-span-2 bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Performance</CardTitle>
            <CardDescription className="text-slate-400">
              Portfolio value over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[300px] w-full" />
            ) : positions && positions.length > 0 ? (
              <PortfolioPerformanceChart data={performanceData} height={300} />
            ) : (
              <div className="flex items-center justify-center h-[300px]">
                <p className="text-slate-500">Add positions to see performance</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Allocation Chart */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center space-x-2">
              <PieChart className="h-5 w-5 text-emerald-400" />
              <span>Allocation</span>
            </CardTitle>
            <CardDescription className="text-slate-400">
              By position value
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
                <p className="text-slate-500 text-sm">No positions</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Positions List */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-white">Positions</CardTitle>
            <CardDescription className="text-slate-400">
              {positions?.length ?? 0} total positions
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : positions && positions.length > 0 ? (
            <PositionList
              positions={positions}
              onEdit={handleEditPosition}
              onRemove={handleRemovePosition}
              showActions={true}
              liveTickers={isConnected ? tickers : []}
            />
          ) : (
            <EmptyState
              icon={<Plus className="h-8 w-8 text-slate-500" />}
              title="No positions yet"
              description="Start building your portfolio by adding your first stock position."
              action={{
                label: 'Add Your First Position',
                onClick: () => setIsAddModalOpen(true),
              }}
            />
          )}
        </CardContent>
      </Card>

      {/* Diversification Warning (if needed) */}
      {positions && positions.length > 0 && positions.length < 5 && (
        <Card className="bg-amber-900/20 border-amber-800/50">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-4">
              <div className="p-2 rounded-lg bg-amber-600/20">
                <AlertTriangle className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <h3 className="text-amber-400 font-medium">Low Diversification</h3>
                <p className="text-slate-400 text-sm mt-1">
                  Your portfolio has only {positions.length} position{positions.length > 1 ? 's' : ''}.
                  Consider adding more stocks to reduce risk through diversification.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Position Modal */}
      <AddPositionModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={() => {
          refetchPortfolio();
        }}
      />
    </div>
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
  value: string;
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
                'text-sm font-medium',
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
            <p className="text-2xl font-bold text-white">{value}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
