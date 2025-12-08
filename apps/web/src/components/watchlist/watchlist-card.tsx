'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Eye,
  Plus,
  MoreVertical,
  Trash2,
  Edit,
  Star,
  StarOff,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/loading';
import { cn } from '@/lib/utils';
import {
  useWatchlist,
  useRemoveWatchlistItem,
  useUpdateWatchlist,
  type WatchlistSummary,
  type WatchlistItem,
} from '@/lib/api/hooks/use-watchlists';

interface WatchlistCardProps {
  watchlist: WatchlistSummary;
  onEdit?: () => void;
  onDelete?: () => void;
  compact?: boolean;
}

/**
 * Card displaying a watchlist with its items
 */
export function WatchlistCard({
  watchlist,
  onEdit,
  onDelete,
  compact = false,
}: WatchlistCardProps) {
  const [showMenu, setShowMenu] = useState(false);
  
  // Fetch full watchlist with items
  const { data: fullWatchlist, isLoading } = useWatchlist(watchlist.watchlist_id);
  const updateWatchlist = useUpdateWatchlist();
  const removeItem = useRemoveWatchlistItem();

  const items = fullWatchlist?.items || [];
  const displayItems = compact ? items.slice(0, 5) : items;

  const handleSetDefault = () => {
    updateWatchlist.mutate({
      watchlistId: watchlist.watchlist_id,
      data: { is_default: true },
    });
    setShowMenu(false);
  };

  return (
    <Card className="bg-slate-800/50 border-slate-700 hover:border-slate-600 transition-colors">
      <CardHeader className="pb-2 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <Eye className="h-4 w-4 text-emerald-400" />
          <CardTitle className="text-sm font-medium text-white">
            <Link
              href={`/watchlist/${watchlist.watchlist_id}`}
              className="hover:text-emerald-400 transition-colors"
            >
              {watchlist.name}
            </Link>
          </CardTitle>
          {watchlist.is_default && (
            <Star className="h-3 w-3 text-yellow-400 fill-yellow-400" />
          )}
        </div>
        
        {/* Menu */}
        <div className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => setShowMenu(!showMenu)}
          >
            <MoreVertical className="h-4 w-4 text-slate-400" />
          </Button>
          
          {showMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowMenu(false)}
              />
              <div className="absolute right-0 top-full mt-1 z-20 w-40 bg-slate-800 border border-slate-700 rounded-md shadow-lg py-1">
                {onEdit && (
                  <button
                    className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700 flex items-center gap-2"
                    onClick={() => {
                      onEdit();
                      setShowMenu(false);
                    }}
                  >
                    <Edit className="h-4 w-4" />
                    Edit
                  </button>
                )}
                {!watchlist.is_default && (
                  <button
                    className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700 flex items-center gap-2"
                    onClick={handleSetDefault}
                  >
                    <Star className="h-4 w-4" />
                    Set as default
                  </button>
                )}
                {onDelete && (
                  <button
                    className="w-full px-3 py-2 text-left text-sm text-red-400 hover:bg-slate-700 flex items-center gap-2"
                    onClick={() => {
                      onDelete();
                      setShowMenu(false);
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {watchlist.description && (
          <p className="text-xs text-slate-500 mb-3">{watchlist.description}</p>
        )}
        
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-6">
            <Eye className="h-8 w-8 text-slate-600 mx-auto mb-2" />
            <p className="text-sm text-slate-500">No stocks in this watchlist</p>
            <Link href={`/watchlist/${watchlist.watchlist_id}`}>
              <Button size="sm" variant="outline" className="mt-3 border-slate-600">
                <Plus className="h-3 w-3 mr-1" />
                Add stocks
              </Button>
            </Link>
          </div>
        ) : (
          <>
            <div className="space-y-1">
              {displayItems.map((item) => (
                <WatchlistItemRow
                  key={item.ticker}
                  item={item}
                  watchlistId={watchlist.watchlist_id}
                  onRemove={() =>
                    removeItem.mutate({
                      watchlistId: watchlist.watchlist_id,
                      ticker: item.ticker,
                    })
                  }
                  compact={compact}
                />
              ))}
            </div>
            
            {compact && items.length > 5 && (
              <Link href={`/watchlist/${watchlist.watchlist_id}`}>
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mt-2 text-slate-400 hover:text-white"
                >
                  View all {items.length} stocks
                </Button>
              </Link>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Individual watchlist item row
 */
function WatchlistItemRow({
  item,
  watchlistId,
  onRemove,
  compact,
}: {
  item: WatchlistItem;
  watchlistId: string;
  onRemove: () => void;
  compact?: boolean;
}) {
  const priceChangePositive = (item.price_change_pct ?? 0) >= 0;

  return (
    <div className="flex items-center justify-between py-2 px-2 rounded hover:bg-slate-700/50 group">
      <Link
        href={`/stocks/${item.ticker}`}
        className="flex items-center gap-3 flex-1 min-w-0"
      >
        <span className="font-medium text-white">{item.ticker}</span>
        {item.current_price && (
          <span className="text-sm text-slate-400">
            ${item.current_price.toFixed(2)}
          </span>
        )}
      </Link>

      <div className="flex items-center gap-2">
        {item.price_change_pct !== null && (
          <span
            className={cn(
              'text-sm font-medium flex items-center gap-1',
              priceChangePositive ? 'text-emerald-400' : 'text-red-400'
            )}
          >
            {priceChangePositive ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            {priceChangePositive ? '+' : ''}
            {item.price_change_pct.toFixed(2)}%
          </span>
        )}

        {!compact && (
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => {
              e.preventDefault();
              onRemove();
            }}
          >
            <Trash2 className="h-3 w-3 text-slate-500 hover:text-red-400" />
          </Button>
        )}
      </div>
    </div>
  );
}

/**
 * Skeleton loader for watchlist card
 */
export function WatchlistCardSkeleton() {
  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader className="pb-2">
        <Skeleton className="h-5 w-32" />
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

