/**
 * React Query hooks for API Key management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type {
  APIResponse,
  APIKeyInfo,
  APIKeyCreateRequest,
  APIKeyCreateResponse,
} from '../types';

// Query Keys
export const apiKeyKeys = {
  all: ['api-keys'] as const,
  list: () => [...apiKeyKeys.all, 'list'] as const,
};

/**
 * Get all API keys for current user
 */
export function useAPIKeys(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: apiKeyKeys.list(),
    queryFn: async () => {
      const response = await api.get<APIResponse<APIKeyInfo[]>>(
        '/auth/api-keys'
      );
      return response.data;
    },
    enabled: options?.enabled,
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Create a new API key
 */
export function useCreateAPIKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: APIKeyCreateRequest) => {
      const response = await api.post<APIResponse<APIKeyCreateResponse>>(
        '/auth/api-keys',
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: apiKeyKeys.list() });
    },
  });
}

/**
 * Revoke an API key
 */
export function useRevokeAPIKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (keyId: string) => {
      const response = await api.delete<APIResponse<{ message: string }>>(
        `/auth/api-keys/${keyId}`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: apiKeyKeys.list() });
    },
    // Optimistic update - remove from list immediately
    onMutate: async (keyId) => {
      await queryClient.cancelQueries({ queryKey: apiKeyKeys.list() });
      const previousKeys = queryClient.getQueryData<APIKeyInfo[]>(
        apiKeyKeys.list()
      );

      queryClient.setQueryData<APIKeyInfo[]>(apiKeyKeys.list(), (old) =>
        old?.filter((key) => key.key_id !== keyId)
      );

      return { previousKeys };
    },
    onError: (_, __, context) => {
      // Rollback on error
      if (context?.previousKeys) {
        queryClient.setQueryData(apiKeyKeys.list(), context.previousKeys);
      }
    },
  });
}

