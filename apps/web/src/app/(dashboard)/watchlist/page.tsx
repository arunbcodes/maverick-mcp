'use client';

import { useState } from 'react';
import { Eye, Plus, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/loading';
import { WatchlistCard, WatchlistCardSkeleton } from '@/components/watchlist';
import {
  useWatchlists,
  useCreateWatchlist,
  useDeleteWatchlist,
} from '@/lib/api/hooks/use-watchlists';

export default function WatchlistPage() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingWatchlistId, setEditingWatchlistId] = useState<string | null>(null);

  const { data: watchlists = [], isLoading } = useWatchlists();
  const deleteWatchlist = useDeleteWatchlist();

  const handleDelete = (watchlistId: string) => {
    if (confirm('Are you sure you want to delete this watchlist?')) {
      deleteWatchlist.mutate(watchlistId);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Eye className="h-7 w-7 text-emerald-400" />
            Watchlists
          </h1>
          <p className="text-slate-400 mt-1">
            Track stocks you&apos;re interested in
          </p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          className="bg-emerald-600 hover:bg-emerald-500"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Watchlist
        </Button>
      </div>

      {/* Watchlists Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <WatchlistCardSkeleton key={i} />
          ))}
        </div>
      ) : watchlists.length === 0 ? (
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="py-16 text-center">
            <Eye className="h-16 w-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-white mb-2">
              No watchlists yet
            </h3>
            <p className="text-slate-400 mb-6 max-w-md mx-auto">
              Create your first watchlist to start tracking stocks you&apos;re
              interested in. Get real-time price updates and alerts.
            </p>
            <Button
              onClick={() => setShowCreateModal(true)}
              className="bg-emerald-600 hover:bg-emerald-500"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Your First Watchlist
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {watchlists.map((watchlist) => (
            <WatchlistCard
              key={watchlist.watchlist_id}
              watchlist={watchlist}
              onEdit={() => setEditingWatchlistId(watchlist.watchlist_id)}
              onDelete={() => handleDelete(watchlist.watchlist_id)}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <CreateWatchlistModal onClose={() => setShowCreateModal(false)} />
      )}

      {/* Edit Modal */}
      {editingWatchlistId && (
        <EditWatchlistModal
          watchlistId={editingWatchlistId}
          onClose={() => setEditingWatchlistId(null)}
        />
      )}
    </div>
  );
}

/**
 * Modal for creating a new watchlist
 */
function CreateWatchlistModal({ onClose }: { onClose: () => void }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const createWatchlist = useCreateWatchlist();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createWatchlist.mutateAsync({
      name,
      description: description || undefined,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <Card className="relative z-10 w-full max-w-md mx-4 bg-slate-900 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Create Watchlist</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Name</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Watchlist"
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
                placeholder="Stocks I'm watching for..."
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <div className="flex gap-3 pt-4">
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
                isLoading={createWatchlist.isPending}
              >
                Create
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Modal for editing a watchlist
 */
function EditWatchlistModal({
  watchlistId,
  onClose,
}: {
  watchlistId: string;
  onClose: () => void;
}) {
  const { data: watchlists = [] } = useWatchlists();
  const watchlist = watchlists.find((w) => w.watchlist_id === watchlistId);

  const [name, setName] = useState(watchlist?.name || '');
  const [description, setDescription] = useState(watchlist?.description || '');

  const { mutateAsync: updateWatchlist, isPending } = useWatchlists().refetch
    ? { mutateAsync: async () => {}, isPending: false }
    : { mutateAsync: async () => {}, isPending: false };

  // TODO: Wire up update mutation properly
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // await updateWatchlist({ watchlistId, data: { name, description } });
    onClose();
  };

  if (!watchlist) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <Card className="relative z-10 w-full max-w-md mx-4 bg-slate-900 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">Edit Watchlist</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Name</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white"
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Description
              </label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <div className="flex gap-3 pt-4">
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
                isLoading={isPending}
              >
                Save Changes
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

