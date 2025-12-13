/**
 * React Query hooks for Alert API endpoints
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchEventSource, EventStreamContentType } from '@microsoft/fetch-event-source';
import { api, getAccessToken } from '../client';
import type { APIResponse } from '../types';

// ============================================
// Types
// ============================================

export type AlertType =
  | 'new_maverick_stock'
  | 'new_bear_stock'
  | 'new_breakout'
  | 'rsi_oversold'
  | 'rsi_overbought'
  | 'price_breakout'
  | 'volume_spike'
  | 'position_gain'
  | 'position_loss'
  | 'stop_loss_hit'
  | 'price_target_hit';

export type AlertPriority = 'low' | 'medium' | 'high' | 'critical';

export type AlertStatus = 'unread' | 'read' | 'dismissed' | 'acted_on';

export interface AlertRule {
  rule_id: string;
  user_id: string;
  name: string;
  alert_type: AlertType;
  enabled: boolean;
  conditions: Record<string, unknown>;
  priority: AlertPriority;
  cooldown_minutes: number;
  created_at: string;
  updated_at: string | null;
}

export interface Alert {
  alert_id: string;
  user_id: string;
  rule_id: string | null;
  alert_type: AlertType;
  priority: AlertPriority;
  title: string;
  message: string;
  ticker: string | null;
  data: Record<string, unknown>;
  ai_insight: string | null;
  status: AlertStatus;
  created_at: string;
  read_at: string | null;
}

export interface PresetRule {
  name: string;
  alert_type: AlertType;
  conditions: Record<string, unknown>;
  description: string;
}

export interface CreateRuleRequest {
  name: string;
  alert_type: AlertType;
  conditions: Record<string, unknown>;
  priority?: AlertPriority;
  cooldown_minutes?: number;
}

export interface UpdateRuleRequest {
  name?: string;
  conditions?: Record<string, unknown>;
  priority?: AlertPriority;
  cooldown_minutes?: number;
  enabled?: boolean;
}

// ============================================
// Query Keys
// ============================================

export const alertKeys = {
  all: ['alerts'] as const,
  rules: () => [...alertKeys.all, 'rules'] as const,
  rule: (ruleId: string) => [...alertKeys.all, 'rules', ruleId] as const,
  history: (limit?: number, status?: AlertStatus) =>
    [...alertKeys.all, 'history', limit, status] as const,
  unreadCount: () => [...alertKeys.all, 'unread-count'] as const,
  presets: () => [...alertKeys.all, 'presets'] as const,
};

// ============================================
// Rule Hooks
// ============================================

/**
 * Get all alert rules for the current user
 */
export function useAlertRules() {
  return useQuery({
    queryKey: alertKeys.rules(),
    queryFn: async () => {
      const response = await api.get<APIResponse<AlertRule[]>>('/alerts/rules');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Create a new alert rule
 */
export function useCreateAlertRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateRuleRequest) => {
      const response = await api.post<APIResponse<AlertRule>>('/alerts/rules', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.rules() });
    },
  });
}

/**
 * Update an alert rule
 */
export function useUpdateAlertRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ ruleId, data }: { ruleId: string; data: UpdateRuleRequest }) => {
      const response = await api.patch<APIResponse<AlertRule>>(
        `/alerts/rules/${ruleId}`,
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.rules() });
    },
  });
}

/**
 * Delete an alert rule
 */
export function useDeleteAlertRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ruleId: string) => {
      await api.delete(`/alerts/rules/${ruleId}`);
      return ruleId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.rules() });
    },
  });
}

/**
 * Toggle an alert rule on/off
 */
export function useToggleAlertRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ ruleId, enabled }: { ruleId: string; enabled: boolean }) => {
      const response = await api.post<APIResponse<AlertRule>>(
        `/alerts/rules/${ruleId}/toggle?enabled=${enabled}`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.rules() });
    },
  });
}

// ============================================
// Alert History Hooks
// ============================================

/**
 * Get alert history
 */
