'use client';

import { useState } from 'react';
import {
  X,
  Loader2,
  FileText,
  TrendingUp,
  TrendingDown,
  Target,
  AlertTriangle,
  Zap,
  BarChart3,
  RefreshCw,
  CheckCircle,
  ArrowUpRight,
  ArrowDownRight,
  Shield,
  Flame,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { APIResponse, InvestorPersona } from '@/lib/api/types';

// Types matching backend
interface ThesisSection {
  title: string;
  content: string;
  bullet_points: string[];
}

interface InvestmentThesisResponse {
  ticker: string;
  company_name: string | null;
  generated_at: string;
  persona: string | null;
  summary: string;
  rating: string;
  risk_level: string;
  confidence: number;
  technical_setup: ThesisSection;
  fundamental_story: ThesisSection;
  catalysts: ThesisSection;
  risks: ThesisSection;
  current_price: string | null;
  price_target: string | null;
  stop_loss: string | null;
  upside_percent: number | null;
  peer_comparison: string[];
  data_sources: string[];
  cached: boolean;
  model_used: string | null;
}

interface ThesisModalProps {
  ticker: string;
  isOpen: boolean;
  onClose: () => void;
  persona?: InvestorPersona | null;
}

/**
 * Modal for displaying comprehensive investment thesis
 */
export function ThesisModal({ ticker, isOpen, onClose, persona }: ThesisModalProps) {
  const [thesis, setThesis] = useState<InvestmentThesisResponse | null>(null);

  const generateMutation = useMutation({
    mutationFn: async (forceRefresh: boolean = false) => {
      const params = new URLSearchParams();
      if (persona) params.set('persona', persona);
      if (forceRefresh) params.set('force_refresh', 'true');
      const queryString = params.toString();
      const url = `/ai-screening/thesis/${ticker}${queryString ? `?${queryString}` : ''}`;
      const response = await api.get<APIResponse<InvestmentThesisResponse>>(url);
      return response.data;
    },
    onSuccess: (data) => {
      setThesis(data);
    },
  });

  // Generate thesis when modal opens
  const handleOpen = () => {
    if (!thesis) {
      generateMutation.mutate(false);
    }
  };

  if (!isOpen) return null;

  // Trigger generation if not yet loaded
  if (!thesis && !generateMutation.isPending && !generateMutation.isError) {
    handleOpen();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-4xl max-h-[90vh] overflow-hidden bg-slate-900 rounded-xl border border-slate-700 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-900">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-600/20">
              <FileText className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                Investment Thesis: {ticker}
              </h2>
              {thesis?.company_name && (
                <p className="text-sm text-slate-400">{thesis.company_name}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {thesis && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => generateMutation.mutate(true)}
                disabled={generateMutation.isPending}
                className="text-slate-400"
              >
                <RefreshCw
                  className={cn('h-4 w-4 mr-1', generateMutation.isPending && 'animate-spin')}
                />
                Refresh
              </Button>
            )}
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-80px)] p-6 space-y-6">
          {generateMutation.isPending ? (
            <ThesisLoading />
          ) : generateMutation.isError ? (
            <ThesisError onRetry={() => generateMutation.mutate(false)} />
          ) : thesis ? (
            <ThesisContent thesis={thesis} />
          ) : null}
        </div>
      </div>
    </div>
  );
}

