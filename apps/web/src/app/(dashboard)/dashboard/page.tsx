'use client';

import { useAuth } from '@/lib/auth/auth-context';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
} from 'lucide-react';
import Link from 'next/link';
import { formatCurrency, formatPercent } from '@/lib/utils';

// Sample data - will be replaced with API calls
const portfolioSummary = {
  totalValue: 125750.42,
  dayChange: 1250.30,
  dayChangePercent: 1.01,
  totalGain: 15750.42,
  totalGainPercent: 14.32,
};

const topPositions = [
  { ticker: 'AAPL', name: 'Apple Inc.', value: 25000, change: 2.5, shares: 125 },
  { ticker: 'MSFT', name: 'Microsoft', value: 22500, change: -0.8, shares: 60 },
  { ticker: 'NVDA', name: 'NVIDIA', value: 20000, change: 4.2, shares: 25 },
  { ticker: 'GOOGL', name: 'Alphabet', value: 18000, change: 1.1, shares: 120 },
];

const marketOverview = [
  { name: 'S&P 500', value: 5234.18, change: 0.82 },
  { name: 'NASDAQ', value: 16543.25, change: 1.15 },
  { name: 'DOW', value: 39150.33, change: 0.45 },
];

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          Welcome back{user?.email ? `, ${user.email.split('@')[0]}` : ''}
        </h1>
        <p className="text-slate-400 mt-1">
          Here&apos;s what&apos;s happening with your portfolio today.
        </p>
      </div>

      {/* Portfolio Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Portfolio Value"
          value={formatCurrency(portfolioSummary.totalValue)}
          icon={<DollarSign className="h-5 w-5" />}
        />
        <SummaryCard
          title="Day Change"
          value={formatCurrency(portfolioSummary.dayChange)}
          change={portfolioSummary.dayChangePercent}
          icon={
            portfolioSummary.dayChange >= 0 ? (
              <TrendingUp className="h-5 w-5" />
            ) : (
              <TrendingDown className="h-5 w-5" />
            )
          }
        />
        <SummaryCard
          title="Total Gain"
          value={formatCurrency(portfolioSummary.totalGain)}
          change={portfolioSummary.totalGainPercent}
          icon={<BarChart3 className="h-5 w-5" />}
        />
        <SummaryCard
          title="Positions"
          value={topPositions.length.toString()}
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
            <div className="space-y-4">
              {topPositions.map((position) => (
                <div
                  key={position.ticker}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 rounded-lg bg-emerald-600/20 flex items-center justify-center">
                      <span className="text-emerald-400 font-semibold text-sm">
                        {position.ticker.slice(0, 2)}
                      </span>
                    </div>
                    <div>
                      <p className="text-white font-medium">{position.ticker}</p>
                      <p className="text-sm text-slate-400">{position.name}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-white font-medium">
                      {formatCurrency(position.value)}
                    </p>
                    <p
                      className={`text-sm flex items-center justify-end ${
                        position.change >= 0 ? 'text-emerald-400' : 'text-red-400'
                      }`}
                    >
                      {position.change >= 0 ? (
                        <ArrowUpRight className="h-4 w-4 mr-1" />
                      ) : (
                        <ArrowDownRight className="h-4 w-4 mr-1" />
                      )}
                      {formatPercent(position.change)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4">
              <Link href="/portfolio">
                <Button className="w-full bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 border border-emerald-600/30">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Position
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Market Overview */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="text-white">Market Overview</CardTitle>
            <CardDescription className="text-slate-400">
              Major indices today
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {marketOverview.map((index) => (
                <div
                  key={index.name}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50"
                >
                  <div>
                    <p className="text-white font-medium">{index.name}</p>
                    <p className="text-sm text-slate-400">
                      {index.value.toLocaleString()}
                    </p>
                  </div>
                  <div
                    className={`flex items-center px-2 py-1 rounded ${
                      index.change >= 0
                        ? 'bg-emerald-600/20 text-emerald-400'
                        : 'bg-red-600/20 text-red-400'
                    }`}
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
      </div>

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
  );
}

function SummaryCard({
  title,
  value,
  change,
  icon,
}: {
  title: string;
  value: string;
  change?: number;
  icon: React.ReactNode;
}) {
  return (
    <Card className="bg-slate-900/50 border-slate-800">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="p-2 rounded-lg bg-emerald-600/20 text-emerald-400">
            {icon}
          </div>
          {change !== undefined && (
            <span
              className={`text-sm ${
                change >= 0 ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {formatPercent(change)}
            </span>
          )}
        </div>
        <div className="mt-4">
          <p className="text-sm text-slate-400">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
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


