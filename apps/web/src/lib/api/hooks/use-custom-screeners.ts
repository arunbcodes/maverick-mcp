/**
 * React Query hooks for Custom Screener API endpoints
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type { APIResponse } from '../types';

// ============================================
// Types
// ============================================

export interface FilterCondition {
  field: string;
  operator: string;
  value: number | string | (string | number)[] | null;
  value2: number | null;
}

export interface CustomScreener {
  screener_id: string;
  user_id: string;
  name: string;
  description: string | null;
  conditions: FilterCondition[];
  sort_by: string | null;
  sort_descending: boolean;
  max_results: number;
  is_public: boolean;
  run_count: number;
  last_run: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface ScreenerSummary {
  screener_id: string;
  name: string;
  description: string | null;
  condition_count: number;
  run_count: number;
  last_run: string | null;
  is_public: boolean;
}

export interface ScreenerResult {
  screener_id: string;
  run_at: string;
  stocks: Record<string, unknown>[];
  total_matches: number;
  execution_time_ms: number;
}

export interface PresetScreener {
  name: string;
  description: string | null;
  conditions: FilterCondition[];
  sort_by: string | null;
}

export interface FilterFieldMeta {
  field: string;
  label: string;
  type: 'number' | 'select' | 'text';
  category: string;
  min?: number;
  max?: number;
}

export interface CreateScreenerRequest {
  name: string;
  description?: string;
  conditions: FilterCondition[];
  sort_by?: string;
  sort_descending?: boolean;
  max_results?: number;
}

export interface UpdateScreenerRequest {
  name?: string;
  description?: string;
  conditions?: FilterCondition[];
  sort_by?: string;
  sort_descending?: boolean;
  max_results?: number;
  is_public?: boolean;
}

// ============================================
// Filter Operators (for UI)
// ============================================

export const FILTER_OPERATORS = [
  { value: 'equals', label: 'Equals', types: ['number', 'text', 'select'] },
  { value: 'not_equals', label: 'Not Equals', types: ['number', 'text', 'select'] },
  { value: 'greater_than', label: 'Greater Than', types: ['number'] },
  { value: 'greater_or_equal', label: 'Greater or Equal', types: ['number'] },
  { value: 'less_than', label: 'Less Than', types: ['number'] },
  { value: 'less_or_equal', label: 'Less or Equal', types: ['number'] },
  { value: 'between', label: 'Between', types: ['number'] },
  { value: 'in', label: 'In List', types: ['text', 'select'] },
  { value: 'contains', label: 'Contains', types: ['text'] },
];

// ============================================
// Query Keys
// ============================================

export const customScreenerKeys = {
  all: ['custom-screeners'] as const,
  lists: () => [...customScreenerKeys.all, 'lists'] as const,
  detail: (id: string) => [...customScreenerKeys.all, 'detail', id] as const,
  results: (id: string) => [...customScreenerKeys.all, 'results', id] as const,
  presets: () => [...customScreenerKeys.all, 'presets'] as const,
  fields: () => [...customScreenerKeys.all, 'fields'] as const,
};

// ============================================
// Screener CRUD Hooks
// ============================================

/**
 * Get all custom screeners
 */
export function useCustomScreeners() {
  return useQuery({
    queryKey: customScreenerKeys.lists(),
    queryFn: async () => {
      const response = await api.get<APIResponse<ScreenerSummary[]>>('/custom-screeners');
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get a specific screener
 */
export function useCustomScreener(screenerId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: customScreenerKeys.detail(screenerId),
    queryFn: async () => {
      const response = await api.get<APIResponse<CustomScreener>>(
        `/custom-screeners/${screenerId}`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!screenerId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Create a new screener
 */
export function useCreateCustomScreener() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateScreenerRequest) => {
      const response = await api.post<APIResponse<CustomScreener>>(
        '/custom-screeners',
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: customScreenerKeys.lists() });
    },
  });
}

/**
 * Update a screener
 */
export function useUpdateCustomScreener() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      screenerId,
      data,
    }: {
      screenerId: string;
      data: UpdateScreenerRequest;
    }) => {
      const response = await api.patch<APIResponse<CustomScreener>>(
        `/custom-screeners/${screenerId}`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: customScreenerKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: customScreenerKeys.detail(variables.screenerId),
      });
    },
  });
}

/**
 * Delete a screener
 */
export function useDeleteCustomScreener() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (screenerId: string) => {
      await api.delete(`/custom-screeners/${screenerId}`);
      return screenerId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: customScreenerKeys.lists() });
    },
  });
}

/**
 * Duplicate a screener
 */
export function useDuplicateCustomScreener() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      screenerId,
      newName,
    }: {
      screenerId: string;
      newName?: string;
    }) => {
      const params = newName ? `?new_name=${encodeURIComponent(newName)}` : '';
      const response = await api.post<APIResponse<CustomScreener>>(
        `/custom-screeners/${screenerId}/duplicate${params}`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: customScreenerKeys.lists() });
    },
  });
}

// ============================================
// Run Screener Hooks
// ============================================

/**
 * Run a screener
 */
export function useRunCustomScreener() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (screenerId: string) => {
      const response = await api.post<APIResponse<ScreenerResult>>(
        `/custom-screeners/${screenerId}/run`
      );
      return response.data;
    },
    onSuccess: (_, screenerId) => {
      queryClient.invalidateQueries({
        queryKey: customScreenerKeys.results(screenerId),
      });
      queryClient.invalidateQueries({
        queryKey: customScreenerKeys.detail(screenerId),
      });
    },
  });
}

/**
 * Get cached results
 */
export function useScreenerResults(screenerId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: customScreenerKeys.results(screenerId),
    queryFn: async () => {
      const response = await api.get<APIResponse<ScreenerResult | null>>(
        `/custom-screeners/${screenerId}/results`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!screenerId,
    staleTime: 5 * 60 * 1000,
  });
}

// ============================================
// Presets & Metadata Hooks
// ============================================

/**
 * Get preset screener templates
 */
export function useScreenerPresets() {
  return useQuery({
    queryKey: customScreenerKeys.presets(),
    queryFn: async () => {
      const response = await api.get<APIResponse<PresetScreener[]>>(
        '/custom-screeners/meta/presets'
      );
      return response.data;
    },
    staleTime: Infinity, // Presets don't change
  });
}

/**
 * Create from preset
 */
export function useCreateFromPreset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (presetName: string) => {
      const response = await api.post<APIResponse<CustomScreener>>(
        `/custom-screeners/meta/presets/${encodeURIComponent(presetName)}/create`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: customScreenerKeys.lists() });
    },
  });
}

/**
 * Get available filter fields
 */
export function useFilterFields() {
  return useQuery({
    queryKey: customScreenerKeys.fields(),
    queryFn: async () => {
      const response = await api.get<APIResponse<FilterFieldMeta[]>>(
        '/custom-screeners/meta/fields'
      );
      return response.data;
    },
    staleTime: Infinity, // Fields don't change
  });
}