function ThesisContent({ thesis }: { thesis: InvestmentThesisResponse }) {
  const ratingConfig = getRatingConfig(thesis.rating);
  const riskConfig = getRiskConfig(thesis.risk_level);

  return (
    <>
      {/* Summary Card */}
      <Card className={cn('border-l-4', ratingConfig.border)}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white">Executive Summary</CardTitle>
            <div className="flex items-center gap-2">
              <RatingBadge rating={thesis.rating} />
              <RiskBadge risk={thesis.risk_level} />
              {thesis.cached && (
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Cached
                </span>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-slate-300 leading-relaxed">{thesis.summary}</p>
          
          {/* Price Targets */}
          {(thesis.price_target || thesis.stop_loss) && (
            <div className="mt-4 grid grid-cols-3 gap-4">
              {thesis.current_price && (
                <div className="p-3 rounded-lg bg-slate-800/50">
                  <p className="text-xs text-slate-500">Current Price</p>
                  <p className="text-lg font-semibold text-white">
                    ${parseFloat(thesis.current_price).toFixed(2)}
                  </p>
                </div>
              )}
              {thesis.price_target && (
                <div className="p-3 rounded-lg bg-emerald-500/10">
                  <p className="text-xs text-emerald-400 flex items-center gap-1">
                    <Target className="h-3 w-3" />
                    Price Target
                  </p>
                  <p className="text-lg font-semibold text-emerald-400">
                    ${parseFloat(thesis.price_target).toFixed(2)}
                    {thesis.upside_percent && (
                      <span className="text-sm ml-1">
                        ({thesis.upside_percent > 0 ? '+' : ''}{thesis.upside_percent.toFixed(1)}%)
                      </span>
                    )}
                  </p>
                </div>
              )}
              {thesis.stop_loss && (
                <div className="p-3 rounded-lg bg-red-500/10">
                  <p className="text-xs text-red-400 flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" />
                    Stop Loss
                  </p>
                  <p className="text-lg font-semibold text-red-400">
                    ${parseFloat(thesis.stop_loss).toFixed(2)}
                  </p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Technical Setup */}
        <SectionCard
          section={thesis.technical_setup}
          icon={<BarChart3 className="h-5 w-5 text-blue-400" />}
          color="blue"
        />

        {/* Fundamental Story */}
        <SectionCard
          section={thesis.fundamental_story}
          icon={<TrendingUp className="h-5 w-5 text-emerald-400" />}
          color="emerald"
        />

        {/* Catalysts */}
        <SectionCard
          section={thesis.catalysts}
          icon={<Zap className="h-5 w-5 text-yellow-400" />}
          color="yellow"
        />

        {/* Risks */}
        <SectionCard
          section={thesis.risks}
          icon={<AlertTriangle className="h-5 w-5 text-red-400" />}
          color="red"
        />
      </div>

      {/* Peer Comparison */}
      {thesis.peer_comparison.length > 0 && (
        <Card className="bg-slate-800/30 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-300">
              Peer Comparison
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {thesis.peer_comparison.map((point, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                  <span className="text-slate-500 mt-1">•</span>
                  {point}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-slate-500 pt-4 border-t border-slate-700">
        <div className="flex items-center gap-4">
          {thesis.generated_at && (
            <span>Generated: {new Date(thesis.generated_at).toLocaleString()}</span>
          )}
          {thesis.model_used && <span>Model: {thesis.model_used}</span>}
        </div>
        <div className="flex items-center gap-1">
          Confidence: {Math.round(thesis.confidence * 100)}%
        </div>
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-slate-600 italic">
        This AI-generated thesis is for educational purposes only and does not
        constitute investment advice. Always conduct your own research.
      </p>
    </>
  );
}

interface SectionCardProps {
  section: ThesisSection;
  icon: React.ReactNode;
  color: 'blue' | 'emerald' | 'yellow' | 'red';
}

function SectionCard({ section, icon, color }: SectionCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500/10 border-blue-500/30',
    emerald: 'bg-emerald-500/10 border-emerald-500/30',
    yellow: 'bg-yellow-500/10 border-yellow-500/30',
    red: 'bg-red-500/10 border-red-500/30',
  };

  return (
    <Card className={cn('border', colorClasses[color])}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
          {icon}
          {section.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-slate-300 leading-relaxed">{section.content}</p>
        {section.bullet_points.length > 0 && (
          <ul className="space-y-1">
            {section.bullet_points.map((point, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                <span className="text-slate-500 mt-1">•</span>
                {point}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function RatingBadge({ rating }: { rating: string }) {
  const config = getRatingConfig(rating);
  const Icon = config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold',
        config.bg,
        config.text
      )}
    >
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  );
}

function RiskBadge({ risk }: { risk: string }) {
  const config = getRiskConfig(risk);
  const Icon = config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium',
        config.bg,
        config.text
      )}
    >
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  );
}

function getRatingConfig(rating: string) {
  switch (rating) {
    case 'strong_buy':
      return {
        label: 'Strong Buy',
        icon: ArrowUpRight,
        bg: 'bg-emerald-500/20',
        text: 'text-emerald-400',
        border: 'border-l-emerald-500',
      };
    case 'buy':
      return {
        label: 'Buy',
        icon: TrendingUp,
        bg: 'bg-green-500/20',
        text: 'text-green-400',
        border: 'border-l-green-500',
      };
    case 'hold':
      return {
        label: 'Hold',
        icon: Target,
        bg: 'bg-yellow-500/20',
        text: 'text-yellow-400',
        border: 'border-l-yellow-500',
      };
    case 'sell':
      return {
        label: 'Sell',
        icon: TrendingDown,
        bg: 'bg-orange-500/20',
        text: 'text-orange-400',
        border: 'border-l-orange-500',
      };
    case 'strong_sell':
      return {
        label: 'Strong Sell',
        icon: ArrowDownRight,
        bg: 'bg-red-500/20',
        text: 'text-red-400',
        border: 'border-l-red-500',
      };
    default:
      return {
        label: 'Unknown',
        icon: Target,
        bg: 'bg-slate-500/20',
        text: 'text-slate-400',
        border: 'border-l-slate-500',
      };
  }
}

function getRiskConfig(risk: string) {
  switch (risk) {
    case 'low':
      return {
        label: 'Low Risk',
        icon: Shield,
        bg: 'bg-emerald-500/10',
        text: 'text-emerald-400',
      };
    case 'moderate':
      return {
        label: 'Moderate',
        icon: Target,
        bg: 'bg-yellow-500/10',
        text: 'text-yellow-400',
      };
    case 'high':
      return {
        label: 'High Risk',
        icon: AlertTriangle,
        bg: 'bg-orange-500/10',
        text: 'text-orange-400',
      };
    case 'very_high':
      return {
        label: 'Very High',
        icon: Flame,
        bg: 'bg-red-500/10',
        text: 'text-red-400',
      };
    default:
      return {
        label: 'Unknown',
        icon: Target,
        bg: 'bg-slate-500/10',
        text: 'text-slate-400',
      };
  }
}

function ThesisLoading() {
  return (
    <div className="flex flex-col items-center justify-center py-12 space-y-4">
      <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
      <div className="text-center">
        <p className="text-white font-medium">Generating Investment Thesis</p>
        <p className="text-sm text-slate-400">
          Analyzing technical, fundamental, and sentiment data...
        </p>
      </div>
      <div className="w-64 h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className="h-full bg-emerald-500 animate-pulse" style={{ width: '60%' }} />
      </div>
    </div>
  );
}

function ThesisError({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 space-y-4">
      <div className="p-3 rounded-full bg-red-500/20">
        <AlertTriangle className="h-8 w-8 text-red-400" />
      </div>
      <div className="text-center">
        <p className="text-white font-medium">Failed to Generate Thesis</p>
        <p className="text-sm text-slate-400">
          There was an error generating the analysis. Please try again.
        </p>
      </div>
      <Button onClick={onRetry} className="bg-emerald-600 hover:bg-emerald-700">
        <RefreshCw className="h-4 w-4 mr-2" />
        Try Again
      </Button>
    </div>
  );
}

/**
 * Button to trigger thesis modal
 */
export function GenerateThesisButton({
  ticker,
  persona,
  className,
}: {
  ticker: string;
  persona?: InvestorPersona | null;
  className?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        variant="outline"
        className={cn('border-emerald-600/50 text-emerald-400 hover:bg-emerald-600/10', className)}
      >
        <FileText className="h-4 w-4 mr-2" />
        Investment Thesis
      </Button>

      <ThesisModal
        ticker={ticker}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        persona={persona}
      />
    </>
  );
}

