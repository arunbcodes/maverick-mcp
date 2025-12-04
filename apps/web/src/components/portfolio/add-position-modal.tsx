'use client';

import { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAddPosition } from '@/lib/api/hooks';
import { useStockSearch } from '@/lib/api/hooks/use-stocks';
import type { AddPositionRequest, StockInfo } from '@/lib/api/types';
import { cn } from '@/lib/utils';

interface AddPositionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function AddPositionModal({
  isOpen,
  onClose,
  onSuccess,
}: AddPositionModalProps) {
  const [ticker, setTicker] = useState('');
  const [shares, setShares] = useState('');
  const [purchasePrice, setPurchasePrice] = useState('');
  const [purchaseDate, setPurchaseDate] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [showSearch, setShowSearch] = useState(false);

  const addPosition = useAddPosition();
  const { data: searchResults } = useStockSearch(ticker, {
    enabled: ticker.length >= 1 && showSearch,
  });

  const resetForm = () => {
    setTicker('');
    setShares('');
    setPurchasePrice('');
    setPurchaseDate('');
    setNotes('');
    setError('');
    setShowSearch(false);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSelectStock = (stock: StockInfo) => {
    setTicker(stock.ticker);
    setShowSearch(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!ticker || !shares || !purchasePrice) {
      setError('Please fill in all required fields');
      return;
    }

    const sharesNum = parseFloat(shares);
    const priceNum = parseFloat(purchasePrice);

    if (isNaN(sharesNum) || sharesNum <= 0) {
      setError('Shares must be a positive number');
      return;
    }

    if (isNaN(priceNum) || priceNum <= 0) {
      setError('Purchase price must be a positive number');
      return;
    }

    const data: AddPositionRequest = {
      ticker: ticker.toUpperCase(),
      shares: sharesNum,
      purchase_price: priceNum,
      purchase_date: purchaseDate || undefined,
      notes: notes || undefined,
    };

    try {
      await addPosition.mutateAsync(data);
      handleClose();
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add position');
    }
  };

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
          <CardTitle className="text-white">Add Position</CardTitle>
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

            {/* Ticker with search */}
            <div className="space-y-2 relative">
              <label className="text-sm font-medium text-slate-300">
                Ticker <span className="text-red-400">*</span>
              </label>
              <Input
                value={ticker}
                onChange={(e) => {
                  setTicker(e.target.value.toUpperCase());
                  setShowSearch(true);
                }}
                onFocus={() => setShowSearch(true)}
                placeholder="AAPL"
                className="bg-slate-800 border-slate-700 text-white"
              />
              {/* Search dropdown */}
              {showSearch && searchResults && searchResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-md shadow-lg z-10 max-h-48 overflow-auto">
                  {searchResults.slice(0, 5).map((stock) => (
                    <button
                      key={stock.ticker}
                      type="button"
                      className="w-full px-3 py-2 text-left hover:bg-slate-700 flex items-center justify-between"
                      onClick={() => handleSelectStock(stock)}
                    >
                      <span className="text-white font-medium">
                        {stock.ticker}
                      </span>
                      <span className="text-slate-400 text-sm truncate ml-2">
                        {stock.name}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Shares */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Shares <span className="text-red-400">*</span>
              </label>
              <Input
                type="number"
                step="0.001"
                min="0"
                value={shares}
                onChange={(e) => setShares(e.target.value)}
                placeholder="100"
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>

            {/* Purchase Price */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Purchase Price <span className="text-red-400">*</span>
              </label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={purchasePrice}
                onChange={(e) => setPurchasePrice(e.target.value)}
                placeholder="150.00"
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>

            {/* Purchase Date */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Purchase Date
              </label>
              <Input
                type="date"
                value={purchaseDate}
                onChange={(e) => setPurchaseDate(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Notes</label>
              <Input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional notes..."
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>

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
                isLoading={addPosition.isPending}
              >
                Add Position
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

