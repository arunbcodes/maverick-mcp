'use client';

import { useState, useMemo } from 'react';
import { useParams, useRouter, notFound } from 'next/navigation';
import {
  useStockQuote,
  useStockInfo,
  useStockHistory,
  useTechnicalIndicators,
  useAddPosition,
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
import { Skeleton } from '@/components/ui/loading';
import { ErrorState } from '@/components/ui/error';
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Plus,
  Activity,
  BarChart3,
  Target,
  X,
  Check,
} from 'lucide-react';
import {
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { formatCurrency, formatPercent, formatCompactNumber, cn } from '@/lib/utils';

type Period = '1W' | '1M' | '3M' | '1Y' | 'ALL';

export default function StockDetailPage() {
  const params = useParams();
  const router = useRouter();
  
  // Runtime validation for ticker param
  const tickerParam = params.ticker;
  if (!tickerParam || typeof tickerParam !== 'string') {
    notFound();
  }
  const ticker = tickerParam.toUpperCase();
  
  const [period, setPeriod] = useState<Period>('3M');
  const [showAddModal, setShowAddModal] = useState(false);

  // Calculate date range based on period
  const dateRange = useMemo(() => {
    const end = new Date();
    const start = new Date();
    switch (period) {
      case '1W':
        start.setDate(end.getDate() - 7);
        break;
      case '1M':
        start.setMonth(end.getMonth() - 1);
        break;
      case '3M':
        start.setMonth(end.getMonth() - 3);
        break;
      case '1Y':
        start.setFullYear(end.getFullYear() - 1);
        break;
      case 'ALL':
        start.setFullYear(end.getFullYear() - 5);
        break;
    }
    return {
      start_date: start.toISOString().split('T')[0],
      end_date: end.toISOString().split('T')[0],
    };
  }, [period]);

  // Fetch data
  const { data: quote, isLoading: quoteLoading, isError: quoteError } = useStockQuote(ticker);
  const { data: info, isLoading: infoLoading } = useStockInfo(ticker);
  const { data: history, isLoading: historyLoading } = useStockHistory(ticker, dateRange);
  const { data: technicals, isLoading: techLoading } = useTechnicalIndicators(ticker);

  const isLoading = quoteLoading || infoLoading;
  const isPositive = (quote?.change ?? 0) >= 0;

  // Prepare chart data - must be before any early returns
  const chartData = useMemo(() => {
    if (!history?.data) return [];
    return history.data.map((d) => ({
      date: d.date,
      price: d.close,
      volume: d.volume,
    }));
  }, [history]);

  // Error state - after all hooks
  if (quoteError) {
    return (
      <div className="space-y-6">
        <BackButton />
        <ErrorState
          title={`Stock not found: ${ticker}`}
          message="We couldn't find this stock. Please check the ticker symbol."
          onRetry={() => router.refresh()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back Navigation */}
      <BackButton />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div>
          {isLoading ? (
            <>
              <Skeleton className="h-10 w-32 mb-2" />
              <Skeleton className="h-6 w-48" />
            </>
          ) : (
            <>
              <div className="flex items-center space-x-3">
                <h1 className="text-3xl font-bold text-white">{ticker}</h1>
                {info?.sector && (
                  <span className="px-2 py-1 text-xs rounded-full bg-slate-800 text-slate-400">
                    {info.sector}
                  </span>
                )}
              </div>
              <p className="text-slate-400 mt-1">{info?.name || 'Loading...'}</p>
            </>
          )}
        </div>

        <div className="flex items-center space-x-4">
          {/* Price */}
          <div className="text-right">
            {isLoading ? (
              <Skeleton className="h-10 w-24" />
            ) : (
              <>
                <p className="text-3xl font-bold text-white">
                  {formatCurrency(quote?.price ?? 0)}
                </p>
                <div
                  className={cn(
                    'flex items-center justify-end space-x-1',
                    isPositive ? 'text-emerald-400' : 'text-red-400'
                  )}
                >
                  {isPositive ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                  <span>
                    {formatCurrency(Math.abs(quote?.change ?? 0))} (
                    {formatPercent(quote?.change_percent ?? 0)})
                  </span>
                </div>
              </>
            )}
          </div>

          {/* Add to Portfolio */}
          <Button
            onClick={() => setShowAddModal(true)}
            className="bg-emerald-600 hover:bg-emerald-500 text-white"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add to Portfolio
          </Button>
        </div>
      </div>

      {/* Price Chart */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-white">Price History</CardTitle>
          <div className="flex space-x-1">
            {(['1W', '1M', '3M', '1Y', 'ALL'] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={cn(
                  'px-3 py-1 text-xs rounded-md transition-colors',
                  period === p
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                )}
              >
                {p}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <Skeleton className="h-[300px] w-full" />
          ) : chartData.length > 0 ? (
            <PriceChart data={chartData} isPositive={isPositive} />
          ) : (
            <div className="flex items-center justify-center h-[300px] text-slate-500">
              No price data available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Technical Indicators Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* RSI */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-sm flex items-center">
              <Activity className="h-4 w-4 mr-2 text-emerald-400" />
              RSI (14)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {techLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : technicals?.rsi ? (
              <RSIGauge value={technicals.rsi.value} signal={technicals.rsi.signal} />
            ) : (
              <p className="text-slate-500 text-sm">No data</p>
            )}
          </CardContent>
        </Card>

        {/* MACD */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-sm flex items-center">
              <BarChart3 className="h-4 w-4 mr-2 text-emerald-400" />
              MACD
            </CardTitle>
          </CardHeader>
          <CardContent>
            {techLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : technicals?.macd ? (
              <MACDDisplay macd={technicals.macd} />
            ) : (
              <p className="text-slate-500 text-sm">No data</p>
            )}
          </CardContent>
        </Card>

        {/* Moving Averages */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-sm flex items-center">
              <TrendingUp className="h-4 w-4 mr-2 text-emerald-400" />
              Moving Averages
            </CardTitle>
          </CardHeader>
          <CardContent>
            {techLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : technicals?.moving_averages ? (
              <MovingAveragesDisplay
                ma={technicals.moving_averages}
                currentPrice={quote?.price ?? 0}
              />
            ) : (
              <p className="text-slate-500 text-sm">No data</p>
            )}
          </CardContent>
        </Card>

        {/* Support/Resistance */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-sm flex items-center">
              <Target className="h-4 w-4 mr-2 text-emerald-400" />
              Support / Resistance
            </CardTitle>
          </CardHeader>
          <CardContent>
            {techLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : technicals?.support_resistance ? (
              <SupportResistanceDisplay sr={technicals.support_resistance} />
            ) : (
              <p className="text-slate-500 text-sm">No data</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Stock Info */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white">Company Info</CardTitle>
        </CardHeader>
        <CardContent>
          {infoLoading ? (
            <div className="grid gap-4 md:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : info ? (
            <div className="grid gap-4 md:grid-cols-4">
              <InfoItem label="Market Cap" value={formatCompactNumber(info.market_cap ?? 0)} />
              <InfoItem label="P/E Ratio" value={info.pe_ratio?.toFixed(2) ?? 'N/A'} />
              <InfoItem label="52W High" value={formatCurrency(info.fifty_two_week_high ?? 0)} />
              <InfoItem label="52W Low" value={formatCurrency(info.fifty_two_week_low ?? 0)} />
              <InfoItem label="Avg Volume" value={formatCompactNumber(info.avg_volume ?? 0)} />
              <InfoItem label="Dividend Yield" value={info.dividend_yield ? `${(info.dividend_yield * 100).toFixed(2)}%` : 'N/A'} />
              <InfoItem label="Sector" value={info.sector ?? 'N/A'} />
              <InfoItem label="Industry" value={info.industry ?? 'N/A'} />
            </div>
          ) : (
            <p className="text-slate-500">No company information available</p>
          )}
        </CardContent>
      </Card>

      {/* Quick Add Modal */}
      {showAddModal && (
        <QuickAddModal
          ticker={ticker}
          currentPrice={quote?.price ?? 0}
          onClose={() => setShowAddModal(false)}
        />
      )}
    </div>
  );
}

function BackButton() {
  const router = useRouter();
  return (
    <Button
      variant="ghost"
      className="text-slate-400 hover:text-white -ml-2"
      onClick={() => router.back()}
    >
      <ArrowLeft className="h-4 w-4 mr-2" />
      Back
    </Button>
  );
}

function PriceChart({ data, isPositive }: { data: { date: string; price: number }[]; isPositive: boolean }) {
  const color = isPositive ? '#22c55e' : '#ef4444';
  
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
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
          tickFormatter={(value) => `$${value.toFixed(0)}`}
          domain={['auto', 'auto']}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
          }}
          labelStyle={{ color: '#94a3b8' }}
          formatter={(value: number) => [formatCurrency(value), 'Price']}
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
          dataKey="price"
          stroke={color}
          strokeWidth={2}
          fill="url(#priceGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

function RSIGauge({ value, signal }: { value: number; signal: string }) {
  const getColor = () => {
    if (value >= 70) return 'text-red-400';
    if (value <= 30) return 'text-emerald-400';
    return 'text-slate-400';
  };

  return (
    <div>
      <div className="flex items-end justify-between">
        <span className={cn('text-3xl font-bold', getColor())}>{value.toFixed(1)}</span>
        <span
          className={cn(
            'text-xs px-2 py-1 rounded capitalize',
            signal === 'oversold' && 'bg-emerald-900/50 text-emerald-400',
            signal === 'overbought' && 'bg-red-900/50 text-red-400',
            signal === 'neutral' && 'bg-slate-800 text-slate-400'
          )}
        >
          {signal}
        </span>
      </div>
      {/* Gauge bar */}
      <div className="mt-2 h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all', getColor().replace('text-', 'bg-'))}
          style={{ width: `${value}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-slate-600 mt-1">
        <span>0</span>
        <span>30</span>
        <span>70</span>
        <span>100</span>
      </div>
    </div>
  );
}

function MACDDisplay({ macd }: { macd: { macd_line: number; signal_line: number; histogram: number; signal: string } }) {
  const isPositive = macd.histogram >= 0;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">MACD</span>
        <span className="text-white">{macd.macd_line.toFixed(3)}</span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">Signal</span>
        <span className="text-white">{macd.signal_line.toFixed(3)}</span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">Histogram</span>
        <span className={isPositive ? 'text-emerald-400' : 'text-red-400'}>
          {macd.histogram.toFixed(3)}
        </span>
      </div>
      <div
        className={cn(
          'text-xs px-2 py-1 rounded text-center capitalize mt-2',
          macd.signal === 'bullish' && 'bg-emerald-900/50 text-emerald-400',
          macd.signal === 'bearish' && 'bg-red-900/50 text-red-400',
          macd.signal === 'neutral' && 'bg-slate-800 text-slate-400'
        )}
      >
        {macd.signal}
      </div>
    </div>
  );
}

function MovingAveragesDisplay({
  ma,
  currentPrice,
}: {
  ma: { sma_20: number; sma_50: number; sma_200: number; trend: string };
  currentPrice: number;
}) {
  const getPosition = (maValue: number) => {
    if (currentPrice > maValue) return { label: 'Above', color: 'text-emerald-400' };
    return { label: 'Below', color: 'text-red-400' };
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">SMA 20</span>
        <span className={getPosition(ma.sma_20).color}>
          {formatCurrency(ma.sma_20)}
        </span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">SMA 50</span>
        <span className={getPosition(ma.sma_50).color}>
          {formatCurrency(ma.sma_50)}
        </span>
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">SMA 200</span>
        <span className={getPosition(ma.sma_200).color}>
          {formatCurrency(ma.sma_200)}
        </span>
      </div>
      <div
        className={cn(
          'text-xs px-2 py-1 rounded text-center capitalize mt-2',
          ma.trend === 'bullish' && 'bg-emerald-900/50 text-emerald-400',
          ma.trend === 'bearish' && 'bg-red-900/50 text-red-400',
          ma.trend === 'neutral' && 'bg-slate-800 text-slate-400'
        )}
      >
        {ma.trend} Trend
      </div>
    </div>
  );
}

function SupportResistanceDisplay({
  sr,
}: {
  sr: { support_levels: number[]; resistance_levels: number[]; current_price: number };
}) {
  const nearestSupport = sr.support_levels[0];
  const nearestResistance = sr.resistance_levels[0];

  return (
    <div className="space-y-3">
      <div>
        <p className="text-xs text-slate-500 mb-1">Resistance</p>
        <div className="flex flex-wrap gap-1">
          {sr.resistance_levels.slice(0, 2).map((level, i) => (
            <span key={i} className="px-2 py-1 text-xs rounded bg-red-900/30 text-red-400">
              {formatCurrency(level)}
            </span>
          ))}
        </div>
      </div>
      <div className="h-px bg-slate-700" />
      <div>
        <p className="text-xs text-slate-500 mb-1">Support</p>
        <div className="flex flex-wrap gap-1">
          {sr.support_levels.slice(0, 2).map((level, i) => (
            <span key={i} className="px-2 py-1 text-xs rounded bg-emerald-900/30 text-emerald-400">
              {formatCurrency(level)}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-lg bg-slate-800/50">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-white font-medium mt-1">{value}</p>
    </div>
  );
}

function QuickAddModal({
  ticker,
  currentPrice,
  onClose,
}: {
  ticker: string;
  currentPrice: number;
  onClose: () => void;
}) {
  const [shares, setShares] = useState('');
  const [price, setPrice] = useState(currentPrice.toString());
  const [error, setError] = useState('');
  const addPosition = useAddPosition();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const sharesNum = parseFloat(shares);
    const priceNum = parseFloat(price);

    if (isNaN(sharesNum) || sharesNum <= 0) {
      setError('Please enter a valid number of shares');
      return;
    }

    try {
      await addPosition.mutateAsync({
        ticker,
        shares: sharesNum,
        purchase_price: priceNum,
      });
      onClose();
      router.push('/portfolio');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add position');
    }
  };

  const totalValue = (parseFloat(shares) || 0) * (parseFloat(price) || 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <Card className="relative z-10 w-full max-w-sm mx-4 bg-slate-900 border-slate-800 animate-fade-in">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-white">Add {ticker}</CardTitle>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5 text-slate-400" />
          </Button>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-md bg-red-900/20 border border-red-800 text-red-400 text-sm">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Shares</label>
              <Input
                type="number"
                step="0.001"
                value={shares}
                onChange={(e) => setShares(e.target.value)}
                placeholder="100"
                className="bg-slate-800 border-slate-700 text-white"
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Purchase Price</label>
              <Input
                type="number"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
            {shares && (
              <div className="p-3 rounded-lg bg-slate-800/50">
                <p className="text-xs text-slate-500">Total Value</p>
                <p className="text-white font-medium">{formatCurrency(totalValue)}</p>
              </div>
            )}
            <div className="flex space-x-3">
              <Button
                type="button"
                variant="outline"
                className="flex-1 border-slate-700 text-slate-300"
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white"
                isLoading={addPosition.isPending}
              >
                <Check className="h-4 w-4 mr-2" />
                Add
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

