'use client';

import { useState } from 'react';
import { Eye, EyeOff, Plus, Check, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  useWatchlists,
  useQuickAddToWatchlist,
  useRemoveWatchlistItem,
  useIsWatching,
} from '@/lib/api/hooks/use-watchlists';

interface AddToWatchlistButtonProps {
  ticker: string;
  variant?: 'default' | 'icon' | 'compact';
  className?: string;
}

/**
 * Button to add/remove a stock from watchlist
 */
export function AddToWatchlistButton({
  ticker,
  variant = 'default',
  className,
}: AddToWatchlistButtonProps) {
  const [showDropdown, setShowDropdown] = useState(false);

  // Check if already watching
  const { data: watchingStatus, isLoading: checkingStatus } = useIsWatching(ticker);
  const { data: watchlists = [] } = useWatchlists();

  // Mutations
  const quickAdd = useQuickAddToWatchlist();
  const removeItem = useRemoveWatchlistItem();

  const isWatching = watchingStatus?.is_watching;

  const handleToggle = () => {
    if (isWatching && watchingStatus?.watchlist_id) {
      removeItem.mutate({
        watchlistId: watchingStatus.watchlist_id,
        ticker,
      });
    } else {
      quickAdd.mutate({ ticker });
    }
  };

  const handleAddToSpecific = (watchlistId: string) => {
    quickAdd.mutate({ ticker, watchlistId });
    setShowDropdown(false);
  };

  const isLoading = quickAdd.isPending || removeItem.isPending || checkingStatus;

  if (variant === 'icon') {
    return (
      <Button
        variant="ghost"
        size="icon"
        className={cn('h-8 w-8', className)}
        onClick={handleToggle}
        disabled={isLoading}
        title={isWatching ? 'Remove from watchlist' : 'Add to watchlist'}
      >
        {isWatching ? (
          <Eye className="h-4 w-4 text-emerald-400" />
        ) : (
          <EyeOff className="h-4 w-4 text-slate-500" />
        )}
      </Button>
    );
  }

  if (variant === 'compact') {
    return (
      <Button
        variant={isWatching ? 'outline' : 'ghost'}
        size="sm"
        className={cn(
          'h-7',
          isWatching
            ? 'border-emerald-600 text-emerald-400'
            : 'text-slate-400 hover:text-white',
          className
        )}
        onClick={handleToggle}
        disabled={isLoading}
      >
        {isWatching ? (
          <>
            <Check className="h-3 w-3 mr-1" />
            Watching
          </>
        ) : (
          <>
            <Eye className="h-3 w-3 mr-1" />
            Watch
          </>
        )}
      </Button>
    );
  }

  // Default variant with dropdown
  return (
    <div className={cn('relative', className)}>
      <div className="flex">
        <Button
          variant={isWatching ? 'outline' : 'secondary'}
          size="sm"
          className={cn(
            'rounded-r-none',
            isWatching && 'border-emerald-600 text-emerald-400'
          )}
          onClick={handleToggle}
          disabled={isLoading}
        >
          {isWatching ? (
            <>
              <Check className="h-4 w-4 mr-2" />
              Watching
            </>
          ) : (
            <>
              <Eye className="h-4 w-4 mr-2" />
              Watch
            </>
          )}
        </Button>
        <Button
          variant={isWatching ? 'outline' : 'secondary'}
          size="sm"
          className={cn(
            'rounded-l-none border-l-0 px-2',
            isWatching && 'border-emerald-600'
          )}
          onClick={() => setShowDropdown(!showDropdown)}
        >
          <ChevronDown className="h-4 w-4" />
        </Button>
      </div>

      {/* Dropdown */}
      {showDropdown && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowDropdown(false)}
          />
          <div className="absolute right-0 top-full mt-1 z-20 w-48 bg-slate-800 border border-slate-700 rounded-md shadow-lg py-1">
            <div className="px-3 py-2 text-xs font-medium text-slate-400 border-b border-slate-700">
              Add to watchlist
            </div>
            {watchlists.length === 0 ? (
              <div className="px-3 py-2 text-sm text-slate-500">
                No watchlists yet
              </div>
            ) : (
              watchlists.map((wl) => (
                <button
                  key={wl.watchlist_id}
                  className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700 flex items-center justify-between"
                  onClick={() => handleAddToSpecific(wl.watchlist_id)}
                >
                  <span>{wl.name}</span>
                  <span className="text-xs text-slate-500">
                    {wl.item_count} items
                  </span>
                </button>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}

/**
 * Quick add button for screener results
 */
export function QuickWatchButton({
  ticker,
  className,
}: {
  ticker: string;
  className?: string;
}) {
  const { data: watchingStatus } = useIsWatching(ticker);
  const quickAdd = useQuickAddToWatchlist();
  const removeItem = useRemoveWatchlistItem();

  const isWatching = watchingStatus?.is_watching;
  const isLoading = quickAdd.isPending || removeItem.isPending;

  const handleClick = () => {
    if (isWatching && watchingStatus?.watchlist_id) {
      removeItem.mutate({
        watchlistId: watchingStatus.watchlist_id,
        ticker,
      });
    } else {
      quickAdd.mutate({ ticker });
    }
  };

  return (
    <button
      className={cn(
        'p-1 rounded transition-colors',
        isWatching
          ? 'text-emerald-400 hover:text-emerald-300'
          : 'text-slate-500 hover:text-slate-300',
        className
      )}
      onClick={handleClick}
      disabled={isLoading}
      title={isWatching ? 'Remove from watchlist' : 'Add to watchlist'}
    >
      {isWatching ? (
        <Eye className="h-4 w-4" />
      ) : (
        <Plus className="h-4 w-4" />
      )}
    </button>
  );
}

