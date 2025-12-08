'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  Bell,
  Eye,
  PieChart,
  Activity,
  ExternalLink,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/loading';
import { cn } from '@/lib/utils';
import { useWatchlists, useWatchlist } from '@/lib/api/hooks/use-watchlists';
import { useAlerts, useUnreadAlertCount } from '@/lib/api/hooks/use-alerts';

// ============================================
// Portfolio Summary Widget
// ============================================

interface PortfolioSummaryProps {
  totalValue?: number;
  totalCost?: number;
  dayChange?: number;
  dayChangePct?: number;
  isLoading?: boolean;
}

export function PortfolioSummaryWidget({
  totalValue = 0,
  totalCost = 0,
  dayChange = 0,
  dayChangePct = 0,
  isLoading = false,
}: PortfolioSummaryProps) {
  const totalPL = totalValue - totalCost;
  const totalPLPct = totalCost > 0 ? (totalPL / totalCost) * 100 : 0;
  const isPositive = totalPL >= 0;
  const isDayPositive = dayChange >= 0;

  if (isLoading) {
    return (
      <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700">
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-40 mb-4" />
          <div className="grid grid-cols-2 gap-4">
            <Skeleton className="h-16" />
            <Skeleton className="h-16" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700 overflow-hidden relative">
      {/* Background pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:14px_14px] opacity-20" />
      
      <CardHeader className="pb-2 relative">
        <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
          <PieChart className="h-4 w-4 text-emerald-400" />
          Portfolio Value
        </CardTitle>
      </CardHeader>
      <CardContent className="relative">
        <div className="text-3xl font-bold text-white mb-4">
          ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Total P&L */}
          <div className="p-3 rounded-lg bg-slate-800/50">
            <p className="text-xs text-slate-500 mb-1">Total P&L</p>
            <div className="flex items-center gap-2">
              <span className={cn('font-semibold', isPositive ? 'text-emerald-400' : 'text-red-400')}>
                {isPositive ? '+' : ''}{totalPL.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
              </span>
              <span className={cn('text-xs', isPositive ? 'text-emerald-400' : 'text-red-400')}>
                ({isPositive ? '+' : ''}{totalPLPct.toFixed(2)}%)
              </span>
            </div>
          </div>

          {/* Day Change */}
          <div className="p-3 rounded-lg bg-slate-800/50">
            <p className="text-xs text-slate-500 mb-1">Today</p>
            <div className="flex items-center gap-2">
              {isDayPositive ? (
                <ArrowUpRight className="h-4 w-4 text-emerald-400" />
              ) : (
                <ArrowDownRight className="h-4 w-4 text-red-400" />
              )}
              <span className={cn('font-semibold', isDayPositive ? 'text-emerald-400' : 'text-red-400')}>
                {isDayPositive ? '+' : ''}{dayChange.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
              </span>
              <span className={cn('text-xs', isDayPositive ? 'text-emerald-400' : 'text-red-400')}>
                ({isDayPositive ? '+' : ''}{dayChangePct.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>

        <Link href="/portfolio">
          <Button variant="ghost" size="sm" className="w-full mt-4 text-slate-400 hover:text-white">
            View Portfolio
            <ExternalLink className="h-3 w-3 ml-2" />
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}

// ============================================
// Market Overview Widget
// ============================================

interface MarketIndex {
  name: string;
  value: number;
  change: number;
  changePct: number;
}

interface MarketOverviewProps {
  indices?: MarketIndex[];
  isLoading?: boolean;
}

export function MarketOverviewWidget({ indices, isLoading = false }: MarketOverviewProps) {
  const defaultIndices: MarketIndex[] = indices || [
    { name: 'S&P 500', value: 5123.45, change: 23.45, changePct: 0.46 },
    { name: 'NASDAQ', value: 16234.56, change: -45.67, changePct: -0.28 },
    { name: 'DOW', value: 39123.45, change: 156.78, changePct: 0.40 },
  ];

  if (isLoading) {
    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-blue-400" />
          Market Overview
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {defaultIndices.map((index) => {
            const isPositive = index.change >= 0;
            return (
              <div
                key={index.name}
                className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-700/50 transition-colors"
              >
                <div>
                  <p className="font-medium text-white">{index.name}</p>
                  <p className="text-sm text-slate-400">
                    {index.value.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </p>
                </div>
                <div className={cn('text-right', isPositive ? 'text-emerald-400' : 'text-red-400')}>
                  <div className="flex items-center gap-1">
                    {isPositive ? (
                      <TrendingUp className="h-4 w-4" />
                    ) : (
                      <TrendingDown className="h-4 w-4" />
                    )}
                    <span className="font-medium">
                      {isPositive ? '+' : ''}{index.changePct.toFixed(2)}%
                    </span>
                  </div>
                  <p className="text-xs">
                    {isPositive ? '+' : ''}{index.change.toFixed(2)}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================
// Recent Alerts Widget
// ============================================

export function RecentAlertsWidget() {
  const { data: alerts = [], isLoading } = useAlerts({ limit: 5 });
  const { data: unreadCount = 0 } = useUnreadAlertCount();

  if (isLoading) {
    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-14" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
          <Bell className="h-4 w-4 text-yellow-400" />
          Recent Alerts
          {unreadCount > 0 && (
            <span className="px-1.5 py-0.5 text-xs rounded-full bg-red-500 text-white">
              {unreadCount}
            </span>
          )}
        </CardTitle>
        <Link href="/settings?tab=alerts">
          <Button variant="ghost" size="sm" className="h-7 text-xs text-slate-400">
            Settings
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        {alerts.length === 0 ? (
          <div className="text-center py-6">
            <Bell className="h-8 w-8 text-slate-600 mx-auto mb-2" />
            <p className="text-sm text-slate-500">No alerts yet</p>
            <p className="text-xs text-slate-600 mt-1">
              Configure alerts to get notified
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {alerts.map((alert) => (
              <div
                key={alert.alert_id}
                className={cn(
                  'p-2 rounded-lg text-sm',
                  alert.status === 'unread'
                    ? 'bg-slate-700/50 border-l-2 border-emerald-500'
                    : 'bg-slate-800/30'
                )}
              >
                <p className="font-medium text-white truncate">{alert.title}</p>
                <p className="text-xs text-slate-400 truncate">{alert.message}</p>
              </div>
            ))}
          </div>
        )}

        <Link href="/alerts">
          <Button variant="ghost" size="sm" className="w-full mt-3 text-slate-400 hover:text-white">
            View All Alerts
            <ExternalLink className="h-3 w-3 ml-2" />
          </Button>
        </Link>
      </CardContent>
    </Card>
  );
}

// ============================================
// Watchlist Widget
// ============================================

export function WatchlistWidget() {
  const { data: watchlists = [], isLoading: loadingLists } = useWatchlists();
  
  // Get the default watchlist
  const defaultWatchlist = watchlists.find((w) => w.is_default) || watchlists[0];
  const { data: watchlist, isLoading: loadingItems } = useWatchlist(
    defaultWatchlist?.watchlist_id || '',
    { enabled: !!defaultWatchlist }
  );

  const isLoading = loadingLists || loadingItems;
  const items = watchlist?.items?.slice(0, 5) || [];

  if (isLoading) {
    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-2">
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-10" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
          <Eye className="h-4 w-4 text-emerald-400" />
          {watchlist?.name || 'Watchlist'}
        </CardTitle>
        <Link href="/watchlist">
          <Button variant="ghost" size="sm" className="h-7 text-xs text-slate-400">
            Manage
          </Button>
        </Link>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <div className="text-center py-6">
            <Eye className="h-8 w-8 text-slate-600 mx-auto mb-2" />
            <p className="text-sm text-slate-500">No stocks in watchlist</p>
            <Link href="/screener">
              <Button variant="outline" size="sm" className="mt-3 border-slate-600">
                Add Stocks
              </Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-1">
            {items.map((item) => {
              const isPositive = (item.price_change_pct ?? 0) >= 0;
              return (
                <Link
                  key={item.ticker}
                  href={`/stocks/${item.ticker}`}
                  className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-700/50 transition-colors"
                >
                  <span className="font-medium text-white">{item.ticker}</span>
                  <div className="text-right">
                    {item.current_price ? (
                      <>
                        <p className="text-sm text-white">
                          ${item.current_price.toFixed(2)}
                        </p>
                        {item.price_change_pct !== null && (
                          <p className={cn(
                            'text-xs',
                            isPositive ? 'text-emerald-400' : 'text-red-400'
                          )}>
                            {isPositive ? '+' : ''}{item.price_change_pct.toFixed(2)}%
                          </p>
                        )}
                      </>
                    ) : (
                      <p className="text-sm text-slate-500">--</p>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>
        )}

        {items.length > 0 && watchlist && watchlist.items.length > 5 && (
          <Link href={`/watchlist/${watchlist.watchlist_id}`}>
            <Button variant="ghost" size="sm" className="w-full mt-2 text-slate-400 hover:text-white">
              View all {watchlist.items.length} stocks
            </Button>
          </Link>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================
// Quick Stats Widget
// ============================================

interface QuickStat {
  label: string;
  value: string | number;
  change?: number;
  icon: typeof TrendingUp;
  color: string;
}

export function QuickStatsWidget({ stats }: { stats?: QuickStat[] }) {
  const defaultStats: QuickStat[] = stats || [
    { label: 'Positions', value: 12, icon: PieChart, color: 'text-emerald-400' },
    { label: 'Win Rate', value: '68%', icon: TrendingUp, color: 'text-blue-400' },
    { label: 'Active Alerts', value: 5, icon: Bell, color: 'text-yellow-400' },
    { label: 'Watchlist', value: 24, icon: Eye, color: 'text-purple-400' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {defaultStats.map((stat) => (
        <Card key={stat.label} className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <stat.icon className={cn('h-5 w-5', stat.color)} />
              {stat.change !== undefined && (
                <span className={cn(
                  'text-xs',
                  stat.change >= 0 ? 'text-emerald-400' : 'text-red-400'
                )}>
                  {stat.change >= 0 ? '+' : ''}{stat.change}%
                </span>
              )}
            </div>
            <p className="text-2xl font-bold text-white mt-2">{stat.value}</p>
            <p className="text-xs text-slate-400">{stat.label}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ============================================
// Activity Feed Widget
// ============================================

interface ActivityItem {
  id: string;
  type: 'buy' | 'sell' | 'alert' | 'thesis';
  ticker?: string;
  message: string;
  time: string;
}

export function ActivityFeedWidget({ activities }: { activities?: ActivityItem[] }) {
  const defaultActivities: ActivityItem[] = activities || [];

  if (defaultActivities.length === 0) {
    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
            <Activity className="h-4 w-4 text-cyan-400" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6">
            <Activity className="h-8 w-8 text-slate-600 mx-auto mb-2" />
            <p className="text-sm text-slate-500">No recent activity</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-slate-400 flex items-center gap-2">
          <Activity className="h-4 w-4 text-cyan-400" />
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {defaultActivities.map((activity) => (
            <div key={activity.id} className="flex items-start gap-3">
              <div className={cn(
                'p-1.5 rounded-full',
                activity.type === 'buy' && 'bg-emerald-500/20',
                activity.type === 'sell' && 'bg-red-500/20',
                activity.type === 'alert' && 'bg-yellow-500/20',
                activity.type === 'thesis' && 'bg-blue-500/20'
              )}>
                {activity.type === 'buy' && <TrendingUp className="h-3 w-3 text-emerald-400" />}
                {activity.type === 'sell' && <TrendingDown className="h-3 w-3 text-red-400" />}
                {activity.type === 'alert' && <Bell className="h-3 w-3 text-yellow-400" />}
                {activity.type === 'thesis' && <DollarSign className="h-3 w-3 text-blue-400" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white">{activity.message}</p>
                <p className="text-xs text-slate-500">{activity.time}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

