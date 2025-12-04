'use client';

import { useState } from 'react';
import { cn, formatCurrency, formatPercent } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Trash2, Edit2, TrendingUp, TrendingDown } from 'lucide-react';
import type { Position } from '@/lib/api/types';

interface PositionRowProps {
  position: Position;
  onEdit?: (position: Position) => void;
  onRemove?: (positionId: string) => void;
  showActions?: boolean;
  isLive?: boolean;
}

export function PositionRow({
  position,
  onEdit,
  onRemove,
  showActions = true,
  isLive = false,
}: PositionRowProps) {
  const [isHovered, setIsHovered] = useState(false);
  
  const isGain = position.gain >= 0;
  const dayIsGain = (position.day_change ?? 0) >= 0;

  return (
    <div
      className={cn(
        'flex items-center justify-between p-4 rounded-lg bg-slate-800/50 transition-all',
        isHovered && 'bg-slate-800',
        isLive && 'ring-1 ring-emerald-500/20'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Left: Ticker & Name */}
      <div className="flex items-center space-x-4 min-w-0 flex-1">
        <div className="w-10 h-10 rounded-lg bg-emerald-600/20 flex items-center justify-center flex-shrink-0">
          <span className="text-emerald-400 font-semibold text-sm">
            {position.ticker.slice(0, 2)}
          </span>
        </div>
        <div className="min-w-0">
          <div className="flex items-center space-x-2">
            <p className="text-white font-medium truncate">{position.ticker}</p>
            {isLive && (
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            )}
          </div>
          <p className="text-sm text-slate-400 truncate">
            {position.name || `${position.shares} shares`}
          </p>
        </div>
      </div>

      {/* Center: Shares & Cost */}
      <div className="hidden md:block text-center px-4">
        <p className="text-white">{position.shares}</p>
        <p className="text-sm text-slate-400">
          @ {formatCurrency(position.avg_cost)}
        </p>
      </div>

      {/* Right: Value & Gain */}
      <div className="text-right flex items-center space-x-4">
        <div>
          <p className="text-white font-medium">
            {formatCurrency(position.market_value ?? position.cost_basis)}
          </p>
          <div className="flex items-center justify-end space-x-1">
            {isGain ? (
              <TrendingUp className="h-3 w-3 text-emerald-400" />
            ) : (
              <TrendingDown className="h-3 w-3 text-red-400" />
            )}
            <span
              className={cn(
                'text-sm',
                isGain ? 'text-emerald-400' : 'text-red-400'
              )}
            >
              {formatCurrency(Math.abs(position.gain))} ({formatPercent(position.gain_percent)})
            </span>
          </div>
        </div>

        {/* Day Change (if available) */}
        {position.day_change !== undefined && (
          <div className="hidden lg:block text-right">
            <p className="text-xs text-slate-500">Today</p>
            <p
              className={cn(
                'text-sm',
                dayIsGain ? 'text-emerald-400' : 'text-red-400'
              )}
            >
              {formatPercent(position.day_change_percent ?? 0)}
            </p>
          </div>
        )}

        {/* Actions */}
        {showActions && (
          <div
            className={cn(
              'flex items-center space-x-1 transition-opacity',
              isHovered ? 'opacity-100' : 'opacity-0'
            )}
          >
            {onEdit && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-slate-400 hover:text-white"
                onClick={() => onEdit(position)}
              >
                <Edit2 className="h-4 w-4" />
              </Button>
            )}
            {onRemove && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-slate-400 hover:text-red-400"
                onClick={() => onRemove(position.position_id)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

interface PositionListProps {
  positions: Position[];
  onEdit?: (position: Position) => void;
  onRemove?: (positionId: string) => void;
  showActions?: boolean;
  liveTickers?: string[];
}

export function PositionList({
  positions,
  onEdit,
  onRemove,
  showActions = true,
  liveTickers = [],
}: PositionListProps) {
  if (positions.length === 0) {
    return null;
  }

  // Sort by market value descending
  const sortedPositions = [...positions].sort(
    (a, b) => (b.market_value ?? b.cost_basis) - (a.market_value ?? a.cost_basis)
  );

  return (
    <div className="space-y-2">
      {sortedPositions.map((position) => (
        <PositionRow
          key={position.position_id}
          position={position}
          onEdit={onEdit}
          onRemove={onRemove}
          showActions={showActions}
          isLive={liveTickers.includes(position.ticker)}
        />
      ))}
    </div>
  );
}

