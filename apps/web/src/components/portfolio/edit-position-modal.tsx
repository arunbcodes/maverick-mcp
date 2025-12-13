'use client';

import { useState, useEffect } from 'react';
import { X, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useUpdatePosition } from '@/lib/api/hooks';
import type { Position, UpdatePositionRequest } from '@/lib/api/types';
import { formatCurrency } from '@/lib/utils';

interface EditPositionModalProps {
  position: Position;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function EditPositionModal({
  position,
  isOpen,
  onClose,
  onSuccess,
}: EditPositionModalProps) {
  const [shares, setShares] = useState(position.shares.toString());
  const [avgCost, setAvgCost] = useState(position.avg_cost.toString());
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');

  const updatePosition = useUpdatePosition();

  // Reset form when position changes
  useEffect(() => {
    if (position) {
      setShares(position.shares.toString());
      setAvgCost(position.avg_cost.toString());
      setNotes('');
      setError('');
    }
  }, [position]);

  const handleClose = () => {
    setError('');
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const sharesNum = parseFloat(shares);
    const avgCostNum = parseFloat(avgCost);

    if (isNaN(sharesNum) || sharesNum <= 0) {
      setError('Shares must be a positive number');
      return;
    }

    if (isNaN(avgCostNum) || avgCostNum <= 0) {
      setError('Average cost must be a positive number');
      return;
    }

    const data: UpdatePositionRequest = {
      shares: sharesNum,
      avg_cost: avgCostNum,
      notes: notes || undefined,
    };

    try {
      const positionId = position.position_id ?? position.id;
      if (!positionId) {
        setError('Position ID not found');
        return;
      }
      await updatePosition.mutateAsync({
        positionId,
        data,
      });
      handleClose();
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update position');
    }
  };

  const totalValue = (parseFloat(shares) || 0) * (parseFloat(avgCost) || 0);
  const hasChanges =
    parseFloat(shares) !== position.shares ||
    parseFloat(avgCost) !== position.avg_cost;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <Card className="relative z-10 w-full max-w-md mx-4 bg-slate-900 border-slate-800 animate-fade-in">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-white">
            Edit {position.ticker}
          </CardTitle>
          <Button
            variant="ghost"
            size="icon"
            className="text-slate-400 hover:text-white"
            onClick={handleClose}
          >
            <X className="h-5 w-5" />
          </Button>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-md bg-red-900/20 border border-red-800 text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* Current Position Info */}
            <div className="p-3 rounded-lg bg-slate-800/50 space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Current Price</span>
                <span className="text-white">
                  {formatCurrency(position.current_price ?? 0)}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Market Value</span>
                <span className="text-white">
                  {formatCurrency(position.market_value ?? position.current_value ?? position.cost_basis ?? position.total_cost ?? 0)}
                </span>
              </div>
            </div>

            {/* Shares */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Shares
              </label>
              <Input
                type="number"
                step="0.001"
                min="0"
                value={shares}
                onChange={(e) => setShares(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>

            {/* Average Cost */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Average Cost
              </label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={avgCost}
                onChange={(e) => setAvgCost(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Notes (optional)
              </label>
              <Input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add a note..."
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>

            {/* Cost Basis Preview */}
            {hasChanges && (
              <div className="p-3 rounded-lg bg-emerald-900/20 border border-emerald-800/50">
                <p className="text-xs text-emerald-400/70">New Cost Basis</p>
                <p className="text-emerald-400 font-medium">
                  {formatCurrency(totalValue)}
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-3 pt-2">
              <Button
                type="button"
                variant="outline"
                className="flex-1 border-slate-700 text-slate-300"
                onClick={handleClose}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white"
                isLoading={updatePosition.isPending}
                disabled={!hasChanges}
              >
                <Check className="h-4 w-4 mr-2" />
                Save Changes
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

