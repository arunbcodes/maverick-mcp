'use client';

import { useState, useMemo } from 'react';
import { usePortfolio, usePortfolioPositions } from '@/lib/api/hooks';
import {
  CorrelationHeatmap,
  DiversificationCard,
  SectorPieChart,
  SectorComparisonChart,
  SectorExposureTable,
  SectorRebalanceCard,
  RiskMetricsCard,
  StressTestCard,
} from '@/components/risk';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import {
  Shield,
  Grid3X3,
  PieChart,
  BarChart2,
  Activity,
  AlertTriangle,
  TrendingUp,
  Zap,
  RefreshCw,
} from 'lucide-react';

export default function RiskDashboardPage() {
  const [activeTab, setActiveTab] = useState('overview');
  
  // Fetch portfolio data
  const { data: portfolio, isLoading: portfolioLoading } = usePortfolio();
  const { data: positions, isLoading: positionsLoading } = usePortfolioPositions();

  // Process positions for risk components
  const processedPositions = useMemo(() => {
    if (!positions) return [];
    return positions.map(p => ({
      ticker: p.ticker,
      market_value: p.market_value || p.cost_basis || 0,
      sector: (p as { sector?: string }).sector || 'Unknown',
    }));
  }, [positions]);

  // Get tickers for correlation matrix
  const tickers = useMemo(() => {
    return processedPositions.map(p => p.ticker);
  }, [processedPositions]);

  // Portfolio value
  const portfolioValue = useMemo(() => {
    return portfolio?.total_value || processedPositions.reduce((sum, p) => sum + p.market_value, 0) || 10000;
  }, [portfolio, processedPositions]);

  // Check if we have data
  const hasPositions = processedPositions.length > 0;

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/20">
                <Shield className="h-6 w-6 text-purple-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Risk Analytics</h1>
                <p className="text-sm text-slate-400">
                  Portfolio risk analysis, correlation, and stress testing
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {portfolioLoading || positionsLoading ? (
                <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/30">
                  <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                  Loading
                </Badge>
              ) : hasPositions ? (
                <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                  {processedPositions.length} positions
                </Badge>
              ) : (
                <Badge variant="outline" className="bg-slate-500/10 text-slate-400 border-slate-500/30">
                  No positions
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-slate-800/50 border border-slate-700 p-1 mb-6">
            <TabsTrigger value="overview" className="data-[state=active]:bg-purple-600">
              <Activity className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="correlation" className="data-[state=active]:bg-purple-600">
              <Grid3X3 className="h-4 w-4 mr-2" />
              Correlation
            </TabsTrigger>
            <TabsTrigger value="sectors" className="data-[state=active]:bg-purple-600">
              <PieChart className="h-4 w-4 mr-2" />
              Sectors
            </TabsTrigger>
            <TabsTrigger value="metrics" className="data-[state=active]:bg-purple-600">
              <BarChart2 className="h-4 w-4 mr-2" />
              Metrics
            </TabsTrigger>
            <TabsTrigger value="stress" className="data-[state=active]:bg-purple-600">
              <Zap className="h-4 w-4 mr-2" />
              Stress Test
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <DiversificationCard
                positions={processedPositions}
                className="lg:col-span-1"
              />
              <Card className="bg-slate-800/50 border-slate-700 lg:col-span-2">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-400" />
                    Risk Alerts
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <RiskAlertsSummary positions={processedPositions} tickers={tickers} />
                </CardContent>
              </Card>
            </div>

            {/* Quick Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <SectorPieChart
                positions={processedPositions}
              />
              <RiskMetricsCard
                portfolioValue={portfolioValue}
              />
            </div>
          </TabsContent>

          {/* Correlation Tab */}
          <TabsContent value="correlation" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <CorrelationHeatmap
                tickers={tickers}
                className="lg:col-span-2"
              />
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
                    <Grid3X3 className="h-4 w-4 text-purple-400" />
                    About Correlation
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-sm text-slate-400">
                  <p>
                    Correlation measures how stocks move together. Values range from -1 to +1.
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded bg-red-500" />
                      <span>&gt; 0.7: High (limited diversification)</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded bg-yellow-500" />
                      <span>0.3-0.7: Moderate</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded bg-emerald-500" />
                      <span>&lt; 0.3: Low (good diversification)</span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-500">
                    Tip: Look for holdings with low correlation to reduce portfolio risk.
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Sectors Tab */}
          <TabsContent value="sectors" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <SectorPieChart
                positions={processedPositions}
              />
              <SectorComparisonChart
                positions={processedPositions}
              />
            </div>
            <SectorExposureTable
              positions={processedPositions}
            />
            <SectorRebalanceCard
              positions={processedPositions}
            />
          </TabsContent>

          {/* Metrics Tab */}
          <TabsContent value="metrics" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RiskMetricsCard
                portfolioValue={portfolioValue}
              />
              <DiversificationCard
                positions={processedPositions}
              />
            </div>
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-blue-400" />
                  Risk Metrics Guide
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                  <div className="p-3 rounded-lg bg-slate-900/50">
                    <h4 className="font-medium text-white mb-1">VaR (Value at Risk)</h4>
                    <p className="text-slate-400 text-xs">
                      Maximum expected loss at 95%/99% confidence. A 2% VaR means you will not lose more than 2% on 95 out of 100 days.
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900/50">
                    <h4 className="font-medium text-white mb-1">Beta</h4>
                    <p className="text-slate-400 text-xs">
                      Measures volatility vs market. Beta=1 means market-like risk. Beta&gt;1 is more volatile, Beta&lt;1 is less.
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900/50">
                    <h4 className="font-medium text-white mb-1">Volatility</h4>
                    <p className="text-slate-400 text-xs">
                      Standard deviation of returns. Higher volatility means larger price swings. Annualized vol is daily × √252.
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-900/50">
                    <h4 className="font-medium text-white mb-1">Sharpe Ratio</h4>
                    <p className="text-slate-400 text-xs">
                      Risk-adjusted return. Higher is better. Sharpe&gt;1 is good, Sharpe&gt;2 is excellent.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Stress Test Tab */}
          <TabsContent value="stress" className="space-y-6">
            <StressTestCard
              portfolioValue={portfolioValue}
            />
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
                  <Zap className="h-4 w-4 text-red-400" />
                  Historical Market Crashes
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className="text-left py-2 text-slate-500 font-normal">Event</th>
                        <th className="text-right py-2 text-slate-500 font-normal">S&P 500 Drop</th>
                        <th className="text-right py-2 text-slate-500 font-normal">Duration</th>
                        <th className="text-right py-2 text-slate-500 font-normal">Recovery</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { event: '2008 Financial Crisis', drop: '-57%', duration: '517 days', recovery: '~4 years' },
                        { event: 'Dot-Com Bubble (2000)', drop: '-49%', duration: '929 days', recovery: '~7 years' },
                        { event: 'COVID-19 Crash (2020)', drop: '-34%', duration: '33 days', recovery: '~6 months' },
                        { event: 'Black Monday (1987)', drop: '-22%', duration: '1 day', recovery: '~2 years' },
                        { event: 'Flash Crash (2010)', drop: '-9%', duration: '~1 hour', recovery: 'Same day' },
                      ].map(row => (
                        <tr key={row.event} className="border-b border-slate-700/50">
                          <td className="py-2 text-white">{row.event}</td>
                          <td className="py-2 text-right font-mono text-red-400">{row.drop}</td>
                          <td className="py-2 text-right text-slate-400">{row.duration}</td>
                          <td className="py-2 text-right text-slate-400">{row.recovery}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

// ============================================
// Risk Alerts Summary Component
// ============================================

function RiskAlertsSummary({
  positions,
  tickers,
}: {
  positions: { ticker: string; market_value: number; sector?: string }[];
  tickers: string[];
}) {
  // Calculate alerts based on current data
  const alerts = useMemo(() => {
    const alertList: { type: string; message: string; severity: 'low' | 'medium' | 'high' }[] = [];

    // Check for concentration
    const totalValue = positions.reduce((sum, p) => sum + p.market_value, 0);
    if (totalValue > 0) {
      const largest = positions.reduce((max, p) => 
        p.market_value > max.market_value ? p : max
      , positions[0]);
      
      if (largest) {
        const weight = (largest.market_value / totalValue) * 100;
        if (weight > 30) {
          alertList.push({
            type: 'concentration',
            message: `${largest.ticker} is ${weight.toFixed(0)}% of portfolio - high concentration risk`,
            severity: 'high',
          });
        } else if (weight > 20) {
          alertList.push({
            type: 'concentration',
            message: `${largest.ticker} is ${weight.toFixed(0)}% of portfolio - consider reducing`,
            severity: 'medium',
          });
        }
      }
    }

    // Check for position count
    if (positions.length < 5) {
      alertList.push({
        type: 'diversification',
        message: `Only ${positions.length} positions - consider adding more for diversification`,
        severity: positions.length < 3 ? 'high' : 'medium',
      });
    }

    // Check for sector concentration
    const sectorCounts: Record<string, number> = {};
    positions.forEach(p => {
      const sector = p.sector || 'Unknown';
      sectorCounts[sector] = (sectorCounts[sector] || 0) + p.market_value;
    });

    Object.entries(sectorCounts).forEach(([sector, value]) => {
      const weight = (value / totalValue) * 100;
      if (weight > 50 && sector !== 'Unknown') {
        alertList.push({
          type: 'sector',
          message: `${sector} is ${weight.toFixed(0)}% of portfolio - overweight`,
          severity: 'high',
        });
      }
    });

    return alertList;
  }, [positions]);

  if (alerts.length === 0) {
    return (
      <div className="text-center py-6">
        <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-3">
          <Shield className="h-6 w-6 text-emerald-400" />
        </div>
        <p className="text-emerald-400 font-medium">All Clear</p>
        <p className="text-sm text-slate-500 mt-1">No risk alerts at this time</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert, i) => (
        <div
          key={i}
          className={cn(
            'flex items-start gap-3 p-3 rounded-lg',
            alert.severity === 'high' ? 'bg-red-500/10 border border-red-500/20' :
            alert.severity === 'medium' ? 'bg-amber-500/10 border border-amber-500/20' :
            'bg-slate-500/10 border border-slate-500/20'
          )}
        >
          <AlertTriangle className={cn(
            'h-4 w-4 mt-0.5 flex-shrink-0',
            alert.severity === 'high' ? 'text-red-400' :
            alert.severity === 'medium' ? 'text-amber-400' : 'text-slate-400'
          )} />
          <div>
            <p className={cn(
              'text-sm',
              alert.severity === 'high' ? 'text-red-400' :
              alert.severity === 'medium' ? 'text-amber-400' : 'text-slate-400'
            )}>
              {alert.message}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

