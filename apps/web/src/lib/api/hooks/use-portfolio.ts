/**
 * React Query hooks for Portfolio API endpoints
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type {
  APIResponse,
  Portfolio,
  Position,
  PortfolioSummary,
  AddPositionRequest,
  UpdatePositionRequest,
} from '../types';

// Query Keys
export const portfolioKeys = {
  all: ['portfolio'] as const,
  list: () => [...portfolioKeys.all, 'list'] as const,
  detail: (id: string) => [...portfolioKeys.all, 'detail', id] as const,
  summary: () => [...portfolioKeys.all, 'summary'] as const,
  positions: () => [...portfolioKeys.all, 'positions'] as const,
  position: (id: string) => [...portfolioKeys.all, 'position', id] as const,
};

/**
 * Get portfolio summary (main dashboard data)
 */
export function usePortfolioSummary(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: portfolioKeys.summary(),
    queryFn: async () => {
      const response = await api.get<APIResponse<PortfolioSummary>>(
        '/portfolio/summary'
      );
      return response.data;
    },
    enabled: options?.enabled,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute for live P&L
  });
}

/**
 * Get full portfolio with all positions
 */
export function usePortfolio(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: portfolioKeys.detail('default'),
    queryFn: async () => {
      const response = await api.get<APIResponse<Portfolio>>('/portfolio');
      return response.data;
    },
    enabled: options?.enabled,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });
}

/**
 * Get all positions
 */
export function usePositions(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: portfolioKeys.positions(),
    queryFn: async () => {
      const response = await api.get<APIResponse<Position[]>>(
        '/portfolio/positions'
      );
      return response.data;
    },
    enabled: options?.enabled,
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
  });
}

/**
 * Get single position details
 */
export function usePosition(positionId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: portfolioKeys.position(positionId),
    queryFn: async () => {
      const response = await api.get<APIResponse<Position>>(
        `/portfolio/positions/${positionId}`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!positionId,
    staleTime: 30 * 1000,
  });
}

/**
 * Add a new position
 */
export function useAddPosition() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: AddPositionRequest) => {
      const response = await api.post<APIResponse<Position>>(
        '/portfolio/positions',
        data
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate all portfolio queries to refetch
      queryClient.invalidateQueries({ queryKey: portfolioKeys.all });
    },
  });
}

/**
 * Update an existing position
 */
export function useUpdatePosition() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      positionId,
      data,
    }: {
      positionId: string;
      data: UpdatePositionRequest;
    }) => {
      const response = await api.put<APIResponse<Position>>(
        `/portfolio/positions/${positionId}`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: portfolioKeys.all });
      queryClient.invalidateQueries({
        queryKey: portfolioKeys.position(variables.positionId),
      });
    },
  });
}

/**
 * Remove a position
 */
export function useRemovePosition() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (positionId: string) => {
      const response = await api.delete<APIResponse<{ message: string }>>(
        `/portfolio/positions/${positionId}`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: portfolioKeys.all });
    },
  });
}

/**
 * Batch update positions (for rebalancing)
 */
export function useBatchUpdatePositions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      updates: Array<{ positionId: string; data: UpdatePositionRequest }>
    ) => {
      const response = await api.put<APIResponse<Position[]>>(
        '/portfolio/positions/batch',
        { updates }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: portfolioKeys.all });
    },
  });
}

/**
 * Optimistic update helper - immediately update cache
 */
export function useOptimisticPositionUpdate() {
  const queryClient = useQueryClient();

  return {
    updatePosition: (positionId: string, updates: Partial<Position>) => {
      queryClient.setQueryData<Position[]>(portfolioKeys.positions(), (old) => {
        if (!old) return old;
        return old.map((p) =>
          p.position_id === positionId ? { ...p, ...updates } : p
        );
      });
    },
    rollback: () => {
      queryClient.invalidateQueries({ queryKey: portfolioKeys.positions() });
    },
  };
}

