'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Search,
  Sparkles,
  X,
  Loader2,
  ChevronRight,
  MessageSquare,
  Lightbulb,
  ArrowRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { APIResponse, InvestorPersona } from '@/lib/api/types';

// Types matching backend
interface ParsedQueryResponse {
  original_query: string;
  interpreted_as: string;
  intent: string;
  strategy: string;
  confidence: number;
  sectors: string[];
  tickers: string[];
  rsi_condition: string | null;
  sma_condition: string | null;
  volume_condition: string | null;
  filters: Record<string, unknown>;
  suggested_persona: string | null;
}

interface QuerySuggestion {
  query: string;
  description: string;
  category: string;
}

interface NLSearchBarProps {
  onSearchResult?: (result: ParsedQueryResponse) => void;
  onStrategyChange?: (strategy: string) => void;
  onFiltersExtracted?: (filters: Record<string, unknown>) => void;
  className?: string;
  placeholder?: string;
}

/**
 * AI-powered natural language search bar for stock screening
 */
export function NLSearchBar({
  onSearchResult,
  onStrategyChange,
  onFiltersExtracted,
  className,
  placeholder = 'Ask AI: "Find tech stocks with strong momentum"',
}: NLSearchBarProps) {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [lastResult, setLastResult] = useState<ParsedQueryResponse | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Fetch suggestions
  const { data: suggestions } = useQuery({
    queryKey: ['nl-suggestions', query],
    queryFn: async () => {
      const response = await api.get<APIResponse<QuerySuggestion[]>>(
        `/ai-screening/search/suggestions?q=${encodeURIComponent(query)}`
      );
      return response.data;
    },
    enabled: showSuggestions && query.length < 3, // Only fetch when showing dropdown with short query
    staleTime: 5 * 60 * 1000,
  });

  // Parse query mutation
  const searchMutation = useMutation({
    mutationFn: async (searchQuery: string) => {
      const response = await api.post<APIResponse<ParsedQueryResponse>>(
        '/ai-screening/search',
        { query: searchQuery }
      );
      return response.data;
    },
    onSuccess: (data) => {
      setLastResult(data);
      setShowResult(true);
      setShowSuggestions(false);
      
      // Notify parent components
      onSearchResult?.(data);
      if (data.strategy) {
        onStrategyChange?.(data.strategy);
      }
      if (data.filters) {
        onFiltersExtracted?.(data.filters);
      }
    },
  });

  // Refine query mutation
  const refineMutation = useMutation({
    mutationFn: async ({ currentQuery, refinement }: { currentQuery: string; refinement: string }) => {
      const response = await api.post<APIResponse<ParsedQueryResponse>>(
        '/ai-screening/search/refine',
        { current_query: currentQuery, refinement }
      );
      return response.data;
    },
    onSuccess: (data) => {
      setLastResult(data);
      setQuery('');
      
      onSearchResult?.(data);
      if (data.strategy) {
        onStrategyChange?.(data.strategy);
      }
      if (data.filters) {
        onFiltersExtracted?.(data.filters);
      }
    },
  });

  // Handle search submission
  const handleSearch = useCallback(() => {
    if (!query.trim()) return;
    
    if (lastResult) {
      // Refine existing query
      refineMutation.mutate({
        currentQuery: lastResult.original_query,
        refinement: query,
      });
    } else {
      // New search
      searchMutation.mutate(query);
    }
  }, [query, lastResult, searchMutation, refineMutation]);

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: QuerySuggestion) => {
    setQuery(suggestion.query);
    searchMutation.mutate(suggestion.query);
  };

  // Clear search
  const handleClear = () => {
    setQuery('');
    setLastResult(null);
    setShowResult(false);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isLoading = searchMutation.isPending || refineMutation.isPending;

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      {/* Search Input */}
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-emerald-400" />
        </div>
        <Input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => !lastResult && setShowSuggestions(true)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleSearch();
            } else if (e.key === 'Escape') {
              setShowSuggestions(false);
            }
          }}
          placeholder={lastResult ? 'Refine: "Add healthcare too"' : placeholder}
          className="pl-10 pr-24 bg-slate-800 border-slate-700 text-white h-12"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {query && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleClear}
              className="h-8 w-8 text-slate-400 hover:text-white"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
          <Button
            onClick={handleSearch}
            disabled={!query.trim() || isLoading}
            className="h-8 px-3 bg-emerald-600 hover:bg-emerald-700"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Search className="h-4 w-4 mr-1" />
                AI
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Current Search Result */}
      {showResult && lastResult && (
        <div className="mt-2 p-3 rounded-lg bg-slate-800/50 border border-slate-700">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Lightbulb className="h-4 w-4 text-yellow-400" />
                <span className="text-sm font-medium text-white">
                  Interpreted as:
                </span>
                <ConfidenceDot confidence={lastResult.confidence} />
              </div>
              <p className="text-sm text-slate-300">{lastResult.interpreted_as}</p>
              
              {/* Show extracted criteria */}
              <div className="flex flex-wrap gap-2 mt-2">
                {lastResult.sectors.length > 0 && (
                  <CriteriaBadge label="Sectors" value={lastResult.sectors.join(', ')} />
                )}
                {lastResult.rsi_condition && (
                  <CriteriaBadge label="RSI" value={lastResult.rsi_condition} />
                )}
                {lastResult.sma_condition && (
                  <CriteriaBadge label="MA" value={lastResult.sma_condition} />
                )}
                {lastResult.suggested_persona && (
                  <CriteriaBadge label="Persona" value={lastResult.suggested_persona} />
                )}
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClear}
              className="text-slate-400 hover:text-white"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Suggestions Dropdown */}
      {showSuggestions && !lastResult && (
        <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden">
          <div className="p-2 border-b border-slate-700">
            <p className="text-xs text-slate-400 flex items-center gap-1">
              <MessageSquare className="h-3 w-3" />
              Try asking in natural language
            </p>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {(suggestions || []).map((suggestion, i) => (
              <button
                key={i}
                onClick={() => handleSuggestionClick(suggestion)}
                className="w-full px-3 py-2 text-left hover:bg-slate-700/50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-white">{suggestion.query}</p>
                    <p className="text-xs text-slate-400">{suggestion.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-400">
                      {suggestion.category}
                    </span>
                    <ChevronRight className="h-4 w-4 text-slate-500" />
                  </div>
                </div>
              </button>
            ))}
          </div>
          {query.length >= 3 && (
            <div className="p-2 border-t border-slate-700">
              <button
                onClick={handleSearch}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-emerald-400 hover:bg-slate-700/50 rounded transition-colors"
              >
                <Search className="h-4 w-4" />
                Search for &quot;{query}&quot;
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ConfidenceDot({ confidence }: { confidence: number }) {
  const color =
    confidence >= 0.8
      ? 'bg-emerald-500'
      : confidence >= 0.6
        ? 'bg-yellow-500'
        : 'bg-red-500';

  return (
    <div
      className={cn('h-2 w-2 rounded-full', color)}
      title={`${Math.round(confidence * 100)}% confidence`}
    />
  );
}

function CriteriaBadge({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded bg-slate-700/50 text-slate-300">
      <span className="text-slate-500">{label}:</span>
      {value}
    </span>
  );
}