export function useAlerts(options?: { limit?: number; status?: AlertStatus }) {
  const params = new URLSearchParams();
  if (options?.limit) params.set('limit', options.limit.toString());
  if (options?.status) params.set('status', options.status);
  const queryString = params.toString();

  // Only fetch if user is logged in
  const isLoggedIn = typeof window !== 'undefined' && !!getAccessToken();

  return useQuery({
    queryKey: alertKeys.history(options?.limit, options?.status),
    queryFn: async () => {
      const url = `/alerts${queryString ? `?${queryString}` : ''}`;
      const response = await api.get<APIResponse<Alert[]>>(url);
      return response.data;
    },
    enabled: isLoggedIn, // Only run when logged in
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: isLoggedIn ? 60 * 1000 : false, // Refetch every minute only if logged in
  });
}

/**
 * Get unread alert count
 */
export function useUnreadAlertCount() {
  // Only fetch if user is logged in
  const isLoggedIn = typeof window !== 'undefined' && !!getAccessToken();

  return useQuery({
    queryKey: alertKeys.unreadCount(),
    queryFn: async () => {
      const response = await api.get<APIResponse<{ unread_count: number }>>(
        '/alerts/unread-count'
      );
      return response.data.unread_count;
    },
    enabled: isLoggedIn, // Only run when logged in
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: isLoggedIn ? 30 * 1000 : false, // Refetch every 30 seconds only if logged in
  });
}

/**
 * Mark an alert as read
 */
export function useMarkAlertRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (alertId: string) => {
      await api.post(`/alerts/${alertId}/read`);
      return alertId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.history() });
      queryClient.invalidateQueries({ queryKey: alertKeys.unreadCount() });
    },
  });
}

/**
 * Mark all alerts as read
 */
export function useMarkAllAlertsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await api.post<APIResponse<{ marked_read: number }>>(
        '/alerts/read-all'
      );
      return response.data.marked_read;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.history() });
      queryClient.invalidateQueries({ queryKey: alertKeys.unreadCount() });
    },
  });
}

/**
 * Dismiss an alert
 */
export function useDismissAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (alertId: string) => {
      await api.post(`/alerts/${alertId}/dismiss`);
      return alertId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.history() });
      queryClient.invalidateQueries({ queryKey: alertKeys.unreadCount() });
    },
  });
}

// ============================================
// Preset Hooks
// ============================================

/**
 * Get preset alert rule templates
 */
export function useAlertPresets() {
  return useQuery({
    queryKey: alertKeys.presets(),
    queryFn: async () => {
      const response = await api.get<APIResponse<PresetRule[]>>('/alerts/presets');
      return response.data;
    },
    staleTime: Infinity, // Presets don't change
  });
}

/**
 * Enable a preset alert rule
 */
export function useEnablePreset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (presetName: string) => {
      const response = await api.post<APIResponse<AlertRule>>(
        `/alerts/presets/${encodeURIComponent(presetName)}/enable`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.rules() });
    },
  });
}

// ============================================
// SSE Hook
// ============================================

interface UseAlertStreamOptions {
  onAlert?: (alert: Alert) => void;
  enabled?: boolean;
}

// Custom error class for retryable errors
class RetriableError extends Error {}
class FatalError extends Error {}

/**
 * Subscribe to real-time alert stream via SSE
 *
 * Uses @microsoft/fetch-event-source to send Authorization header with JWT.
 * Features exponential backoff and max retry limit.
 *
 * IMPORTANT: This hook is disabled by default. Pass enabled: true to activate.
 */
