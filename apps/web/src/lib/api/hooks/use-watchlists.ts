/**
 * React Query hooks for Watchlist API endpoints
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type { APIResponse } from '../types';

// ============================================
// Types
// ============================================

export interface WatchlistItem {
  ticker: string;
  added_at: string;
  notes: string | null;
  alert_enabled: boolean;
  target_price: number | null;
  stop_price: number | null;
  position: number;
  current_price: number | null;
  price_change: number | null;
  price_change_pct: number | null;
}

export interface Watchlist {
  watchlist_id: string;
  user_id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  items: WatchlistItem[];
  item_count: number;
  created_at: string;
  updated_at: string | null;
}

export interface WatchlistSummary {
  watchlist_id: string;
  name: string;
  description: string | null;
  is_default: boolean;
  item_count: number;
  created_at: string;
}

export interface CreateWatchlistRequest {
  name: string;
  description?: string;
  is_default?: boolean;
}

export interface UpdateWatchlistRequest {
  name?: string;
  description?: string;
  is_default?: boolean;
}

export interface AddItemRequest {
  ticker: string;
  notes?: string;
  target_price?: number;
  stop_price?: number;
}

export interface UpdateItemRequest {
  notes?: string;
  alert_enabled?: boolean;
  target_price?: number;
  stop_price?: number;
}

export interface IsWatchingResponse {
  is_watching: boolean;
  watchlist_id: string | null;
  watchlist_name: string | null;
  notes: string | null;
  target_price: number | null;
  stop_price: number | null;
}

// ============================================
// Query Keys
// ============================================

export const watchlistKeys = {
  all: ['watchlists'] as const,
  lists: () => [...watchlistKeys.all, 'lists'] as const,
  list: (id: string) => [...watchlistKeys.all, 'list', id] as const,
  watching: (ticker: string) => [...watchlistKeys.all, 'watching', ticker] as const,
};

// ============================================
// Watchlist Hooks
// ============================================

/**
 * Get all watchlists for the current user
 */
export function useWatchlists() {
  return useQuery({
    queryKey: watchlistKeys.lists(),
    queryFn: async () => {
      const response = await api.get<APIResponse<WatchlistSummary[]>>('/watchlists');
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Get a specific watchlist with items
 */
export function useWatchlist(watchlistId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: watchlistKeys.list(watchlistId),
    queryFn: async () => {
      const response = await api.get<APIResponse<Watchlist>>(
        `/watchlists/${watchlistId}?include_prices=true`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!watchlistId,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 30 * 1000, // Refresh prices every 30s
  });
}

/**
 * Create a new watchlist
 */
export function useCreateWatchlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateWatchlistRequest) => {
      const response = await api.post<APIResponse<Watchlist>>('/watchlists', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: watchlistKeys.lists() });
    },
  });
}

/**
 * Update a watchlist
 */
export function useUpdateWatchlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ watchlistId, data }: { watchlistId: string; data: UpdateWatchlistRequest }) => {
      const response = await api.patch<APIResponse<Watchlist>>(
        `/watchlists/${watchlistId}`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: watchlistKeys.lists() });
      queryClient.invalidateQueries({ queryKey: watchlistKeys.list(variables.watchlistId) });
    },
  });
}

/**
 * Delete a watchlist
 */
export function useDeleteWatchlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (watchlistId: string) => {
      await api.delete(`/watchlists/${watchlistId}`);
      return watchlistId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: watchlistKeys.lists() });
    },
  });
}

// ============================================
// Item Hooks
// ============================================

/**
 * Add an item to a watchlist
 */
export function useAddWatchlistItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ watchlistId, data }: { watchlistId: string; data: AddItemRequest }) => {
      const response = await api.post<APIResponse<WatchlistItem>>(
        `/watchlists/${watchlistId}/items`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: watchlistKeys.list(variables.watchlistId) });
      queryClient.invalidateQueries({ queryKey: watchlistKeys.lists() });
      queryClient.invalidateQueries({ queryKey: watchlistKeys.watching(variables.data.ticker) });
    },
  });
}

/**
 * Add multiple items to a watchlist
 */
export function useAddWatchlistItemsBatch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ watchlistId, tickers }: { watchlistId: string; tickers: string[] }) => {
      const response = await api.post<APIResponse<WatchlistItem[]>>(
        `/watchlists/${watchlistId}/items/batch`,
        { tickers }
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: watchlistKeys.list(variables.watchlistId) });
      queryClient.invalidateQueries({ queryKey: watchlistKeys.lists() });
    },
  });
}

/**
 * Update an item in a watchlist
 */
export function useUpdateWatchlistItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      watchlistId,
      ticker,
      data,
    }: {
      watchlistId: string;
      ticker: string;
      data: UpdateItemRequest;
    }) => {
      const response = await api.patch<APIResponse<WatchlistItem>>(
        `/watchlists/${watchlistId}/items/${ticker}`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: watchlistKeys.list(variables.watchlistId) });
    },
  });
}

/**
 * Remove an item from a watchlist
 */
export function useRemoveWatchlistItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ watchlistId, ticker }: { watchlistId: string; ticker: string }) => {
      await api.delete(`/watchlists/${watchlistId}/items/${ticker}`);
      return { watchlistId, ticker };
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: watchlistKeys.list(variables.watchlistId) });
      queryClient.invalidateQueries({ queryKey: watchlistKeys.lists() });
      queryClient.invalidateQueries({ queryKey: watchlistKeys.watching(variables.ticker) });
    },
  });
}

/**
 * Reorder items in a watchlist
 */
export function useReorderWatchlistItems() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ watchlistId, tickers }: { watchlistId: string; tickers: string[] }) => {
      await api.post(`/watchlists/${watchlistId}/reorder`, { tickers });
      return { watchlistId, tickers };
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: watchlistKeys.list(variables.watchlistId) });
    },
  });
}

// ============================================
// Quick Add & Check Hooks
// ============================================

/**
 * Quickly add a stock to a watchlist
 */
export function useQuickAddToWatchlist() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ ticker, watchlistId }: { ticker: string; watchlistId?: string }) => {
      const response = await api.post<
        APIResponse<{ item: WatchlistItem; watchlist_id: string; watchlist_name: string }>
      >('/watchlists/quick-add', { ticker, watchlist_id: watchlistId });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: watchlistKeys.lists() });
      queryClient.invalidateQueries({ queryKey: watchlistKeys.list(data.watchlist_id) });
    },
  });
}

/**
 * Check if a ticker is in any watchlist
 */
export function useIsWatching(ticker: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: watchlistKeys.watching(ticker),
    queryFn: async () => {
      const response = await api.get<APIResponse<IsWatchingResponse>>(
        `/watchlists/check/${ticker}`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!ticker,
    staleTime: 60 * 1000, // 1 minute
  });
}

