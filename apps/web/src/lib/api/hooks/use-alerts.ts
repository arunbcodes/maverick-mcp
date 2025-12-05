/**
 * React Query hooks for Alert API endpoints
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../client';
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

  return useQuery({
    queryKey: alertKeys.history(options?.limit, options?.status),
    queryFn: async () => {
      const url = `/alerts${queryString ? `?${queryString}` : ''}`;
      const response = await api.get<APIResponse<Alert[]>>(url);
      return response.data;
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
}

/**
 * Get unread alert count
 */
export function useUnreadAlertCount() {
  return useQuery({
    queryKey: alertKeys.unreadCount(),
    queryFn: async () => {
      const response = await api.get<APIResponse<{ unread_count: number }>>(
        '/alerts/unread-count'
      );
      return response.data.unread_count;
    },
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
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

/**
 * Subscribe to real-time alert stream via SSE
 */
export function useAlertStream(options?: UseAlertStreamOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastAlert, setLastAlert] = useState<Alert | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const queryClient = useQueryClient();

  const connect = useCallback(() => {
    if (options?.enabled === false) return;

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const url = `${baseUrl}/api/v1/alerts/stream`;

    try {
      const eventSource = new EventSource(url, { withCredentials: true });
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        setError(null);
      };

      eventSource.addEventListener('connected', () => {
        setIsConnected(true);
      });

      eventSource.addEventListener('alert', (event) => {
        try {
          const alert: Alert = JSON.parse(event.data);
          setLastAlert(alert);

          // Callback
          options?.onAlert?.(alert);

          // Invalidate queries to update UI
          queryClient.invalidateQueries({ queryKey: alertKeys.history() });
          queryClient.invalidateQueries({ queryKey: alertKeys.unreadCount() });
        } catch (e) {
          console.error('Failed to parse alert:', e);
        }
      });

      eventSource.addEventListener('ping', () => {
        // Keepalive received
      });

      eventSource.onerror = (e) => {
        setIsConnected(false);
        setError(new Error('Connection lost'));

        // Reconnect after delay
        eventSource.close();
        setTimeout(connect, 5000);
      };
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Failed to connect'));
    }
  }, [options?.enabled, options?.onAlert, queryClient]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return {
    isConnected,
    lastAlert,
    error,
    reconnect: connect,
    disconnect,
  };
}