export function useAlertStream(options?: UseAlertStreamOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastAlert, setLastAlert] = useState<Alert | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const retryCountRef = useRef(0);
  const isConnectingRef = useRef(false);
  const queryClient = useQueryClient();

  const MAX_RETRIES = 3; // Reduced from 5
  const BASE_DELAY = 10000; // 10 seconds (increased from 5)
  const MAX_DELAY = 120000; // 2 minutes

  // Check if user is logged in - do this at render time, not in callback
  const isLoggedIn = typeof window !== 'undefined' && !!getAccessToken();

  // Only enable if explicitly enabled AND user is logged in
  const shouldConnect = options?.enabled === true && isLoggedIn;

  const disconnect = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    isConnectingRef.current = false;
    setIsConnected(false);
    retryCountRef.current = 0;
  }, []);

  const connect = useCallback(async () => {
    // Don't connect if not enabled or not logged in
    if (!shouldConnect) {
      return;
    }

    // Prevent multiple concurrent connection attempts
    if (isConnectingRef.current) {
      return;
    }

    // Don't connect if we've exceeded max retries
    if (retryCountRef.current >= MAX_RETRIES) {
      console.warn('Alert stream: max retries exceeded, stopping');
      setError(new Error('Max retries exceeded'));
      return;
    }

    // Get fresh token
    const token = getAccessToken();
    if (!token) {
      return;
    }

    // Abort existing connection if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    isConnectingRef.current = true;

    // Create new abort controller
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Use relative URL to go through Next.js proxy
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || '';
    const url = `${baseUrl}/api/v1/alerts/stream`;

    try {
      await fetchEventSource(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': EventStreamContentType,
        },
        signal: abortController.signal,
        // Disable library's built-in retry to use our own
        openWhenHidden: false,

        async onopen(response) {
          isConnectingRef.current = false;
          if (response.ok && response.headers.get('content-type')?.includes(EventStreamContentType)) {
            setIsConnected(true);
            setError(null);
            retryCountRef.current = 0;
            return;
          } else if (response.status === 401 || response.status === 403) {
            // Auth error - don't retry, user needs to re-login
            throw new FatalError('Unauthorized');
          } else if (response.status >= 400 && response.status < 500) {
            // Client errors - don't retry
            throw new FatalError(`Client error: ${response.status}`);
          } else {
            // Server errors - could retry but be conservative
            throw new FatalError(`Server error: ${response.status}`);
          }
        },

        onmessage(msg) {
          if (msg.event === 'connected') {
            setIsConnected(true);
            retryCountRef.current = 0;
          } else if (msg.event === 'alert') {
            try {
              const alert: Alert = JSON.parse(msg.data);
              setLastAlert(alert);
              options?.onAlert?.(alert);
              queryClient.invalidateQueries({ queryKey: alertKeys.history() });
              queryClient.invalidateQueries({ queryKey: alertKeys.unreadCount() });
            } catch (e) {
              console.error('Failed to parse alert:', e);
            }
          }
          // Ignore ping events
        },

        onclose() {
          setIsConnected(false);
          isConnectingRef.current = false;
          // Don't auto-reconnect on close - let user manually reconnect if needed
        },

        onerror(err) {
          setIsConnected(false);
          isConnectingRef.current = false;

          // Always treat errors as fatal to prevent reconnection storms
          if (err instanceof FatalError) {
            setError(err);
          } else {
            setError(new Error('Connection failed'));
          }
          // Throw to stop the library's internal retry
          throw new FatalError('Stopping reconnection');
        },
      });
    } catch (e) {
      isConnectingRef.current = false;
      if (e instanceof FatalError) {
        setError(e);
      } else if (!(e instanceof DOMException && e.name === 'AbortError')) {
        setError(e instanceof Error ? e : new Error('Failed to connect'));
      }
    }
  }, [shouldConnect, options?.onAlert, queryClient]);

  const resetAndReconnect = useCallback(() => {
    retryCountRef.current = 0;
    setError(null);
    disconnect();
    // Small delay before reconnecting
    setTimeout(connect, 1000);
  }, [connect, disconnect]);

  useEffect(() => {
    if (shouldConnect) {
      connect();
    }
    return disconnect;
  }, [shouldConnect, connect, disconnect]);

  return {
    isConnected,
    lastAlert,
    error,
    reconnect: resetAndReconnect,
    disconnect,
  };
}

