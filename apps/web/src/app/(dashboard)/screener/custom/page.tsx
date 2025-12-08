'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Filter,
  Plus,
  Play,
  Copy,
  Trash2,
  MoreVertical,
  ChevronLeft,
  Zap,
  Search,
  Clock,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/loading';
import { FilterBuilder, FilterSummary } from '@/components/screener';
import { cn } from '@/lib/utils';
import {
  useCustomScreeners,
  useCreateCustomScreener,
  useDeleteCustomScreener,
  useDuplicateCustomScreener,
  useRunCustomScreener,
  useScreenerPresets,
  useCreateFromPreset,
  type FilterCondition,
  type ScreenerSummary,
} from '@/lib/api/hooks';

export default function CustomScreenersPage() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedScreenerId, setSelectedScreenerId] = useState<string | null>(null);

  const { data: screeners = [], isLoading } = useCustomScreeners();
  const { data: presets = [] } = useScreenerPresets();

  const deleteScreener = useDeleteCustomScreener();
  const duplicateScreener = useDuplicateCustomScreener();
  const createFromPreset = useCreateFromPreset();

  const handleDelete = (screenerId: string) => {
    if (confirm('Are you sure you want to delete this screener?')) {
      deleteScreener.mutate(screenerId);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/screener">
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <Filter className="h-7 w-7 text-emerald-400" />
              Custom Screeners
            </h1>
            <p className="text-slate-400 mt-1">
              Build your own stock screening criteria
            </p>
          </div>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          className="bg-emerald-600 hover:bg-emerald-500"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Screener
        </Button>
      </div>

      {/* Presets Section */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
            <Zap className="h-4 w-4 text-yellow-400" />
            Quick Start Templates
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {presets.map((preset) => (
              <Button
                key={preset.name}
                variant="outline"
                size="sm"
                className="border-slate-600 text-slate-300 hover:text-white"
                onClick={() => createFromPreset.mutate(preset.name)}
                disabled={createFromPreset.isPending}
              >
                {preset.name}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Screeners List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <Skeleton className="h-6 w-32 mb-2" />
                <Skeleton className="h-4 w-48 mb-4" />
                <Skeleton className="h-8 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : screeners.length === 0 ? (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-16 text-center">
            <Filter className="h-16 w-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-white mb-2">
              No custom screeners yet
            </h3>
            <p className="text-slate-400 mb-6 max-w-md mx-auto">
              Create your first custom screener or start from a template to
              find stocks matching your specific criteria.
            </p>
            <div className="flex justify-center gap-3">
              <Button
                variant="outline"
                className="border-slate-600"
                onClick={() => createFromPreset.mutate('Momentum Leaders')}
              >
                <Zap className="h-4 w-4 mr-2" />
                Use Template
              </Button>
              <Button
                onClick={() => setShowCreateModal(true)}
                className="bg-emerald-600 hover:bg-emerald-500"
              >
                <Plus className="h-4 w-4 mr-2" />
                Build From Scratch
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {screeners.map((screener) => (
            <ScreenerCard
              key={screener.screener_id}
              screener={screener}
              onSelect={() => setSelectedScreenerId(screener.screener_id)}
              onDuplicate={() =>
                duplicateScreener.mutate({ screenerId: screener.screener_id })
              }
              onDelete={() => handleDelete(screener.screener_id)}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateScreenerModal onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  );
}

/**
 * Screener card
 */
function ScreenerCard({
  screener,
  onSelect,
  onDuplicate,
  onDelete,
}: {
  screener: ScreenerSummary;
  onSelect: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
}) {
  const [showMenu, setShowMenu] = useState(false);
  const runScreener = useRunCustomScreener();

  return (
    <Card className="bg-slate-800/50 border-slate-700 hover:border-slate-600 transition-colors">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-medium text-white">{screener.name}</h3>
            {screener.description && (
              <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                {screener.description}
              </p>
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
                <div className="absolute right-0 top-full mt-1 z-20 w-36 bg-slate-800 border border-slate-700 rounded-md shadow-lg py-1">
                  <button
                    className="w-full px-3 py-2 text-left text-sm text-slate-300 hover:bg-slate-700 flex items-center gap-2"
                    onClick={() => {
                      onDuplicate();
                      setShowMenu(false);
                    }}
                  >
                    <Copy className="h-4 w-4" />
                    Duplicate
                  </button>
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
                </div>
              </>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-xs text-slate-500 mb-4">
          <span className="flex items-center gap-1">
            <Filter className="h-3 w-3" />
            {screener.condition_count} filters
          </span>
          <span className="flex items-center gap-1">
            <Play className="h-3 w-3" />
            {screener.run_count} runs
          </span>
          {screener.last_run && (
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatRelativeTime(screener.last_run)}
            </span>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 border-slate-600"
            onClick={onSelect}
          >
            <Search className="h-3 w-3 mr-1" />
            Edit
          </Button>
          <Button
            size="sm"
            className="flex-1 bg-emerald-600 hover:bg-emerald-500"
            onClick={() => runScreener.mutate(screener.screener_id)}
            isLoading={runScreener.isPending}
          >
            <Play className="h-3 w-3 mr-1" />
            Run
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Create screener modal
 */
function CreateScreenerModal({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [conditions, setConditions] = useState<FilterCondition[]>([]);
  const [sortBy, setSortBy] = useState<string>('');
  const [sortDescending, setSortDescending] = useState(true);

  const createScreener = useCreateCustomScreener();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createScreener.mutateAsync({
      name,
      description: description || undefined,
      conditions,
      sort_by: sortBy || undefined,
      sort_descending: sortDescending,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto py-8">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <Card className="relative z-10 w-full max-w-2xl mx-4 bg-slate-900 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Filter className="h-5 w-5 text-emerald-400" />
            Create Custom Screener
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">Name</label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="My Screener"
                  className="bg-slate-800 border-slate-700 text-white"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">
                  Description (optional)
                </label>
                <Input
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Find stocks that..."
                  className="bg-slate-800 border-slate-700 text-white"
                />
              </div>
            </div>

            {/* Filter Builder */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Filters (AND logic)
              </label>
              <FilterBuilder conditions={conditions} onChange={setConditions} />
            </div>

            {/* Sort Options */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">Sort By</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full px-3 py-2 rounded-md bg-slate-800 border border-slate-700 text-white text-sm"
                >
                  <option value="">No sorting</option>
                  <option value="price">Price</option>
                  <option value="price_change_pct">Price Change %</option>
                  <option value="volume">Volume</option>
                  <option value="rsi_14">RSI (14)</option>
                  <option value="market_cap">Market Cap</option>
                  <option value="momentum_score">Momentum Score</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">Sort Order</label>
                <select
                  value={sortDescending ? 'desc' : 'asc'}
                  onChange={(e) => setSortDescending(e.target.value === 'desc')}
                  className="w-full px-3 py-2 rounded-md bg-slate-800 border border-slate-700 text-white text-sm"
                >
                  <option value="desc">Highest First</option>
                  <option value="asc">Lowest First</option>
                </select>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4 border-t border-slate-700">
              <Button
                type="button"
                variant="outline"
                className="flex-1 border-slate-700 text-slate-300"
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-emerald-600 hover:bg-emerald-500"
                isLoading={createScreener.isPending}
                disabled={!name || conditions.length === 0}
              >
                Create Screener
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

