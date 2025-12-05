'use client';

import { useState } from 'react';
import {
  Lightbulb,
  TrendingUp,
  AlertTriangle,
  Target,
  ChevronDown,
  ChevronUp,
  Loader2,
  Sparkles,
  RefreshCw,
  CheckCircle,
  Info,
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
import { useLazyStockExplanation } from '@/lib/api/hooks';
import type { StockExplanation, InvestorPersona, ConfidenceLevel } from '@/lib/api/types';

interface StockExplanationButtonProps {
  ticker: string;
  strategy?: string;
  persona?: InvestorPersona;
  className?: string;
}

/**
 * "Why this stock?" button that triggers AI explanation
 */
export function StockExplanationButton({
  ticker,
  strategy = 'maverick',
  persona,
  className,
}: StockExplanationButtonProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const { mutate: fetch, data, isPending, isError, error } = useLazyStockExplanation(
    strategy,
    ticker,
    { persona }
  );

  const handleClick = () => {
    if (!data && !isPending) {
      fetch();
    }
    setShowExplanation(!showExplanation);
  };

  return (
    <div className={cn('space-y-2', className)}>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleClick}
        className="text-xs text-muted-foreground hover:text-primary"
      >
        {isPending ? (
          <>
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Sparkles className="mr-1 h-3 w-3" />
            Why this stock?
            {showExplanation ? (
              <ChevronUp className="ml-1 h-3 w-3" />
            ) : (
              <ChevronDown className="ml-1 h-3 w-3" />
            )}
          </>
        )}
      </Button>

      {showExplanation && (
        <div className="animate-in slide-in-from-top-2 duration-200">
          {isError ? (
            <ExplanationError error={error} onRetry={() => fetch()} />
          ) : data ? (
            <ExplanationPanel explanation={data} />
          ) : isPending ? (
            <ExplanationSkeleton />
          ) : null}
        </div>
      )}
    </div>
  );
}

interface ExplanationPanelProps {
  explanation: StockExplanation;
  className?: string;
}

/**
 * Expandable panel showing AI-generated explanation
 */
export function ExplanationPanel({ explanation, className }: ExplanationPanelProps) {
  const confidenceColor = getConfidenceColor(explanation.confidence);
  
  return (
    <Card className={cn('border-l-4', confidenceColor.border, className)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-yellow-500" />
            AI Analysis
          </CardTitle>
          <div className="flex items-center gap-2">
            <ConfidenceBadge confidence={explanation.confidence} />
            {explanation.cached && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <CheckCircle className="h-3 w-3" />
                Cached
              </span>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Summary */}
        <div>
          <p className="text-sm leading-relaxed">{explanation.summary}</p>
        </div>

        {/* Technical Setup */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            Technical Setup
          </h4>
          <p className="text-sm text-muted-foreground">{explanation.technical_setup}</p>
        </div>

        {/* Key Signals */}
        {explanation.key_signals.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              Key Signals
            </h4>
            <ul className="space-y-1">
              {explanation.key_signals.map((signal, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-green-500 mt-1">•</span>
                  {signal}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Support/Resistance */}
        {explanation.support_resistance && (
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-1">
              <Target className="h-3 w-3" />
              Key Levels
            </h4>
            <p className="text-sm text-muted-foreground">{explanation.support_resistance}</p>
          </div>
        )}

        {/* Risk Factors */}
        {explanation.risk_factors.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1">
              <AlertTriangle className="h-3 w-3 text-yellow-500" />
              Risk Factors
            </h4>
            <ul className="space-y-1">
              {explanation.risk_factors.map((risk, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <span className="text-yellow-500 mt-1">•</span>
                  {risk}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Disclaimer */}
        <p className="text-xs text-muted-foreground italic border-t pt-2 mt-2 flex items-start gap-1">
          <Info className="h-3 w-3 mt-0.5 flex-shrink-0" />
          AI-generated analysis for educational purposes. Not investment advice.
        </p>
      </CardContent>
    </Card>
  );
}

interface ConfidenceBadgeProps {
  confidence: ConfidenceLevel;
}

function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  const config = getConfidenceColor(confidence);
  
  return (
    <span
      className={cn(
        'text-xs px-2 py-0.5 rounded-full font-medium',
        config.bg,
        config.text
      )}
    >
      {confidence.charAt(0).toUpperCase() + confidence.slice(1)} Confidence
    </span>
  );
}

function getConfidenceColor(confidence: ConfidenceLevel) {
  switch (confidence) {
    case 'high':
      return {
        border: 'border-l-green-500',
        bg: 'bg-green-500/10',
        text: 'text-green-600',
      };
    case 'medium':
      return {
        border: 'border-l-yellow-500',
        bg: 'bg-yellow-500/10',
        text: 'text-yellow-600',
      };
    case 'low':
      return {
        border: 'border-l-red-500',
        bg: 'bg-red-500/10',
        text: 'text-red-600',
      };
  }
}

function ExplanationSkeleton() {
  return (
    <Card className="border-l-4 border-l-muted animate-pulse">
      <CardHeader className="pb-2">
        <div className="h-4 w-24 bg-muted rounded" />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-2">
          <div className="h-3 w-full bg-muted rounded" />
          <div className="h-3 w-4/5 bg-muted rounded" />
        </div>
        <div className="space-y-2">
          <div className="h-3 w-20 bg-muted rounded" />
          <div className="h-3 w-3/4 bg-muted rounded" />
        </div>
        <div className="space-y-2">
          <div className="h-3 w-16 bg-muted rounded" />
          <div className="h-3 w-2/3 bg-muted rounded" />
          <div className="h-3 w-1/2 bg-muted rounded" />
        </div>
      </CardContent>
    </Card>
  );
}

interface ExplanationErrorProps {
  error: Error | null;
  onRetry: () => void;
}

function ExplanationError({ error, onRetry }: ExplanationErrorProps) {
  return (
    <Card className="border-l-4 border-l-red-500">
      <CardContent className="py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-red-500">
            <AlertTriangle className="h-4 w-4" />
            {error?.message || 'Failed to generate explanation'}
          </div>
          <Button variant="ghost" size="sm" onClick={onRetry}>
            <RefreshCw className="h-3 w-3 mr-1" />
            Retry
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Compact inline explanation preview
 */
export function InlineExplanation({
  explanation,
  className,
}: {
  explanation: StockExplanation;
  className?: string;
}) {
  return (
    <div className={cn('text-sm text-muted-foreground', className)}>
      <p className="line-clamp-2">{explanation.summary}</p>
    </div>
  );
}

