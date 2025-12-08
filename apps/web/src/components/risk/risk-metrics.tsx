'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/loading';
import { cn } from '@/lib/utils';
import {
  useCalculateFullRiskMetrics,
  useRunStressTests,
  useRunCustomStressTest,
  getRiskLevelColor,
  getRiskLevelBadge,
  getBetaColor,
  formatPercent,
  formatAmount,
  type RiskMetricsSummary,
  type VaRResult,
  type BetaResult,
  type VolatilityResult,
  type StressTestResult,
  type RiskLevel,
} from '@/lib/api/hooks/use-risk';
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity,
  Shield,
  Zap,
  Info,
  Play,
  BarChart2,
  Target,
} from 'lucide-react';

// ============================================
// Main Risk Metrics Card
// ============================================

interface RiskMetricsCardProps {
  portfolioReturns?: number[];
  portfolioValue: number;
  className?: string;
}

export function RiskMetricsCard({
  portfolioReturns,
  portfolioValue,
  className,
}: RiskMetricsCardProps) {
  const calculateMetrics = useCalculateFullRiskMetrics();
  const [metrics, setMetrics] = useState<RiskMetricsSummary | null>(null);

  // Generate sample returns if not provided
  const returns = useMemo(() => {
    if (portfolioReturns && portfolioReturns.length >= 20) {
      return portfolioReturns;
    }
    // Generate sample returns for demo
    const sampleReturns: number[] = [];
    for (let i = 0; i < 252; i++) {
      sampleReturns.push((Math.random() - 0.48) * 0.03); // ~10% annual return
    }
    return sampleReturns;
  }, [portfolioReturns]);

  const handleCalculate = async () => {
    const result = await calculateMetrics.mutateAsync({
      portfolioReturns: returns,
      portfolioValue,
    });
    if (result) {
      setMetrics(result);
    }
  };

  return (
    <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
            <Shield className="h-4 w-4 text-purple-400" />
            Risk Metrics
          </CardTitle>
          <Button
            size="sm"
            onClick={handleCalculate}
            disabled={calculateMetrics.isPending}
            className="h-7 bg-purple-600 hover:bg-purple-500"
          >
            {calculateMetrics.isPending ? (
              <Activity className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Play className="h-3 w-3 mr-1" />
                Calculate
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {metrics ? (
          <RiskMetricsDisplay metrics={metrics} />
        ) : (
          <div className="text-center py-8">
            <Shield className="h-12 w-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">
              Click Calculate to analyze portfolio risk metrics
            </p>
            <p className="text-slate-500 text-xs mt-1">
              VaR, Beta, Volatility, and Stress Testing
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================
// Risk Metrics Display
// ============================================

function RiskMetricsDisplay({ metrics }: { metrics: RiskMetricsSummary }) {
  return (
    <div className="space-y-4">
      {/* Risk Score */}
      <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50">
        <div>
          <p className="text-xs text-slate-500">Overall Risk Score</p>
          <div className="flex items-center gap-2 mt-1">
            <span className={cn('text-2xl font-bold font-mono', getRiskLevelColor(metrics.risk_level))}>
              {metrics.risk_score.toFixed(0)}
            </span>
            <Badge variant="outline" className={cn('text-xs', getRiskLevelBadge(metrics.risk_level))}>
              {formatRiskLevel(metrics.risk_level)}
            </Badge>
          </div>
        </div>
        <RiskScoreGauge score={metrics.risk_score} level={metrics.risk_level} />
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 gap-3">
        <VaRCard var={metrics.var} />
        <BetaCard beta={metrics.beta} />
        <VolatilityCard volatility={metrics.volatility} />
        <StressTestSummary stressTests={metrics.stress_tests} />
      </div>
    </div>
  );
}

// ============================================
// Risk Score Gauge
// ============================================

function RiskScoreGauge({ score, level }: { score: number; level: RiskLevel }) {
  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;

  const getStrokeColor = (level: RiskLevel) => {
    switch (level) {
      case 'low': return '#10b981';
      case 'moderate': return '#eab308';
      case 'high': return '#f97316';
      case 'very_high': return '#ef4444';
      default: return '#64748b';
    }
  };

  return (
    <div className="relative w-16 h-16">
      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 70 70">
        <circle
          cx="35"
          cy="35"
          r={radius}
          stroke="currentColor"
          strokeWidth="4"
          fill="none"
          className="text-slate-700"
        />
        <circle
          cx="35"
          cy="35"
          r={radius}
          stroke={getStrokeColor(level)}
          strokeWidth="4"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
        />
      </svg>
    </div>
  );
}

// ============================================
// VaR Card
// ============================================

function VaRCard({ var: varResult }: { var: VaRResult }) {
  return (
    <div className="p-3 rounded-lg bg-slate-900/50">
      <div className="flex items-center gap-1 mb-2">
        <AlertTriangle className="h-3 w-3 text-amber-400" />
        <span className="text-xs text-slate-400">Value at Risk</span>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between">
          <span className="text-xs text-slate-500">95% VaR</span>
          <span className="text-xs font-mono text-amber-400">
            {formatPercent(Math.abs(varResult.var_95))}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-xs text-slate-500">99% VaR</span>
          <span className="text-xs font-mono text-red-400">
            {formatPercent(Math.abs(varResult.var_99))}
          </span>
        </div>
        <div className="flex justify-between pt-1 border-t border-slate-700">
          <span className="text-xs text-slate-500">Max Daily Loss</span>
          <span className="text-xs font-mono text-white">
            {formatAmount(varResult.var_95_amount)}
          </span>
        </div>
      </div>
    </div>
  );
}

// ============================================
// Beta Card
// ============================================

function BetaCard({ beta }: { beta: BetaResult }) {
  return (
    <div className="p-3 rounded-lg bg-slate-900/50">
      <div className="flex items-center gap-1 mb-2">
        <BarChart2 className="h-3 w-3 text-blue-400" />
        <span className="text-xs text-slate-400">Portfolio Beta</span>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between items-center">
          <span className="text-xs text-slate-500">Beta</span>
          <span className={cn('text-lg font-mono font-bold', getBetaColor(beta.beta))}>
            {beta.beta.toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-xs text-slate-500">R²</span>
          <span className="text-xs font-mono text-slate-300">
            {(beta.r_squared * 100).toFixed(0)}%
          </span>
        </div>
        <p className="text-[10px] text-slate-500 pt-1 line-clamp-2">
          {beta.interpretation}
        </p>
      </div>
    </div>
  );
}

// ============================================
// Volatility Card
// ============================================

function VolatilityCard({ volatility }: { volatility: VolatilityResult }) {
  return (
    <div className="p-3 rounded-lg bg-slate-900/50">
      <div className="flex items-center gap-1 mb-2">
        <Activity className="h-3 w-3 text-purple-400" />
        <span className="text-xs text-slate-400">Volatility</span>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between">
          <span className="text-xs text-slate-500">Annual</span>
          <span className="text-xs font-mono text-purple-400">
            {formatPercent(volatility.annualized_volatility)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-xs text-slate-500">Downside</span>
          <span className="text-xs font-mono text-red-400">
            {formatPercent(volatility.downside_volatility)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-xs text-slate-500">Upside</span>
          <span className="text-xs font-mono text-emerald-400">
            {formatPercent(volatility.upside_volatility)}
          </span>
        </div>
      </div>
    </div>
  );
}

// ============================================
// Stress Test Summary
// ============================================

function StressTestSummary({ stressTests }: { stressTests: StressTestResult[] }) {
  const worstCase = stressTests[0]; // Already sorted by severity
  
  return (
    <div className="p-3 rounded-lg bg-slate-900/50">
      <div className="flex items-center gap-1 mb-2">
        <Zap className="h-3 w-3 text-red-400" />
        <span className="text-xs text-slate-400">Stress Test</span>
      </div>
      {worstCase && (
        <div className="space-y-1">
          <p className="text-xs text-white font-medium">{worstCase.scenario_name}</p>
          <div className="flex justify-between">
            <span className="text-xs text-slate-500">Est. Loss</span>
            <span className="text-xs font-mono text-red-400">
              {formatPercent(Math.abs(worstCase.estimated_portfolio_loss))}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-xs text-slate-500">Amount</span>
            <span className="text-xs font-mono text-white">
              {formatAmount(worstCase.estimated_loss_amount)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================
// Stress Test Card (Full)
// ============================================

export function StressTestCard({
  portfolioBeta = 1.0,
  portfolioValue,
  className,
}: {
  portfolioBeta?: number;
  portfolioValue: number;
  className?: string;
}) {
  const runStressTests = useRunStressTests();
  const runCustomTest = useRunCustomStressTest();
  const [results, setResults] = useState<StressTestResult[]>([]);
  const [customDrop, setCustomDrop] = useState('');

  const handleRunAll = async () => {
    const result = await runStressTests.mutateAsync({
      portfolioBeta,
      portfolioValue,
    });
    if (result) {
      setResults(result);
    }
  };

  const handleCustomTest = async () => {
    const dropPercent = parseFloat(customDrop);
    if (isNaN(dropPercent) || dropPercent <= 0) return;

    const result = await runCustomTest.mutateAsync({
      portfolioBeta,
      portfolioValue,
      marketDropPercent: dropPercent,
      scenarioName: `${dropPercent}% Drop`,
    });
    if (result) {
      setResults(prev => [result, ...prev]);
    }
    setCustomDrop('');
  };

  return (
    <Card className={cn('bg-slate-800/50 border-slate-700', className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
            <Zap className="h-4 w-4 text-red-400" />
            Stress Testing
          </CardTitle>
          <Button
            size="sm"
            onClick={handleRunAll}
            disabled={runStressTests.isPending}
            className="h-7 bg-red-600 hover:bg-red-500"
          >
            {runStressTests.isPending ? (
              <Activity className="h-4 w-4 animate-spin" />
            ) : (
              'Run All Scenarios'
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Custom Test */}
        <div className="flex gap-2">
          <Input
            type="number"
            placeholder="Custom drop %"
            value={customDrop}
            onChange={(e) => setCustomDrop(e.target.value)}
            className="h-8 bg-slate-900 border-slate-700"
          />
          <Button
            size="sm"
            variant="outline"
            onClick={handleCustomTest}
            disabled={!customDrop || runCustomTest.isPending}
            className="h-8 border-slate-600"
          >
            Test
          </Button>
        </div>

        {/* Results */}
        {results.length > 0 ? (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {results.map((result, i) => (
              <StressTestRow key={`${result.scenario}-${i}`} result={result} />
            ))}
          </div>
        ) : (
          <div className="text-center py-4 text-slate-500 text-sm">
            Run stress tests to see potential losses
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function StressTestRow({ result }: { result: StressTestResult }) {
  return (
    <div className="flex items-center justify-between p-2 rounded bg-slate-900/50">
      <div>
        <p className="text-sm text-white">{result.scenario_name}</p>
        <p className="text-xs text-slate-500">{result.description}</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-mono text-red-400">
          -{formatPercent(Math.abs(result.estimated_portfolio_loss))}
        </p>
        <p className="text-xs text-slate-400">
          {formatAmount(result.estimated_loss_amount)}
        </p>
      </div>
    </div>
  );
}

// ============================================
// Utilities
// ============================================

function formatRiskLevel(level: RiskLevel): string {
  return level.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

