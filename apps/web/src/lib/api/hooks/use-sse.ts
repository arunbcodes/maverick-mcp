/**
 * SSE (Server-Sent Events) hooks for real-time price updates
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { getAccessToken } from '../client';
import { stockKeys } from './use-stocks';
import { portfolioKeys } from './use-portfolio';
import type { PriceUpdate, StockQuote } from '../types';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseSSEOptions {
  enabled?: boolean;
  onMessage?: (data: PriceUpdate) => void;
  onError?: (error: Error) => void;
  onStatusChange?: (status: ConnectionStatus) => void;
  reconnectInterval?: number;
  maxRetries?: number;
}

/**
 * Subscribe to real-time price updates for specific tickers
 */
export function usePriceStream(
  tickers: string[],
  options: UseSSEOptions = {}
) {
  const {
    enabled = true,
    onMessage,
    onError,
    onStatusChange,
    reconnectInterval = 5000,
    maxRetries = 5,
  } = options;

  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef(0);
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [lastUpdate, setLastUpdate] = useState<PriceUpdate | null>(null);

  const updateStatus = useCallback(
    (newStatus: ConnectionStatus) => {
      setStatus(newStatus);
      onStatusChange?.(newStatus);
    },
    [onStatusChange]
  );

  const connect = useCallback(() => {
    if (!enabled || tickers.length === 0) return;

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    updateStatus('connecting');

    const token = getAccessToken();
    const tickerParam = tickers.join(',');
    const baseUrl = '/api/v1/sse/prices';
    const url = token
      ? `${baseUrl}?tickers=${tickerParam}&token=${token}`
      : `${baseUrl}?tickers=${tickerParam}`;

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      updateStatus('connected');
      retryCountRef.current = 0;
    };

    eventSource.onmessage = (event) => {
      try {
        const data: PriceUpdate = JSON.parse(event.data);
        setLastUpdate(data);
        onMessage?.(data);

        // Update React Query cache with new price
        queryClient.setQueryData<StockQuote>(
          stockKeys.quote(data.ticker),
          (old) => {
            if (!old) return old;
            return {
              ...old,
              price: data.price,
              change: data.change,
              change_percent: data.change_percent,
              volume: data.volume,
              timestamp: data.timestamp,
            };
          }
        );

        // Also invalidate portfolio to trigger recalculation
        queryClient.invalidateQueries({
          queryKey: portfolioKeys.summary(),
          refetchType: 'none', // Don't refetch, just mark as stale
        });
      } catch (err) {
        console.error('Failed to parse SSE message:', err);
      }
    };

    eventSource.onerror = (event) => {
      updateStatus('error');
      eventSource.close();

      const error = new Error('SSE connection error');
      onError?.(error);

      // Retry logic
      if (retryCountRef.current < maxRetries) {
        retryCountRef.current++;
        setTimeout(connect, reconnectInterval);
      } else {
        updateStatus('disconnected');
      }
    };

    // Handle specific events
    eventSource.addEventListener('price', (event) => {
      try {
        const data: PriceUpdate = JSON.parse(event.data);
        setLastUpdate(data);
        onMessage?.(data);
      } catch (err) {
        console.error('Failed to parse price event:', err);
      }
    });

    eventSource.addEventListener('heartbeat', () => {
      // Connection is alive, reset retry count
      retryCountRef.current = 0;
    });
  }, [
    enabled,
    tickers,
    queryClient,
    onMessage,
    onError,
    updateStatus,
    reconnectInterval,
    maxRetries,
  ]);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    updateStatus('disconnected');
  }, [updateStatus]);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Reconnect when tickers change
  useEffect(() => {
    if (eventSourceRef.current && status === 'connected') {
      disconnect();
      connect();
    }
  }, [tickers.join(',')]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    status,
    lastUpdate,
    reconnect: connect,
    disconnect,
    isConnected: status === 'connected',
    isConnecting: status === 'connecting',
    hasError: status === 'error',
  };
}

/**
 * Subscribe to portfolio value updates
 */
export function usePortfolioStream(options: Omit<UseSSEOptions, 'onMessage'> = {}) {
  const queryClient = useQueryClient();
  const [portfolioValue, setPortfolioValue] = useState<number | null>(null);

  return usePriceStream([], {
    ...options,
    onMessage: (update) => {
      // Portfolio updates come through a separate channel
      // This is a simplified version - real implementation would
      // aggregate position updates
      queryClient.invalidateQueries({ queryKey: portfolioKeys.summary() });
    },
  });
}

/**
 * Hook to manage SSE subscriptions across components
 */
export function useSSEManager() {
  const [subscribedTickers, setSubscribedTickers] = useState<Set<string>>(
    new Set()
  );

  const subscribe = useCallback((tickers: string | string[]) => {
    const tickerArray = Array.isArray(tickers) ? tickers : [tickers];
    setSubscribedTickers((prev) => {
      const next = new Set(prev);
      tickerArray.forEach((t) => next.add(t.toUpperCase()));
      return next;
    });
  }, []);

  const unsubscribe = useCallback((tickers: string | string[]) => {
    const tickerArray = Array.isArray(tickers) ? tickers : [tickers];
    setSubscribedTickers((prev) => {
      const next = new Set(prev);
      tickerArray.forEach((t) => next.delete(t.toUpperCase()));
      return next;
    });
  }, []);

  const clearAll = useCallback(() => {
    setSubscribedTickers(new Set());
  }, []);

  return {
    subscribedTickers: Array.from(subscribedTickers),
    subscribe,
    unsubscribe,
    clearAll,
    count: subscribedTickers.size,
  };
}

